// Deterministic delivery only. The seven original stylesheets remain authority.
import fs from "node:fs";
import { createHash } from "node:crypto";
import postcss from "postcss";
const root = new URL("../", import.meta.url);
const check = process.argv.includes("--check");
const sources = [
  "app/globals.css",
  "app/public.css",
  "app/typography.css",
  "app/acquisition.css",
  "app/funnel.css",
  "app/public-layout.css",
  "components/cognition/cognition.css",
];
const sheets = sources.map((path) => ({
  path,
  text: fs.readFileSync(new URL(path, root), "utf8").replace(/\r\n/g, "\n"),
}));
const legacy = sheets
  .map(({ path, text }) => `/* ${path} */\n${text}`)
  .join("\n");
const allowed =
  /\.(?:button|icon-button|dialog|skip-link|sr-only|mono|eyebrow|privacy-[\w-]+|publication-note|draft-form|weekly-brief-form|form-fields|form-bottom|brief-consent|field-error|marketing-newsletter-channel|marketing-text-link|lab-newsletter-channel|rights-request-copy)(?![\w-])/;
const unrelated =
  /\.(?:product[\w-]*|admin[\w-]*|canonical[\w-]*|axent[\w-]*|obs-[\w-]*|cg-[\w-]*|public-page|public-header|public-footer|public-main|public-back-top|mini-footer|acquisition-[\w-]*)\b/;
function select(node) {
  if (node.type === "rule") {
    const selectors = postcss.list
      .comma(node.selector)
      .filter(
        (selector) =>
          !unrelated.test(selector) &&
          (allowed.test(selector) || !selector.includes(".")),
      );
    return selectors.length
      ? node.clone({ selector: selectors.join(",\n") })
      : null;
  }
  if (node.type === "atrule" && node.name !== "font-face") {
    if (node.name.endsWith("keyframes")) return node.clone();
    const children = node.nodes?.map(select).filter(Boolean);
    if (children?.length) return node.clone({ nodes: children });
  }
  return null;
}
const foundation = postcss.root();
for (const { path, text } of sheets.filter(
  (sheet) => !sheet.path.startsWith("components/"),
)) {
  for (const node of postcss.parse(text, { from: path }).nodes) {
    const chosen = select(node);
    if (chosen) foundation.append(chosen);
  }
}
// Outside the lab repertoire, the original licensed faces remain available.
const fonts = JSON.parse(
  fs.readFileSync(new URL("lib/landing-lab-fonts.json", root), "utf8"),
).fonts;
const ranges = fonts[0].unicodeRange
  .split(",")
  .map((value) =>
    value
      .slice(2)
      .split("-")
      .map((value) => parseInt(value, 16)),
  )
  .map(([a, b]) => [a, b ?? a]);
let cursor = 0;
const complement = [];
for (const [start, end] of ranges) {
  if (cursor < start) complement.push([cursor, start - 1]);
  cursor = end + 1;
}
if (cursor <= 0x10ffff) complement.push([cursor, 0x10ffff]);
const outside = complement
  .map(([a, b]) => `U+${a.toString(16)}-${b.toString(16)}`)
  .join(",");
const fallback = fonts
  .map(
    (font) =>
      `@font-face{font-family:${JSON.stringify(font.family)};src:url("${font.source}") format("woff2");font-weight:${font.weight};font-display:swap;unicode-range:${outside}}`,
  )
  .join("\n");
const controls = fs.readFileSync(
  new URL("components/landing-shared-controls.css", root),
  "utf8",
);
const base = fallback + "\n" + foundation.toString() + "\n" + controls;
const folder = new URL("public/styles/", root);
fs.mkdirSync(folder, { recursive: true });
const manifest = {
  sources,
  fontManifestSha256: createHash("sha256")
    .update(fs.readFileSync(new URL("lib/landing-lab-fonts.json", root)))
    .digest("hex"),
};
for (const [name, text] of [
  ["base", base],
  ["legacy", legacy],
]) {
  const sha256 = createHash("sha256").update(text).digest("hex");
  const filename = `${name}.${sha256.slice(0, 12)}.css`;
  if (check) {
    if (fs.readFileSync(new URL(filename, folder), "utf8") !== text)
      throw new Error("Regenerate surface styles");
  } else fs.writeFileSync(new URL(filename, folder), text);
  manifest[name] = {
    url: "/styles/" + filename,
    bytes: Buffer.byteLength(text),
    sha256,
  };
}
const manifestText = JSON.stringify(manifest, null, 2) + "\n";
if (check) {
  if (
    fs.readFileSync(new URL("lib/surface-styles.json", root), "utf8") !==
    manifestText
  )
    throw new Error("Regenerate surface styles");
} else fs.writeFileSync(new URL("lib/surface-styles.json", root), manifestText);

// Prepare exact asset paths; never apply the production configuration here.
const edgePath = new URL(
  "../../../deploy/production/traefik/axignal-public-seo.yml",
  root,
);
let edge = fs.readFileSync(edgePath, "utf8").replace(/\r\n/g, "\n");
const assetLines =
  [manifest.base.url, manifest.legacy.url]
    .map((url) => `         Path(\`${url}\`) ||`)
    .join("\n") + "\n";
if (check) {
  for (const asset of [manifest.base, manifest.legacy]) {
    if (!edge.includes(`Path(\`${asset.url}\`)`))
      throw new Error("Exact style asset ingress is stale");
  }
  if (edge.includes("PathPrefix(`/styles"))
    throw new Error("Style ingress must be exact");
} else {
  edge = edge.replace(
    /^\s*Path\(`\/styles\/(?:base|legacy)\.[a-f0-9]{12}\.css`\) \|\|\n/gm,
    "",
  );
  edge = edge.replace(
    "         PathPrefix(`/brand/`) ||",
    assetLines + "         PathPrefix(`/brand/`) ||",
  );
  fs.writeFileSync(edgePath, edge);
}
console.log(JSON.stringify(manifest));
