// Delivery assets are generated from translations.json, never authored here.
import fs from "node:fs";
const catalog = JSON.parse(
  fs.readFileSync(new URL("../lib/translations.json", import.meta.url), "utf8"),
);
const output = new URL("../lib/translation-delivery/", import.meta.url);
fs.mkdirSync(output, { recursive: true });
for (const [index, locale] of ["de", "pt", "fr", "it"].entries()) {
  const values = Object.fromEntries(
    Object.entries(catalog).map(([key, columns]) => [key, columns[index]]),
  );
  fs.writeFileSync(
    new URL(locale + ".json", output),
    JSON.stringify(values) + "\n",
  );
}
console.log(
  `Generated four locale delivery files, ${Object.keys(catalog).length} keys each.`,
);
