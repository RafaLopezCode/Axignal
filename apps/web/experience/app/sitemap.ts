import type { MetadataRoute } from "next";
import { acquisitionPages, acquisitionHubs, localizedPagePath } from "@/lib/acquisition";
import { locales } from "@/lib/languages";
import { absolutePublicUrl, hreflangMap } from "@/lib/acquisition-seo";

export default function sitemap(): MetadataRoute.Sitemap {
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
  return [...hubs, ...articles];
}
