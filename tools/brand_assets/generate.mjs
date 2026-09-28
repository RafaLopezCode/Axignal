#!/usr/bin/env node

import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const args = new Map();
for (let index = 2; index < process.argv.length; index += 2) {
  const key = process.argv[index];
  const value = process.argv[index + 1];
  if (!key?.startsWith("--") || !value) {
    throw new Error("Usage: node tools/brand_assets/generate.mjs [--source DIR] [--output DIR] [--chrome FILE]");
  }
  args.set(key.slice(2), value);
}

const repositoryRoot = path.resolve(import.meta.dirname, "../..");
const sourceDirectory = path.resolve(args.get("source") ?? "D:/AXIGNAL/LOGOS");
const outputDirectory = path.resolve(
  repositoryRoot,
  args.get("output") ?? "apps/web/subscriber/assets/brand",
);
const chromePath = path.resolve(
  args.get("chrome") ??
    process.env.CHROME_PATH ??
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
);

const svgAssets = [
  {
    source: "logo_horizontal_light_fraunces.svg",
    output: "logo-light.svg",
    role: "logo",
    variant: "light-background",
    composition: "horizontal",
  },
  {
    source: "logo_horizontal_dark_fraunces.svg",
    output: "logo-dark.svg",
    role: "logo",
    variant: "dark-background",
    composition: "horizontal",
  },
  {
    source: "axignal_isotipo.svg",
    output: "isotope.svg",
    role: "isotope",
    variant: "shared-light-and-dark",
    composition: "square",
  },
  {
    source: "favicon.svg",
    output: "favicon.svg",
    role: "favicon",
    variant: "vector",
    composition: "square-with-brand-safe-padding",
  },
];
const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");
const normalizedSvg = (bytes) =>
  Buffer.from(
    bytes.toString("utf8").replace(/\r\n?/g, "\n").replace(/[\t ]+$/gm, ""),
    "utf8",
  );

async function sendCdp(socket, method, params = {}) {
  const id = sendCdp.nextId++;
  const response = new Promise((resolve, reject) => {
    sendCdp.pending.set(id, { resolve, reject });
  });
  socket.send(JSON.stringify({ id, method, params }));
  return response;
}
sendCdp.nextId = 1;
sendCdp.pending = new Map();

function makeIco(png) {
  const header = Buffer.alloc(22);
  header.writeUInt16LE(0, 0);
  header.writeUInt16LE(1, 2);
  header.writeUInt16LE(1, 4);
  header.writeUInt8(32, 6);
  header.writeUInt8(32, 7);
  header.writeUInt8(0, 8);
  header.writeUInt8(0, 9);
  header.writeUInt16LE(1, 10);
  header.writeUInt16LE(32, 12);
  header.writeUInt32LE(png.length, 14);
  header.writeUInt32LE(header.length, 18);
  return Buffer.concat([header, png]);
}

async function rasterizeFavicon(sourceBytes) {
  const profile = await mkdtemp(path.join(tmpdir(), "axignal-brand-chrome-"));
  const chrome = spawn(
    chromePath,
    [
      "--headless=new",
      "--disable-gpu",
      "--disable-background-networking",
      "--disable-extensions",
      "--no-first-run",
      "--no-default-browser-check",
      "--remote-debugging-port=0",
      `--user-data-dir=${profile}`,
      "about:blank",
    ],
    { stdio: "ignore", windowsHide: true },
  );

  try {
    const activePortPath = path.join(profile, "DevToolsActivePort");
    let activePort;
    for (let attempt = 0; attempt < 100; attempt += 1) {
      try {
        [activePort] = (await readFile(activePortPath, "utf8")).split(/\r?\n/);
        if (activePort) break;
      } catch {
        // Chrome has not opened its local DevTools endpoint yet.
      }
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
    if (!activePort) throw new Error("Chrome DevTools did not start.");

    const targets = await fetch(`http://127.0.0.1:${activePort}/json/list`).then(
      (response) => response.json(),
    );
    const pageTarget = targets.find((target) => target.type === "page");
    if (!pageTarget?.webSocketDebuggerUrl) throw new Error("Chrome page target is unavailable.");

    const socket = new WebSocket(pageTarget.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      socket.addEventListener("open", resolve, { once: true });
      socket.addEventListener("error", reject, { once: true });
    });
    socket.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      if (message.id === undefined) return;
      const pending = sendCdp.pending.get(message.id);
      if (!pending) return;
      sendCdp.pending.delete(message.id);
      if (message.error) pending.reject(new Error(message.error.message));
      else pending.resolve(message.result);
    });

    const faviconData = `data:image/svg+xml;base64,${sourceBytes.toString("base64")}`;
    const expression = [
      "(async () => {",
      "  const image = new Image();",
      `  image.src = ${JSON.stringify(faviconData)};`,
      "  await image.decode();",
      "  const output = {};",
      "  for (const size of [16, 32]) {",
      "    const canvas = document.createElement('canvas');",
      "    canvas.width = size;",
      "    canvas.height = size;",
      "    const context = canvas.getContext('2d', { alpha: true });",
      "    context.imageSmoothingEnabled = true;",
      "    context.imageSmoothingQuality = 'high';",
      "    context.drawImage(image, 0, 0, size, size);",
      "    output[size] = canvas.toDataURL('image/png').split(',')[1];",
      "  }",
      "  return { userAgent: navigator.userAgent, pngs: output };",
      "})()",
    ].join("\n");
    const result = await sendCdp(socket, "Runtime.evaluate", {
      expression,
      awaitPromise: true,
      returnByValue: true,
    });
    if (result.exceptionDetails) {
      throw new Error(result.exceptionDetails.text ?? "SVG rasterization failed.");
    }
    socket.close();
    const value = result.result?.value;
    if (!value?.pngs?.[16] || !value.pngs[32]) {
      throw new Error("Chrome did not return both favicon sizes.");
    }
    return {
      userAgent: value.userAgent,
      pngs: Object.fromEntries(
        Object.entries(value.pngs).map(([size, base64]) => [
          Number(size),
          Buffer.from(base64, "base64"),
        ]),
      ),
    };
  } finally {
    if (chrome.exitCode === null) {
      const exited = new Promise((resolve) => chrome.once("exit", resolve));
      chrome.kill();
      await Promise.race([exited, new Promise((resolve) => setTimeout(resolve, 2000))]);
    }
    await rm(profile, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
  }
}

await mkdir(outputDirectory, { recursive: true });
const sourceBytesByName = new Map();
const outputRecords = [];
for (const asset of svgAssets) {
  const sourcePath = path.join(sourceDirectory, asset.source);
  const bytes = await readFile(sourcePath);
  sourceBytesByName.set(asset.source, bytes);
  const outputBytes = normalizedSvg(bytes);
  const outputPath = path.join(outputDirectory, asset.output);
  await writeFile(outputPath, outputBytes);
  const viewBox = outputBytes.toString("utf8").match(/\bviewBox="([^"]+)"/)?.[1] ?? "unspecified";
  outputRecords.push({
    source_file: asset.source,
    source_sha256: digest(bytes),
    role: asset.role,
    variant: asset.variant,
    composition: asset.composition,
    output_file: asset.output,
    output_dimensions: `viewBox ${viewBox}`,
    output_format: "SVG",
    output_operation: "UTF-8/LF; trailing horizontal whitespace removed; vector markup retained",
    output_sha256: digest(outputBytes),
  });
}

const rasterized = await rasterizeFavicon(sourceBytesByName.get("favicon.svg"));
for (const size of [16, 32]) {
  const outputFile = `favicon-${size}x${size}.png`;
  const bytes = rasterized.pngs[size];
  await writeFile(path.join(outputDirectory, outputFile), bytes);
  outputRecords.push({
    source_file: "favicon.svg",
    source_sha256: digest(sourceBytesByName.get("favicon.svg")),
    role: "favicon",
    variant: `${size}x${size}`,
    composition: "square-with-brand-safe-padding",
    output_file: outputFile,
    output_dimensions: `${size}x${size}`,
    output_format: "PNG",
    output_operation: "Direct SVG-to-canvas rasterization",
    output_sha256: digest(bytes),
  });
}

const icoBytes = makeIco(rasterized.pngs[32]);
await writeFile(path.join(outputDirectory, "favicon.ico"), icoBytes);
outputRecords.push({
  source_file: "favicon.svg",
  source_sha256: digest(sourceBytesByName.get("favicon.svg")),
  role: "favicon",
  variant: "32x32-embedded-png",
  composition: "square-with-brand-safe-padding",
  output_file: "favicon.ico",
  output_dimensions: "32x32 embedded PNG",
  output_format: "ICO",
  output_operation: "ICO container around the direct 32x32 SVG-derived PNG",
  output_sha256: digest(icoBytes),
});

const manifest = {
  schema_version: 1,
  source_directory: sourceDirectory,
  generator: "tools/brand_assets/generate.mjs",
  rasterizer: "Chrome headless Canvas; direct SVG-to-PNG, no intermediate raster",
  rasterizer_user_agent: rasterized.userAgent,
  assets: outputRecords,
};
const manifestBytes = Buffer.from(`${JSON.stringify(manifest, null, 2)}\n`, "utf8");
await writeFile(path.join(outputDirectory, "brand-assets.v1.json"), manifestBytes);
console.log(`BRAND_OUTPUT_DIRECTORY=${outputDirectory}`);
console.log(`GENERATED_ASSETS=${outputRecords.length}`);
console.log(`BRAND_MANIFEST_SHA256=${digest(manifestBytes)}`);
