import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const localizedKnowledgeLocales = ["es", "en", "fr", "de", "it", "pt"];
export const expectedHtmlFilesPerLocale = 89;

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

export const localizedPublicPagePaths = ["", "data", "industries", "pricing", "industries/industry", "industries/construction", "industries/energy", "industries/logistics", "industries/professional-services", "industries/agencies"];

/** Patch the known public catalog only; missing output or language attributes fail closed. */
export function localizeStaticPublicHtml({appDir, locales=localizedKnowledgeLocales, pages=localizedPublicPagePaths}) {
  const updated=[];
  for(const locale of locales) {
    for(const page of pages) {
      const file=path.join(appDir, page ? `${locale}/${page}.html` : `${locale}.html`);
      if(!fs.existsSync(file)) throw new Error(`Missing prerendered public page: ${file}`);
      const original=fs.readFileSync(file,"utf8");
      if(!/<html\b[^>]*\blang="[^"]+"/.test(original)) throw new Error(`Missing html lang attribute in ${file}`);
      // Attribute order is not fixed. Match the closing quote, not a required trailing space.
      const html=original.replace(/(<html\b[^>]*\blang=")[^"]+(")/, `$1${locale}$2`);
      fs.writeFileSync(file,html,"utf8");
      const verified=fs.readFileSync(file,"utf8").match(/<html\b[^>]*\blang="([^"]+)"/)?.[1];
      if(verified!==locale) throw new Error(`Failed to localize public html lang: ${file}`);
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
  const publicPages=localizeStaticPublicHtml({appDir, pages:[...localizedPublicPagePaths,"landing-lab"]});
  console.log(`Localized html lang for ${updated.length} knowledge and ${publicPages.length} public catalog pages.`);
}
