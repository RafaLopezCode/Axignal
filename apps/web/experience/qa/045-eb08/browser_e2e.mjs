import fs from "node:fs";
import { spawn } from "node:child_process";

const chrome = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const debugPort = 9223;
const origin = process.env.AXIGNAL_EXPERIENCE_ORIGIN ?? "http://127.0.0.1:3810";
const dataDir = process.env.AXIGNAL_EB08_DATA_DIR;
if (!dataDir) throw new Error("AXIGNAL_EB08_DATA_DIR_REQUIRED");
const tokenPath = dataDir + "\\admin-session.key";
const profile = process.env.AXIGNAL_EB08_CHROME_PROFILE ?? dataDir + "-chrome";
fs.rmSync(profile, { recursive: true, force: true });
const token = fs.readFileSync(tokenPath, "utf8").trim();

const proc = spawn(chrome, [
  "--headless=new",
  "--disable-gpu",
  "--no-first-run",
  "--no-default-browser-check",
  "--remote-debugging-port=" + debugPort,
  "--user-data-dir=" + profile,
  "--window-size=1440,1000",
  "about:blank",
], { stdio: "ignore" });

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function waitJson(url, attempts = 100) {
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
    ws.onopen = () => resolve({
      ws,
      send(method, params = {}) {
        const id = next++;
        return new Promise((resolveCommand, rejectCommand) => {
          waiting.set(id, { resolve: resolveCommand, reject: rejectCommand });
          ws.send(JSON.stringify({ id, method, params }));
        });
      },
    });
    ws.onerror = reject;
  });
}

async function evaluate(send, expression) {
  const result = await send("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
  if (result.exceptionDetails) throw new Error("EVALUATION_FAILED");
  return result.result && result.result.value;
}

async function waitFor(send, expression, attempts = 100) {
  for (let i = 0; i < attempts; i++) {
    if (await evaluate(send, expression)) return true;
    await sleep(100);
  }
  return false;
}

async function openSignal(send) {
  return await evaluate(
    send,
    "(()=>{const labels=/Abrir hallazgo|Open finding|Ver señal y evidencia|Read signal and evidence|Abrir última observación|Open latest observation/;const b=[...document.querySelectorAll('button')].find(x=>labels.test(x.textContent||''));if(!b)return false;b.click();return true;})()",
  );
}

try {
  await waitJson("http://127.0.0.1:" + debugPort + "/json/version");
  const tab = await fetch(
    "http://127.0.0.1:" + debugPort + "/json/new?" + encodeURIComponent(origin + "/admin/customer-zero"),
    { method: "PUT" },
  ).then((r) => r.json());
  const connected = await connect(tab.webSocketDebuggerUrl);
  const ws = connected.ws;
  const send = connected.send;
  await send("Runtime.enable");
  await send("Page.enable");
  await send("Page.navigate", { url: origin + "/admin/customer-zero" });
  const originReady = await waitFor(
    send,
    "location.origin === 'http://127.0.0.1:3810' && document.readyState === 'complete'",
    150,
  );
  if (!originReady) throw new Error("EXPERIENCE_ORIGIN_NOT_READY");

  const authExpression = "(async()=>{const r=await fetch('/api/admin/session',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:" + JSON.stringify(token) + "})});return r.status;})()";
  const auth = await evaluate(send, authExpression);
  if (auth !== 200) throw new Error("ADMIN_SESSION_FAILED:" + auth);

  await send("Page.navigate", { url: origin + "/admin/customer-zero" });
  const loaded = await waitFor(
    send,
    "document.querySelector('main.panorama-main') !== null && document.body.innerText.includes('Arbor Cooling')",
    150,
  );
  if (!loaded) {
    const diagnostic = await evaluate(
      send,
      "(async()=>{const [context,organizations]=await Promise.all([fetch('/api/subscriber-context',{cache:'no-store'}),fetch('/api/organizations',{cache:'no-store'})]);return {contextStatus:context.status,contextBody:await context.text(),organizationsStatus:organizations.status,organizationsBody:await organizations.text(),visible:document.body.innerText.slice(0,1200)};})()",
    );
    console.error(JSON.stringify({ diagnostic }, null, 2));
    throw new Error("ECONOMIC_PROJECTION_NOT_RENDERED");
  }

  const overview = await evaluate(
    send,
    "(()=>{const body=document.body.innerText;return {arbor:body.includes('Arbor Cooling'),potential:/Potencial|Potential|POTENTIAL/.test(body),today:body.includes('Hoy')||body.includes('Today'),width:document.documentElement.scrollWidth,viewport:window.innerWidth};})()",
  );
  if (!overview.arbor || !overview.potential || !overview.today) throw new Error("PANORAMA_CONTENT_MISSING");
  if (overview.width > overview.viewport + 1) throw new Error("DESKTOP_OVERFLOW");

  if (!(await openSignal(send))) throw new Error("SIGNAL_ENTRY_CTA_MISSING");
  if (!(await waitFor(send, "document.querySelector('article.runtime-signal') !== null", 100)))
    throw new Error("SIGNAL_DETAIL_NOT_RENDERED");

  const desktop = await evaluate(
    send,
    "(()=>{const article=document.querySelector('article.runtime-signal');const body=document.body.innerText;return {articleId:article?.id??null,title:article?.querySelector('h2')?.textContent?.trim()??null,potential:/Potencial|Potential|POTENTIAL/.test(article?.innerText||''),arbor:body.includes('Arbor Cooling'),today:body.includes('Hoy')||body.includes('Today'),width:document.documentElement.scrollWidth,viewport:window.innerWidth};})()",
  );
  if (!desktop.articleId || !desktop.articleId.startsWith("xignal:economic:"))
    throw new Error("WRONG_SIGNAL_ID");
  if (!desktop.potential || !desktop.arbor || !desktop.today)
    throw new Error("DESKTOP_CONTENT_MISSING");
  if (desktop.width > desktop.viewport + 1) throw new Error("DESKTOP_OVERFLOW");

  const opened = await evaluate(
    send,
    "(()=>{const b=[...document.querySelectorAll('button')].find(x=>/Cómo lo sabe AXIGNAL|How AXIGNAL knows/.test(x.textContent||''));if(!b)return false;b.click();return true;})()",
  );
  if (!opened) throw new Error("EVIDENCE_BUTTON_MISSING");
  if (!(await waitFor(send, "document.querySelector('.evidence-journey') !== null")))
    throw new Error("EVIDENCE_NOT_OPEN");

  const evidence = await evaluate(
    send,
    "(()=>{const text=document.querySelector('.evidence-journey')?.innerText||'';return {arbor:text.includes('arbor-cooling.example'),harbor:text.includes('harbor-storage.example'),observation:/Observación|Observation/.test(text),textLength:text.length};})()",
  );
  if (!evidence.arbor || !evidence.harbor || !evidence.observation)
    throw new Error("EVIDENCE_LINEAGE_INCOMPLETE");

  const beforeReload = desktop.articleId;
  await send("Page.reload", { ignoreCache: true });
  if (!(await waitFor(send, "document.querySelector('main.panorama-main') !== null", 150)))
    throw new Error("RELOAD_PROJECTION_MISSING");
  if (!(await openSignal(send))) throw new Error("RELOAD_SIGNAL_ENTRY_MISSING");
  if (!(await waitFor(send, "document.querySelector('article.runtime-signal') !== null", 100)))
    throw new Error("RELOAD_SIGNAL_MISSING");
  const afterReload = await evaluate(
    send,
    "document.querySelector('article.runtime-signal')?.id ?? null",
  );
  if (afterReload !== beforeReload) throw new Error("RELOAD_CONTINUITY_FAILED");

  await send("Emulation.setDeviceMetricsOverride", {
    width: 390,
    height: 844,
    deviceScaleFactor: 1,
    mobile: true,
  });
  await send("Page.reload", { ignoreCache: true });
  if (!(await waitFor(send, "document.querySelector('main.panorama-main') !== null", 150)))
    throw new Error("MOBILE_PROJECTION_MISSING");
  if (!(await openSignal(send))) throw new Error("MOBILE_SIGNAL_ENTRY_MISSING");
  if (!(await waitFor(send, "document.querySelector('article.runtime-signal') !== null", 100)))
    throw new Error("MOBILE_SIGNAL_MISSING");
  const mobile = await evaluate(
    send,
    "(()=>{const tools=document.querySelector('.runtime-mobile-tools');return {scrollWidth:document.documentElement.scrollWidth,innerWidth:window.innerWidth,signal:!!document.querySelector('article.runtime-signal'),tools:!!tools&&getComputedStyle(tools).display!=='none'};})()",
  );
  if (!mobile.signal || !mobile.tools || mobile.scrollWidth > mobile.innerWidth + 1)
    throw new Error("MOBILE_LAYOUT_FAILED");

  console.log(
    JSON.stringify(
      {
        status: "PASS",
        overview,
        desktop,
        evidence,
        reloadSameSignal: afterReload === beforeReload,
        mobile,
      },
      null,
      2,
    ),
  );
  ws.close();
} finally {
  proc.kill();
}
