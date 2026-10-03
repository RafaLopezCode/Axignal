#!/usr/bin/env node
import { spawn } from "node:child_process";
import { mkdtemp, readFile, writeFile, rm, copyFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const repo = path.resolve(import.meta.dirname, "../..");
const logoPath = path.join(repo, "apps/web/subscriber/assets/brand/logo-light.svg");
const outDir = path.join(repo, "apps/web/subscriber/assets/brand");
const chrome = process.env.CHROME_PATH ?? "C:/Program Files/Google/Chrome/Application/chrome.exe";
const logoData = (await readFile(logoPath)).toString("base64");
const temp = await mkdtemp(path.join(tmpdir(), "axignal-social-"));

function html(width, height) {
  const logoWidth = width === height ? Math.round(width * 0.68) : Math.round(width * 0.62);
  return `<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box}html,body{margin:0;width:${width}px;height:${height}px;overflow:hidden}
body{display:flex;align-items:center;justify-content:center;background:#f7f5ef;color:#3c3c3c}
.card{width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:${Math.round(height*0.08)}px;padding:${Math.round(height*0.09)}px}
img{width:${logoWidth}px;height:auto;display:block}
p{margin:0;font:500 ${Math.round(height*0.038)}px/1.2 Arial,sans-serif;letter-spacing:.08em;color:#3c3c3c}
</style></head><body><main class="card"><img alt="Axignal" src="data:image/svg+xml;base64,${logoData}"><p>OBSERVE · CONNECT · UNDERSTAND · EXPLAIN</p></main></body></html>`;
}

async function shot(name, width, height) {
  const htmlPath = path.join(temp, `${name}.html`);
  const outPath = path.join(outDir, `${name}.png`);
  await writeFile(htmlPath, html(width, height), "utf8");
  await new Promise((resolve, reject) => {
    const p = spawn(chrome, [
      "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
      "--force-device-scale-factor=1", `--window-size=${width},${height}`,
      `--screenshot=${outPath}`, pathToFileURL(htmlPath).href
    ], { stdio: "ignore", windowsHide: true });
    p.on("exit", code => code === 0 ? resolve() : reject(new Error(`Chrome exit ${code}`)));
    p.on("error", reject);
  });
  return outPath;
}

try {
  const og = await shot("og-image-1200x630", 1200, 630);
  await copyFile(og, path.join(outDir, "twitter-image-1200x630.png"));
  await shot("social-square-1200", 1200, 1200);
  console.log("SOCIAL_ASSETS=3");
} finally {
  await rm(temp, { recursive: true, force: true });
}
