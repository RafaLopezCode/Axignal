#!/usr/bin/env node
/** Smoke test: verify each adapter loads a tiny fixture without errors. */

import { launchBrowser, runScenario, startServer, stopServer } from "./lib.mjs";

const engines = (process.argv[2] || "cytoscape,sigma,g6,cosmos").split(",");
const server = await startServer();
const browser = await launchBrowser();
try {
  for (const engine of engines) {
    const result = await runScenario(browser, {
      engine,
      fixture: "tiny.clustered.json",
      steps: async (page) => ({
        baseNodes: await page.evaluate(() => window.AXIGBench.results.base_nodes ?? null),
        idle: await page.evaluate(() => window.AXIGBench.idleFrames(30)),
      }),
    });
    process.stdout.write(
      `${engine}: ok=${result.ok} wall=${result.wallLoadMs}ms errors=${JSON.stringify(result.errors).slice(0, 200)}\n`,
    );
    if (result.consoleErrors.length) {
      process.stdout.write(`   console: ${result.consoleErrors.slice(0, 3).join(" | ").slice(0, 300)}\n`);
    }
  }
} finally {
  await browser.close();
  await stopServer(server);
}
