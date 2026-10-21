import fs from "node:fs";
import ts from "typescript";
import { getLandingLabContent } from "../lib/landing-lab-content";
import { labInsight } from "../lib/landing-lab-model";
import { EXAMPLE_MOMENTS } from "../lib/landing-observatory";
import { locales } from "../lib/languages";
import { translate } from "../lib/copy-catalog";
import { publicNavigationCopy } from "../lib/public-navigation";
const data = getLandingLabContent(null);
let text = JSON.stringify(data) + JSON.stringify(publicNavigationCopy) + "0123456789.,+−€ /";
for (const { id } of locales)
  for (const moment of EXAMPLE_MOMENTS)
    for (const question of data.labQuestions)
      text += JSON.stringify(
        labInsight(moment, question.id, (value) =>
          translate(value.es, value.en, id),
        ),
      );
const file = new URL("../components/landing-lab.tsx", import.meta.url);
const tree = ts.createSourceFile(
  file.pathname,
  fs.readFileSync(file, "utf8"),
  ts.ScriptTarget.Latest,
  true,
  ts.ScriptKind.TSX,
);
function visit(node: ts.Node) {
  if (
    ts.isStringLiteral(node) ||
    ts.isNoSubstitutionTemplateLiteral(node) ||
    ts.isJsxText(node)
  )
    text += node.text;
  ts.forEachChild(node, visit);
}
visit(tree);
const chars = [...new Set([...text])]
  .filter((char) => {
    const n = char.codePointAt(0)!;
    return (
      (n >= 0x20 && n <= 0x24f) ||
      (n >= 0x300 && n <= 0x36f) ||
      (n >= 0x2000 && n <= 0x206f) ||
      (n >= 0x20a0 && n <= 0x20cf) ||
      (n >= 0x2190 && n <= 0x21ff) ||
      n === 0x2212 ||
      n === 0x221e
    );
  })
  .sort((a, b) => a.codePointAt(0)! - b.codePointAt(0)!);
const output =
  JSON.stringify(
    {
      note: "Exact public landing wording, inline literals and all 90 existing synthetic views; includes the zero glyph for ch widths.",
      characters: chars.join(""),
    },
    null,
    2,
  ) + "\n";
const target = new URL("../lib/landing-lab-repertoire.json", import.meta.url);
if (process.argv.includes("--check")) {
  if (fs.readFileSync(target, "utf8") !== output)
    throw new Error("Regenerate landing repertoire and official font subsets");
} else fs.writeFileSync(target, output);
console.log(`${chars.length} editorial characters`);
