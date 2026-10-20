import type { Metadata } from "next";

/** Approved derivatives only: BRAND_ASSET_AUTHORITY_V2, Search / SEO requirements. */
export const siteIcons = {
  icon: [
    { url: "/brand/favicon-96x96.png", type: "image/png", sizes: "96x96" },
    {
      url: "/brand/favicon.ico",
      type: "image/x-icon",
      sizes: "16x16 32x32 48x48",
    },
    { url: "/brand/favicon.svg", type: "image/svg+xml", sizes: "any" },
  ],
  apple: [{ url: "/brand/apple-touch-icon.png", sizes: "180x180", type: "image/png" }],
  other: [
    { rel: "icon", url: "/brand/icon-192.png", sizes: "192x192", type: "image/png" },
    { rel: "icon", url: "/brand/icon-512.png", sizes: "512x512", type: "image/png" },
  ],
} satisfies Metadata["icons"];
