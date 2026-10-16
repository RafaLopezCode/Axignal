export const localizedKnowledgeLocales: string[];
export const expectedHtmlFilesPerLocale: number;
export const localizedPublicPagePaths: string[];
export function localizeStaticKnowledgeHtml(options: {
  appDir: string;
  locales?: string[];
  expectedPerLocale?: number;
}): string[];
export function localizeStaticPublicHtml(options: {
  appDir: string;
  locales?: string[];
}): string[];
