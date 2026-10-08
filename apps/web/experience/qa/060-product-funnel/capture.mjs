// Full-page funnel screenshots at the four review widths, plus a per-page audit:
// horizontal overflow, h1 count, unnamed buttons/links and small touch targets.
// Usage: node capture.mjs <origin> <out-dir>
import fs from "node:fs";
import path from "node:path";
import { launch } from "./cdp.mjs";

const [origin = "http://127.0.0.1:3830", out = "qa-shots"] = process.argv.slice(2);
const widths = [1440, 1024, 768, 390];
const pages = [
  ["landing", "/"],
  ["example", "/panorama"],
  ["example-reach", "/panorama?family=markets"],
  ["example-evidence", "/panorama?signal=renovation&depth=prove"],
  ["signup", "/signup"],
  ["login", "/login"],
  ["policies", "/policies"],
];
const audit = `(() => {
  const visible = (el) => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 0 && r.height > 0 && s.visibility !== "hidden" && s.display !== "none"; };
  const controls = [...document.querySelectorAll("a[href],button")].filter(visible);
  const unnamed = controls.filter((el) => !(el.getAttribute("aria-label") || el.textContent || "").trim()).map((el) => el.outerHTML.slice(0, 80));
  const small = controls.filter((el) => { const r = el.getBoundingClientRect(); return r.height < 24 || r.width < 24; }).map((el) => (el.textContent || el.getAttribute("aria-label") || "").trim().slice(0, 40));
  return { overflow: document.documentElement.scrollWidth > innerWidth + 1, h1: document.querySelectorAll("h1").length, title: document.title, unnamed, smallTargets: small.slice(0, 8) };
})()`;

const page = await launch();
const report = [];
try {
  await page.goto(origin + "/");
  await page.evaluate(`localStorage.setItem("axignal.privacy-notice.v1", JSON.stringify({ dismissedAt: Date.now() })); true`);
  for (const width of widths) {
    await page.viewport(width, width < 768 ? 844 : 900);
    for (const [name, route] of pages) {
      await page.goto(origin + route);
      await page.evaluate("document.querySelectorAll('.reveal').forEach((n) => n.classList.add('in-view')); true");
      await new Promise((r) => setTimeout(r, 400));
      const file = path.join(out, `${name}-${width}.png`);
      await page.screenshot(file);
      report.push({ width, name, route, ...(await page.evaluate(audit)) });
    }
  }
  // First visit on a phone, with the privacy notice, above the fold only.
  await page.viewport(390, 844);
  await page.evaluate(`localStorage.removeItem("axignal.privacy-notice.v1"); true`);
  await page.goto(origin + "/");
  await page.screenshot(path.join(out, "landing-390-first-visit.png"), { full: false });
} finally {
  await page.close();
}
fs.writeFileSync(path.join(out, "audit.json"), JSON.stringify(report, null, 2) + "\n");
const problems = report.filter((r) => r.overflow || r.unnamed.length || r.h1 !== 1);
console.log(JSON.stringify({ captured: report.length, problems: problems.map(({ width, name, overflow, h1, unnamed }) => ({ width, name, overflow, h1, unnamed: unnamed.length })) }, null, 2));
