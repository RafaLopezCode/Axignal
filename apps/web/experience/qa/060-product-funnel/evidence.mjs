// Above-the-fold before/after evidence for the PR (small JPEGs, privacy notice dismissed
// except on the first-visit phone shot). Usage: node evidence.mjs <origin> <label> <out-dir>
import path from "node:path";
import { launch } from "./cdp.mjs";

const [origin, label, out] = process.argv.slice(2);
const shots = [
  ["landing", "/", 1440], ["landing", "/", 390],
  ["pricing", "/#pricing", 1440], ["pricing", "/#pricing", 390],
  ["example", "/panorama", 1440], ["example", "/panorama", 390],
  ["example-evidence", "/panorama?signal=renovation&depth=prove", 1440],
  ["signup", "/signup", 1440], ["signup", "/signup", 390],
];
const page = await launch(9245);
try {
  await page.viewport(390, 844);
  await page.goto(origin + "/");
  await page.screenshot(path.join(out, `${label}-landing-390-first-visit.jpg`), { full: false, jpeg: true });
  await page.evaluate(`localStorage.setItem("axignal.privacy-notice.v1", JSON.stringify({ dismissedAt: Date.now() })); true`);
  for (const [name, route, width] of shots) {
    await page.viewport(width, width < 768 ? 844 : 900);
    await page.goto(origin + route);
    if (route.includes("#")) await page.evaluate(`document.querySelector(${JSON.stringify(route.slice(route.indexOf("#")))})?.scrollIntoView(); true`);
    await new Promise((r) => setTimeout(r, 700));
    await page.screenshot(path.join(out, `${label}-${name}-${width}.jpg`), { full: false, jpeg: true });
  }
} finally {
  await page.close();
}
console.log("ok", label);
