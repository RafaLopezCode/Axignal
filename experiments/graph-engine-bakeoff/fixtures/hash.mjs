#!/usr/bin/env node
/** Compute SHA-256 + counts for every generated fixture, writing manifest.json. */

import { createHash } from "node:crypto";
import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const DATA = join(HERE, "data");

const files = readdirSync(DATA).filter((f) => f.endsWith(".json") && f !== "manifest.json");
const manifest = [];
for (const file of files.sort()) {
  const raw = readFileSync(join(DATA, file));
  const hash = createHash("sha256").update(raw).digest("hex");
  let meta = {};
  try {
    meta = JSON.parse(raw.toString("utf8")).meta || {};
  } catch {
    meta = {};
  }
  manifest.push({ file, hash, nodeCount: meta.nodeCount, edgeCount: meta.edgeCount, topology: meta.topology, scale: meta.scale, bytes: raw.length });
}
writeFileSync(join(DATA, "manifest.json"), JSON.stringify(manifest, null, 2));
process.stdout.write(`${manifest.length} fixtures hashed\n`);
