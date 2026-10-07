import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const localizedKnowledgeLocales = ["es", "en", "fr", "de", "it", "pt"];
export const expectedHtmlFilesPerLocale = 88;

function walkHtml(directory) {
  if (!fs.existsSync(directory)) return [];
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) return walkHtml(target);
    return entry.isFile() && entry.name.endsWith(".html") ? [target] : [];
  });
}

export function localizeStaticKnowledgeHtml({
  appDir,
  locales = localizedKnowledgeLocales,
  expectedPerLocale = expectedHtmlFilesPerLocale,
}) {
  const updated = [];
  for (const locale of locales) {
    const hub = path.join(appDir, locale, "knowledge.html");
    const articles = walkHtml(path.join(appDir, locale, "knowledge"));
    const files = [hub, ...articles];
    if (!fs.existsSync(hub))
      throw new Error(`Missing prerendered hub for ${locale}: ${hub}`);
    if (files.length !== expectedPerLocale)
      throw new Error(
        `Unexpected prerendered knowledge count for ${locale}: ${files.length}; expected ${expectedPerLocale}`,
      );
    for (const file of files) {
      const original = fs.readFileSync(file, "utf8");
      const match = original.match(/<html\b[^>]*\blang="([^"]+)"/);
      if (!match)
        throw new Error(`Missing html lang attribute in ${file}`);
      const localized = original.replace(
        /(<html\b[^>]*\blang=")[^"]+(")/,
        `$1${locale}$2`,
      );
      fs.writeFileSync(file, localized, "utf8");
      const verified = fs.readFileSync(file, "utf8").match(/<html\b[^>]*\blang="([^"]+)"/)?.[1];
      if (verified !== locale)
        throw new Error(`Failed to localize html lang for ${file}: ${verified ?? "missing"}`);
      updated.push(file);
    }
  }
  return updated;
}

const invokedDirectly =
  process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);

if (invokedDirectly) {
  const distDir = process.env.AXIGNAL_NEXT_DIST_DIR
    ? path.resolve(process.env.AXIGNAL_NEXT_DIST_DIR)
    : path.resolve("node_modules/.cache/axignal-next");
  const appDir = path.join(distDir, "server", "app");
  const updated = localizeStaticKnowledgeHtml({ appDir });
  console.log(`Localized html lang for ${updated.length} prerendered knowledge pages.`);
}
