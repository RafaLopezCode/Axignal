// Minimal Chrome DevTools Protocol driver for funnel QA. No browser package: it drives
// the locally installed Chrome, headless, with a throwaway profile. Read-only against
// the target origin except for the clicks a visitor would make.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";

const CHROME = process.env.AXIGNAL_QA_CHROME ?? "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
export const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function waitJson(url, attempts = 150) {
  for (let i = 0; i < attempts; i++) {
    try {
      const response = await fetch(url);
      if (response.ok) return await response.json();
    } catch {}
    await sleep(100);
  }
  throw new Error("CDP_NOT_READY");
}

function connect(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let next = 1;
  const waiting = new Map();
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.id && waiting.has(message.id)) {
      const pending = waiting.get(message.id);
      waiting.delete(message.id);
      if (message.error) pending.reject(new Error(JSON.stringify(message.error)));
      else pending.resolve(message.result);
    }
  };
  return new Promise((resolve, reject) => {
    ws.onopen = () =>
      resolve({
        ws,
        send(method, params = {}) {
          const id = next++;
          return new Promise((ok, fail) => {
            waiting.set(id, { resolve: ok, reject: fail });
            ws.send(JSON.stringify({ id, method, params }));
          });
        },
      });
    ws.onerror = reject;
  });
}

export async function launch(port = 9241) {
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), "axignal-funnel-qa-"));
  const proc = spawn(
    CHROME,
    [
      "--headless=new",
      "--disable-gpu",
      "--hide-scrollbars",
      "--no-first-run",
      "--no-default-browser-check",
      "--remote-debugging-port=" + port,
      "--user-data-dir=" + profile,
      "about:blank",
    ],
    { stdio: "ignore" },
  );
  await waitJson("http://127.0.0.1:" + port + "/json/version");
  const tab = await fetch("http://127.0.0.1:" + port + "/json/new?about:blank", { method: "PUT" }).then((r) => r.json());
  const { ws, send } = await connect(tab.webSocketDebuggerUrl);
  await send("Runtime.enable");
  await send("Page.enable");
  const page = {
    send,
    async viewport(width, height = 900, mobile = width < 768) {
      await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile });
    },
    async evaluate(expression) {
      const result = await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
      if (result.exceptionDetails) throw new Error("EVALUATION_FAILED: " + JSON.stringify(result.exceptionDetails).slice(0, 400));
      return result.result && result.result.value;
    },
    async waitFor(expression, attempts = 120) {
      for (let i = 0; i < attempts; i++) {
        if (await page.evaluate(expression)) return true;
        await sleep(100);
      }
      return false;
    },
    async goto(url) {
      await send("Page.navigate", { url });
      await page.waitFor("document.readyState === 'complete'");
      await sleep(900);
    },
    async screenshot(file, { full = true, jpeg = false } = {}) {
      let clip;
      if (full) {
        const height = await page.evaluate("Math.ceil(document.documentElement.scrollHeight)");
        const width = await page.evaluate("document.documentElement.clientWidth");
        clip = { x: 0, y: 0, width, height: Math.min(height, 12000), scale: 1 };
      }
      const shot = await send("Page.captureScreenshot", { format: jpeg ? "jpeg" : "png", ...(jpeg ? { quality: 72 } : {}), captureBeyondViewport: full, ...(clip ? { clip } : {}) });
      fs.mkdirSync(path.dirname(file), { recursive: true });
      fs.writeFileSync(file, Buffer.from(shot.data, "base64"));
    },
    async close() {
      try { ws.close(); } catch {}
      proc.kill();
      await sleep(300);
      fs.rmSync(profile, { recursive: true, force: true, maxRetries: 5 });
    },
  };
  return page;
}
