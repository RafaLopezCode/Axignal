import type { MetadataRoute } from "next";
import { acquisitionPages, acquisitionHubs, localizedPagePath } from "@/lib/acquisition";
import { locales } from "@/lib/languages";
import { absolutePublicUrl, hreflangMap } from "@/lib/acquisition-seo";
import { homeLanguages } from "@/lib/site-seo";

export default function sitemap(): MetadataRoute.Sitemap {
  // The home page is the front door of the funnel and its only canonical landing URL.
  // The home page in each language has its own URL; every version declares the others.
  const languages = homeLanguages();
  const home: MetadataRoute.Sitemap = [
    { url: absolutePublicUrl("/"), alternates: { languages } },
    ...locales.map(({ id }) => ({ url: absolutePublicUrl(`/${id}`), alternates: { languages } })),
    { url: absolutePublicUrl("/pricing") },
  ];
  const hubs: MetadataRoute.Sitemap = acquisitionHubs.map((hub) => ({
    url: absolutePublicUrl(hub.path),
    alternates: { languages: hreflangMap(Object.fromEntries(acquisitionHubs.map((item) => [item.locale, item.path]))) },
  }));
  const articles: MetadataRoute.Sitemap = acquisitionPages.flatMap((page) => locales.flatMap(({ id }) => {
    if (!page.locales[id]) return [];
    const paths = Object.fromEntries(locales.flatMap(({ id: alternate }) => page.locales[alternate] ? [[alternate, localizedPagePath(page, alternate)]] : []));
    return [{
      url: absolutePublicUrl(localizedPagePath(page, id)),
      alternates: { languages: hreflangMap(paths) },
    }];
  }));
  return [...home, ...hubs, ...articles];
}
