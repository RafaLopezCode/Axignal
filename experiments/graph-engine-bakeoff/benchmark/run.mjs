#!/usr/bin/env node
/**
 * AXIGLAND graph-engine bakeoff runner.
 *
 *   node benchmark/run.mjs --mode=perf [--heavy] [--scales=tiny,small] [--engines=sigma]
 *   node benchmark/run.mjs --mode=scenarios [--engines=...]
 *   node benchmark/run.mjs --mode=screenshots [--engines=...]
 *
 * Writes results/*.json and screenshots/*.jpg. Deterministic fixtures only.
 */

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { cpus, release, totalmem } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { gpuInfo, launchBrowser, runScenario, startServer, stopServer } from "./lib.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..");
const RESULTS = join(ROOT, "results");
const SHOTS = join(ROOT, "screenshots");

const args = Object.fromEntries(
  process.argv
    .slice(2)
    .filter((a) => a.startsWith("--"))
    .map((a) => {
      const [k, v] = a.replace(/^--/, "").split("=");
      return [k, v ?? true];
    }),
);

const MODE = args.mode || "perf";
const HEAVY = Boolean(args.heavy);
const ENGINES = (args.engines || "cytoscape,sigma,g6").split(",");

function save(name, data) {
  mkdirSync(RESULTS, { recursive: true });
  writeFileSync(join(RESULTS, name), JSON.stringify(data, null, 2));
}

/** Merge incoming results into an existing file keyed by engine|fixture. */
function mergeSave(name, incoming) {
  mkdirSync(RESULTS, { recursive: true });
  const path = join(RESULTS, name);
  let existing = [];
  try {
    existing = JSON.parse(readFileSync(path, "utf8"));
  } catch {
    existing = [];
  }
  const key = (r) => `${r.engine}|${r.fixture}`;
  const map = new Map(existing.map((r) => [key(r), r]));
  for (const r of incoming) map.set(key(r), r);
  writeFileSync(path, JSON.stringify([...map.values()], null, 2));
}

function shotName(engine, name) {
  return `${engine}_${name}`;
}

function saveScreenshot(page, name) {
  mkdirSync(SHOTS, { recursive: true });
  return page.screenshot({ path: join(SHOTS, `${name}.jpg`), type: "jpeg", quality: 72 });
}

async function environment(browser) {
  return {
    os: `${process.platform} ${process.arch} (${release()})`,
    cpu: cpus()[0]?.model,
    ramGb: Math.round(totalmem() / 1024 ** 3),
    node: process.version,
    browserVersion: browser.version(),
    gpu: await gpuInfo(browser),
    viewport: { width: 1440, height: 900, deviceScaleFactor: 1 },
  };
}

async function perfSteps(scale) {
  return async (page) => {
    const idle = await page.evaluate(() => window.AXIGBench.idleFrames(60));
    const panzoom = await page.evaluate(() => window.AXIGBench.panZoomFrames(90));
    const heap = await page.evaluate(
      () => window.AXIGBench.metrics().events.filter((e) => e.name === "js_heap_mb").pop()?.value ?? null,
    );
    return { scale, idleFrames: idle, panZoomFrames: panzoom, heapMb: heap };
  };
}

async function scenarioSteps(scenario, engine) {
  return async (page) => {
    switch (scenario) {
      case "first_map": {
        await page.evaluate(() => window.AXIGBench.idleFrames(60));
        await saveScreenshot(page, shotName(engine, "first_map"));
        return await page.evaluate(() => window.AXIGBench.results);
      }
      case "progressive": {
        const out = {};
        for (const n of [100, 500, 5000, 20000]) {
          out[`+${n}`] = await page.evaluate((k) => window.AXIGBench.expand(k), n);
        }
        await saveScreenshot(page, shotName(engine, "progressive_expanded"));
        return out;
      }
      case "recenter":
        return await page.evaluate((nodeId) => window.AXIGBench.recenter(nodeId), "n5");
      case "epistemic": {
        const observedOnly = await page.evaluate(async () => {
          await window.AXIGBench.epistemic(["OBSERVED"]);
          return window.AXIGBench.metrics().events.filter((e) => e.name === "epistemic_ms").pop()?.value;
        });
        await saveScreenshot(page, shotName(engine, "epistemic_observed_only"));
        const all = await page.evaluate(async () => {
          await window.AXIGBench.epistemic(["OBSERVED", "POTENTIAL", "HISTORICAL"]);
          return window.AXIGBench.metrics().events.filter((e) => e.name === "epistemic_ms").pop()?.value;
        });
        return { observedOnlyMs: observedOnly, allMs: all };
      }
      case "pathx": {
        const out = await page.evaluate(() => window.AXIGBench.pathx());
        await saveScreenshot(page, shotName(engine, "pathx"));
        const clear = await page.evaluate(async () => {
          const t = performance.now();
          await window.AXIGBench.clearPath();
          return performance.now() - t;
        });
        return { ...out, clearMs: clear };
      }
      case "filter": {
        const filterMs = await page.evaluate(async () => {
          const t = performance.now();
          await window.AXIGBench.filterByNatures(["SUPPLIES", "DISTRIBUTES"]);
          return performance.now() - t;
        });
        await saveScreenshot(page, shotName(engine, "filter_supply"));
        await page.evaluate(() => window.AXIGBench.filterByNatures(null));
        return { filterMs };
      }
      case "temporal": {
        await page.evaluate(() => window.AXIGBench.setTime(Date.parse("2024-06-01T00:00:00Z")));
        await saveScreenshot(page, shotName(engine, "temporal_t1"));
        const t2 = await page.evaluate(async () => {
          const t = performance.now();
          await window.AXIGBench.setTime(Date.parse("2025-06-01T00:00:00Z"));
          return performance.now() - t;
        });
        await saveScreenshot(page, shotName(engine, "temporal_t2"));
        return { t2TransitionMs: t2 };
      }
      case "continuous":
        return {
          framesDuringDiscovery: await page.evaluate(async () => {
            return window.AXIGBench.sampleWhile(async () => {
              for (let i = 0; i < 10; i += 1) await window.AXIGBench.expand(50);
            }, 150);
          }),
        };
      case "hairball":
        await page.evaluate(() => window.AXIGBench.idleFrames(30));
        await saveScreenshot(page, shotName(engine, "hairball"));
        return await page.evaluate(() => window.AXIGBench.idleFrames(60));
      case "corporate":
        await page.evaluate(() => window.AXIGBench.idleFrames(30));
        await saveScreenshot(page, shotName(engine, "corporate_structure"));
        return await page.evaluate(() => window.AXIGBench.results);
      default:
        return null;
    }
  };
}

const SCENARIOS = [
  { scenario: "first_map", fixture: "medium.clustered.json", base: 0.05 },
  { scenario: "progressive", fixture: "medium.clustered.json", base: 0.05 },
  { scenario: "recenter", fixture: "medium.clustered.json", base: 0.3 },
  { scenario: "epistemic", fixture: "medium.clustered.json", base: 0.5 },
  { scenario: "pathx", fixture: "medium.clustered.json", base: 0.5 },
  { scenario: "filter", fixture: "medium.clustered.json", base: 0.5 },
  { scenario: "temporal", fixture: "medium.temporal.json", base: 0.5 },
  { scenario: "continuous", fixture: "medium.clustered.json", base: 0.05 },
  { scenario: "hairball", fixture: "medium.hairball.json", base: 1 },
  { scenario: "corporate", fixture: "medium.corporate.json", base: 0.5 },
];

const SHOT_SPECS = [
  { scenario: "first_map", fixture: "small.clustered.json", base: 0.4 },
  { scenario: "hairball", fixture: "small.hairball.json", base: 1 },
  { scenario: "corporate", fixture: "small.corporate.json", base: 0.6 },
  { scenario: "pathx", fixture: "small.clustered.json", base: 0.6 },
  { scenario: "epistemic", fixture: "small.clustered.json", base: 0.6 },
];

async function main() {
  const server = await startServer();
  const browser = await launchBrowser();
  try {
    const env = await environment(browser);
    save("environment.json", env);
    process.stdout.write(`ENV ${JSON.stringify(env.gpu)}\n`);

    if (MODE === "perf") {
      const scales =
        (args.scales && String(args.scales).split(",")) ||
        (HEAVY ? ["tiny", "small", "medium", "large", "stress"] : ["tiny", "small", "medium"]);
      const all = [];
      for (const engine of ENGINES) {
        for (const scale of scales) {
          const result = await runScenario(browser, {
            engine,
            fixture: `${scale}.clustered.json`,
            base: 0.5,
            steps: await perfSteps(scale),
          });
          process.stdout.write(
            `perf ${engine} ${scale}: ok=${result.ok} idleP95=${result.idleFrames?.p95} pzP95=${result.panZoomFrames?.p95}\n`,
          );
          all.push(result);
        }
      }
      mergeSave("perf.json", all);
    } else if (MODE === "scenarios") {
      const all = [];
      for (const engine of ENGINES) {
        for (const spec of SCENARIOS) {
          const result = await runScenario(browser, {
            engine,
            fixture: spec.fixture,
            base: spec.base,
            steps: await scenarioSteps(spec.scenario, engine),
          });
          process.stdout.write(`scenario ${engine} ${spec.scenario}: ok=${result.ok} errors=${result.errors.length}\n`);
          all.push({ ...spec, ...result });
        }
      }
      mergeSave("scenarios.json", all);
    } else if (MODE === "screenshots") {
      for (const engine of ENGINES) {
        for (const spec of SHOT_SPECS) {
          const result = await runScenario(browser, {
            engine,
            fixture: spec.fixture,
            base: spec.base,
            steps: async (page) => {
              await page.evaluate(() => window.AXIGBench.idleFrames(30));
              if (spec.scenario === "pathx") await page.evaluate(() => window.AXIGBench.pathx());
              if (spec.scenario === "epistemic") await page.evaluate(() => window.AXIGBench.epistemic(["OBSERVED"]));
              await saveScreenshot(page, shotName(engine, spec.scenario));
              return {};
            },
          });
          process.stdout.write(`shot ${engine} ${spec.scenario}: ok=${result.ok}\n`);
        }
      }
    }
  } finally {
    await browser.close();
    await stopServer(server);
  }
}

await main();
