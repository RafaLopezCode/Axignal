// Spec 060 funnel E2E, driven like a visitor (clicks, not URLs):
// landing → promise → open the one example → a change → why it matters → its evidence
// → back to AXIGNAL → pricing → sign up. Prints each step; exits non-zero on failure.
// Usage: node funnel_e2e.mjs [origin] [width]
import { launch } from "./cdp.mjs";

const origin = process.argv[2] ?? "http://127.0.0.1:3830";
const width = Number(process.argv[3] ?? 1440);
const steps = [];
const page = await launch(9243);

const text = () => page.evaluate("document.body.innerText");
async function click(selector, label) {
  const ok = await page.evaluate(`(() => {
    const re = new RegExp(${JSON.stringify(label)});
    const el = [...document.querySelectorAll(${JSON.stringify(selector)})]
      .find((n) => re.test((n.textContent || n.getAttribute("aria-label") || "").trim()) && n.getBoundingClientRect().height > 0);
    if (!el) return false;
    el.scrollIntoView({ block: "center" });
    el.click();
    return true;
  })()`);
  if (!ok) throw new Error(`NOT_FOUND: ${selector} ~ ${label}`);
}
async function step(name, check) {
  const ok = await check();
  steps.push({ step: name, ok, at: await page.evaluate("location.pathname + location.search + location.hash") });
  if (!ok) throw new Error("STEP_FAILED: " + name);
}

try {
  await page.viewport(width, width < 768 ? 844 : 900);
  await page.goto(origin + "/");
  await page.evaluate(`localStorage.setItem("axignal.privacy-notice.v1", JSON.stringify({ dismissedAt: Date.now() })); location.reload(); true`);
  await page.waitFor("document.readyState === 'complete' && !!document.querySelector('h1')");
  await new Promise((r) => setTimeout(r, 800));

  await step("5s: the promise says what, for whom and what for", async () => {
    const body = await text();
    return /Sabe qué cambia alrededor de tu empresa/.test(body) &&
      /las organizaciones que eliges/.test(body) &&
      /Para quien dirige o hace crecer una empresa/.test(body);
  });
  await step("30s: observe, remember, change, relevance, why", async () => {
    const body = await text();
    return ["AXIGNAL observa y recuerda.", "Ves lo que importa y por qué.", "Dice lo que todavía no sabe.", "Recuerda cuándo supo cada cosa."]
      .every((phrase) => body.includes(phrase));
  });

  await click("a", "^Ver un ejemplo");
  await page.waitFor("location.pathname === '/demo' && document.body.innerText.includes('Ejemplo guiado con una organización ficticia')");
  await new Promise((r) => setTimeout(r, 1200));
  await step("example is clearly an example, not your account", async () => {
    const body = await text();
    return body.includes("Norte Renovable: Reforma edificios para que gasten menos energía") && body.includes("En tu cuenta, AXIGNAL observa las organizaciones reales");
  });
  await step("first view shows its economic world", async () => {
    const body = await text();
    return ["Dónde trabaja", "Dónde podría crecer", "Qué le afecta desde fuera"].every((p) => body.includes(p));
  });

  await click("button", "Entender por qué importa");
  await page.waitFor("!!document.querySelector('article.signal-detail')");
  await step("a change: what happened", async () => (await text()).includes("Un programa público de ayudas encaja con lo que hace."));
  await step("why it matters", async () => /El programa paga el tipo de obra que Norte Renovable dice hacer/.test(await text()));

  await click("[role=tab]", "Evidencia");
  await page.waitFor("location.search.includes('depth=prove')");
  await new Promise((r) => setTimeout(r, 600));
  await step("its evidence: source and observation date", async () => {
    const body = await text();
    return body.includes("Programa público de ayudas para que los edificios gasten menos energía") && /1 sept 2026|1 sep 2026/.test(body);
  });

  await click("a", "^Volver a AXIGNAL$");
  await page.waitFor("location.pathname === '/'");
  await new Promise((r) => setTimeout(r, 800));
  await step("back on the product journey", async () => (await text()).includes("Sabe qué cambia"));

  if (width >= 800) await click(".public-header nav a", "^Precio$");
  else {
    await click("button", "Abrir navegación");
    await page.waitFor("!!document.querySelector('.public-menu')");
    await click(".public-menu a", "^Precio");
  }
  await new Promise((r) => setTimeout(r, 800));
  await step("pricing answers what I pay and what one organization is", async () => {
    const body = await text();
    return body.includes("Pagas por organización observada.") && body.includes("Una organización es una empresa que AXIGNAL observa para ti") && /9,95\s?€/.test(body) && /4,95\s?€/.test(body);
  });

  await click("#pricing a", "Empieza con tu organización");
  await page.waitFor("location.pathname === '/signup'");
  await new Promise((r) => setTimeout(r, 800));
  await step("sign up says what happens next", async () => {
    const body = await text();
    return body.includes("Empieza con tu organización.") && body.includes("Añade una organización") && !/esta versión no crea cuentas/.test(body);
  });
  await step("no prototype language anywhere on the way", async () => !/Esta demo|versión local|datos ilustrativos/.test(await text()));
} catch (error) {
  steps.push({ step: "error", ok: false, detail: String(error) });
} finally {
  await page.close();
}
console.log(JSON.stringify({ width, steps }, null, 2));
if (steps.some((s) => !s.ok)) process.exitCode = 1;
