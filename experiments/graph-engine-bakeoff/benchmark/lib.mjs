/** Shared benchmark helpers: manages the Vite server and Playwright Chrome. */

import { setTimeout as delay } from "node:timers/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";
import { createServer } from "vite";

export const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
export const PORT = 5199;
export const BASE_URL = `http://127.0.0.1:${PORT}`;

export async function startServer() {
  const server = await createServer({
    root: ROOT,
    configFile: join(ROOT, "vite.config.mjs"),
    server: { port: PORT, strictPort: true, host: "127.0.0.1" },
    logLevel: "silent",
  });
  await server.listen();
  const deadline = Date.now() + 30000;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(BASE_URL);
      if (res.ok) return server;
    } catch {
      /* not ready */
    }
    await delay(300);
  }
  await server.close();
  throw new Error("vite server did not start");
}

export async function stopServer(server) {
  try {
    await server?.close();
  } catch {
    /* ignore */
  }
}

export async function launchBrowser() {
  const browser = await chromium.launch({
    channel: "chrome",
    headless: true,
    args: [
      "--use-angle=d3d11",
      "--enable-gpu",
      "--ignore-gpu-blocklist",
      "--enable-unsafe-webgpu",
      "--disable-dev-shm-usage",
    ],
  });
  return browser;
}

export async function gpuInfo(browser) {
  const page = await browser.newPage();
  await page.goto("about:blank");
  const info = await page.evaluate(() => {
    const canvas = document.createElement("canvas");
    const gl = canvas.getContext("webgl2") || canvas.getContext("webgl");
    if (!gl) return { webgl: false };
    const ext = gl.getExtension("WEBGL_debug_renderer_info");
    return {
      webgl: true,
      vendor: ext ? gl.getParameter(ext.UNMASKED_VENDOR_WEBGL) : gl.getParameter(gl.VENDOR),
      renderer: ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER),
      version: gl.getParameter(gl.VERSION),
    };
  });
  await page.close();
  return info;
}

export async function runScenario(browser, { engine, fixture, base = 0.3, steps }) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const consoleErrors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  page.on("pageerror", (err) => consoleErrors.push(String(err)));

  const url = `${BASE_URL}/?engine=${engine}&fixture=${fixture}&base=${base}`;
  const t0 = Date.now();
  await page.goto(url, { waitUntil: "domcontentloaded" });
  try {
    await page.waitForFunction(() => window.AXIGBench && (window.AXIGBench.ok === true || window.AXIGBench.ok === false), {
      timeout: 60000,
    });
  } catch {
    consoleErrors.push("AXIGBench never became ready");
  }
  const wallLoadMs = Date.now() - t0;
  const ok = await page.evaluate(() => window.AXIGBench?.ok ?? false);
  let result = { engine, fixture, ok, wallLoadMs, errors: [] };
  if (ok) {
    result = { ...result, ...(await steps(page)) };
  }
  result.errors = await page.evaluate(() => window.AXIGBench?.errors ?? []);
  result.consoleErrors = consoleErrors;
  result.metrics = await page.evaluate(() => (window.AXIGBench ? window.AXIGBench.metrics() : null));
  await page.close();
  return result;
}

export function writeJson(path, data) {
  // eslint-disable-next-line no-undef
  return import("node:fs").then(({ mkdirSync, writeFileSync }) => {
    mkdirSync(dirname(path), { recursive: true });
    // eslint-disable-next-line no-undef
    writeFileSync(path, JSON.stringify(data, null, 2));
  });
}
