#!/usr/bin/env node
/**
 * Deterministic AXIGLAND benchmark fixture generator.
 *
 * Same seed -> byte-identical fixtures for every engine. Uses a seeded PRNG
 * (mulberry32); no unseeded randomness. Positions are precomputed so rendering
 * throughput can be compared independently of layout.
 *
 * Usage:
 *   node fixtures/generate.mjs                 # tiny/small/medium, clustered
 *   node fixtures/generate.mjs --topology all  # tiny/small/medium x all topologies
 *   node fixtures/generate.mjs --heavy         # also large + stress
 *   node fixtures/generate.mjs --only small --topology hairball
 */

import { createHash } from "node:crypto";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  Currentness,
  EpistemicClass,
  NodeKind,
  RelationshipNature,
  SCALES,
  Topology,
} from "../model/model.mjs";

export const SEED = 20260924;
const HERE = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = join(HERE, "data");

const NATURES = Object.values(RelationshipNature);
const KINDS = [
  NodeKind.ORGANIZATION,
  NodeKind.ORGANIZATION,
  NodeKind.ORGANIZATION,
  NodeKind.MARKET,
  NodeKind.CAPABILITY,
  NodeKind.PRODUCT,
];
const EPISTEMIC_MIX = [
  EpistemicClass.OBSERVED,
  EpistemicClass.OBSERVED,
  EpistemicClass.OBSERVED,
  EpistemicClass.OBSERVED,
  EpistemicClass.OBSERVED,
  EpistemicClass.OBSERVED,
  EpistemicClass.OBSERVED,
  EpistemicClass.POTENTIAL,
  EpistemicClass.POTENTIAL,
  EpistemicClass.HISTORICAL,
];

function mulberry32(seed) {
  let a = seed >>> 0;
  return function next() {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function currentnessFor(epistemicClass, rnd) {
  if (epistemicClass === EpistemicClass.HISTORICAL) return Currentness.HISTORICAL;
  if (epistemicClass === EpistemicClass.POTENTIAL) {
    return rnd() < 0.5 ? Currentness.UNKNOWN_CURRENTNESS : Currentness.STALE;
  }
  const r = rnd();
  if (r < 0.75) return Currentness.CURRENTLY_OBSERVED;
  if (r < 0.9) return Currentness.STALE;
  return Currentness.HISTORICAL;
}

const DAY = 86400_000;
const EPOCH = Date.parse("2024-01-01T00:00:00Z");

function buildNodes(count, rnd) {
  const clusterCount = Math.max(1, Math.round(Math.sqrt(count / 8)));
  const nodes = new Array(count);
  for (let i = 0; i < count; i += 1) {
    const cluster = i % clusterCount;
    const cx = (cluster % 8) * 1000;
    const cy = Math.floor(cluster / 8) * 1000;
    const kind = KINDS[Math.floor(rnd() * KINDS.length)];
    nodes[i] = {
      id: `n${i}`,
      kind,
      label: `${kind.slice(0, 3)}-${i}`,
      relevance: Math.round(rnd() * 1000) / 1000,
      evidenceCertainty: Math.round(rnd() * 1000) / 1000,
      temporalActivity: Math.round(rnd() * 1000) / 1000,
      cluster,
      x: Math.round(cx + (rnd() - 0.5) * 900),
      y: Math.round(cy + (rnd() - 0.5) * 900),
    };
  }
  return { nodes, clusterCount };
}

function pickPair(topology, clusterCount, nodeCount, rnd) {
  const i0 = Math.floor(rnd() * nodeCount);
  let i = i0;
  let j;
  switch (topology) {
    case Topology.NEIGHBOURHOOD: {
      // dense around node 0, then local hops
      if (rnd() < 0.6) return [0, 1 + Math.floor(rnd() * Math.min(nodeCount - 1, 40))];
      j = Math.floor(rnd() * nodeCount);
      break;
    }
    case Topology.SUPPLY: {
      // directional layered chains
      const layer = Math.min(4, Math.floor(rnd() * 5));
      i = Math.floor((layer / 5) * nodeCount) + Math.floor(rnd() * (nodeCount / 5));
      j = Math.floor(((layer + 1) / 5) * nodeCount) + Math.floor(rnd() * (nodeCount / 5));
      return [i, Math.min(j, nodeCount - 1)];
    }
    case Topology.CORPORATE: {
      // hierarchy: later nodes point to earlier parents, occasional cross links
      if (rnd() < 0.75) {
        const child = 1 + Math.floor(rnd() * (nodeCount - 1));
        const parent = Math.floor(rnd() * child);
        return [child, parent];
      }
      j = Math.floor(rnd() * nodeCount);
      break;
    }
    case Topology.HAIRBALL: {
      j = Math.floor(rnd() * nodeCount);
      break;
    }
    case Topology.CLUSTERED:
    case Topology.TEMPORAL:
    default: {
      const c = Math.floor(rnd() * clusterCount);
      if (rnd() < 0.85 && clusterCount > 1) {
        i = c + Math.floor(rnd() * (nodeCount / clusterCount)) * clusterCount;
        j = c + Math.floor(rnd() * (nodeCount / clusterCount)) * clusterCount;
      } else {
        j = Math.floor(rnd() * nodeCount);
      }
      break;
    }
  }
  return [Math.min(i, nodeCount - 1), Math.min(j ?? 0, nodeCount - 1)];
}

export function generate(scaleName, topology) {
  const scale = SCALES[scaleName];
  if (!scale) throw new Error(`unknown scale: ${scaleName}`);
  const rnd = mulberry32(SEED + scale.nodes * 7 + topology.length * 13);
  const nodeCount = scale.nodes;
  const edgeCount = scale.edges;
  const { nodes, clusterCount } = buildNodes(nodeCount, rnd);

  const edges = [];
  const seen = new Set();
  let attempts = 0;
  const maxAttempts = edgeCount * 12;
  while (edges.length < edgeCount && attempts < maxAttempts) {
    attempts += 1;
    const [a, b] = pickPair(topology, clusterCount, nodeCount, rnd);
    if (a === b) continue;
    const nature = NATURES[Math.floor(rnd() * NATURES.length)];
    const key = `${a}|${b}|${nature}`;
    if (seen.has(key)) continue;
    seen.add(key);

    const epistemicClass = EPISTEMIC_MIX[Math.floor(rnd() * EPISTEMIC_MIX.length)];
    const currentness = currentnessFor(epistemicClass, rnd);
    const firstObserved = EPOCH + Math.floor(rnd() * 540) * DAY;
    const lastObserved = firstObserved + Math.floor(rnd() * 180) * DAY;
    const lastVerified = lastObserved + Math.floor(rnd() * 60) * DAY;
    const validFrom = firstObserved;
    const validUntil = epistemicClass === EpistemicClass.HISTORICAL ? lastObserved : null;
    edges.push({
      id: `e${edges.length}`,
      source: nodes[a].id,
      target: nodes[b].id,
      nature,
      epistemicClass,
      currentness,
      materiality: Math.round(rnd() * 1000) / 1000,
      evidenceStrength: Math.round(rnd() * 1000) / 1000,
      direction: ["SUBSIDIARY_OF", "PARENT_OF", "OWNS", "BRAND_OF", "DIVISION_OF"].includes(nature)
        ? "STRUCTURAL"
        : "ECONOMIC",
      valid_from: validFrom,
      valid_until: validUntil,
      first_observed_at: firstObserved,
      last_observed_at: lastObserved,
      last_verified_at: lastVerified,
      // Temporal mutation: T1 vs T2 populations (Scenario 8).
      drawn: rnd(),
    });
  }

  return {
    meta: {
      seed: SEED,
      scale: scaleName,
      topology,
      nodeCount: nodes.length,
      edgeCount: edges.length,
      generatedFrom: "fixtures/generate.mjs",
    },
    nodes,
    edges,
  };
}

export function fixtureFileName(scaleName, topology) {
  return `${scaleName}.${topology}.json`;
}

export function writeFixture(scaleName, topology) {
  const data = generate(scaleName, topology);
  mkdirSync(OUT_DIR, { recursive: true });
  const file = join(OUT_DIR, fixtureFileName(scaleName, topology));
  writeFileSync(file, JSON.stringify(data));
  const hash = createHash("sha256").update(JSON.stringify(data)).digest("hex");
  return { file, hash, nodeCount: data.meta.nodeCount, edgeCount: data.meta.edgeCount };
}

function parseArgs(argv) {
  const args = { only: null, topology: Topology.CLUSTERED, allTopologies: false, heavy: false };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === "--only") args.only = argv[++i];
    else if (a === "--topology") {
      const v = argv[++i];
      if (v === "all") args.allTopologies = true;
      else args.topology = v;
    } else if (a === "--heavy") args.heavy = true;
  }
  return args;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const scales = args.only
    ? [args.only]
    : args.heavy
      ? ["tiny", "small", "medium", "large", "stress"]
      : ["tiny", "small", "medium"];
  const topologies = args.allTopologies ? Object.values(Topology) : [args.topology];
  const manifest = [];
  for (const scale of scales) {
    for (const topology of topologies) {
      const started = Date.now();
      const result = writeFixture(scale, topology);
      manifest.push({ scale, topology, ...result, ms: Date.now() - started });
      process.stdout.write(
        `${scale}/${topology}: ${result.nodeCount}n ${result.edgeCount}e ${result.hash.slice(0, 12)} (${Date.now() - started}ms)\n`,
      );
    }
  }
  writeFileSync(join(OUT_DIR, "manifest.json"), JSON.stringify(manifest, null, 2));
}

import { realpathSync } from "node:fs";

const invokedPath = process.argv[1] ? realpathSync(process.argv[1]) : "";
if (invokedPath === fileURLToPath(import.meta.url)) {
  await main();
}
