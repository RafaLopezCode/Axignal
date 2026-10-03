import ts from "typescript";
import fs from "node:fs";
import path from "node:path";
export function collectCopy() {
  const rows = new Map();
  function add(es, en, file) {
    if (!rows.has(en)) rows.set(en, { en, es, files: [] });
    rows.get(en).files.push(file.replaceAll("\\", "/"));
  }
  function walk(dir) {
    for (const f of fs.readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, f.name);
      if (f.isDirectory()) walk(p);
      else if (/\.tsx?$/.test(p) && !p.includes("copy-catalog")) {
        const sf = ts.createSourceFile(
          p,
          fs.readFileSync(p, "utf8"),
          ts.ScriptTarget.Latest,
          true,
        );
        function visit(n) {
          if (
            ts.isCallExpression(n) &&
            ts.isIdentifier(n.expression) &&
            ["t", "c", "translate"].includes(n.expression.text) &&
            n.arguments.length >= 2 &&
            ts.isStringLiteral(n.arguments[0]) &&
            ts.isStringLiteral(n.arguments[1])
          )
            add(n.arguments[0].text, n.arguments[1].text, p);
          if (ts.isObjectLiteralExpression(n)) {
            const prop = (name) =>
              n.properties.find(
                (p) =>
                  ts.isPropertyAssignment(p) &&
                  ((ts.isIdentifier(p.name) && p.name.text === name) ||
                    (ts.isStringLiteral(p.name) && p.name.text === name)),
              );
            const es = prop("es"),
              en = prop("en");
            if (
              es &&
              en &&
              ts.isStringLiteral(es.initializer) &&
              ts.isStringLiteral(en.initializer)
            )
              add(es.initializer.text, en.initializer.text, p);
          }
          ts.forEachChild(n, visit);
        }
        visit(sf);
      }
    }
  }
  walk("components");
  walk("lib");
  walk("app");
  return [...rows.values()];
}
if (process.argv[1]?.endsWith("locale-inventory.mjs")) {
  const rows = collectCopy();
  if (process.argv[2] === "--check") {
    const catalog = JSON.parse(
      fs.readFileSync("lib/translations.json", "utf8"),
    );
    const missing = rows.filter(
      (r) =>
        !Array.isArray(catalog[r.en]) ||
        catalog[r.en].length !== 4 ||
        catalog[r.en].some((v) => typeof v !== "string" || !v.trim()),
    );
    console.log({ entries: rows.length, missing: missing.map((r) => r.en) });
    if (missing.length) process.exitCode = 1;
  } else {
    fs.writeFileSync(
      "lib/translation-source.json",
      JSON.stringify(rows, null, 2) + "\n",
    );
    console.log({
      count: rows.length,
      characters: rows.reduce((a, r) => a + r.en.length, 0),
    });
    const from = Number(process.argv[2] ?? 0),
      to = Number(process.argv[3] ?? rows.length);
    for (let i = from; i < Math.min(to, rows.length); i++)
      console.log(i + "|" + rows[i].en);
  }
}
