# AXIGNAL Brand Asset Authority V2

**Status:** CANONICAL  
**Effective:** 2026-10-03  
**Supersedes:** `BRAND_ASSET_AUTHORITY_V1.md`

`D:\AXIGNAL\LOGOS` is the authoritative, read-only artwork source. Only the four
approved SVGs below are canonical source artwork. Previous gold/orbital-X source
artwork is retired and must not be reintroduced.

## Canonical source inventory

| Source | SHA-256 | Role | ViewBox / paths | Canonical treatment |
| --- | --- | --- | --- | --- |
| `favicon.svg` | `77e45a7b31d0ccabe3df4bd10963e4e6e857ae1be949c23f067f061908ae18a2` | Browser/search favicon source | `0 0 901 900`; 1 path | Monocle mark, AXIGNAL blue `#354F98` |
| `Logo_Claro.svg` | `3df29aa09f405b6a5de898841c90c7775909dfbdf344e17a5b6dc73a39c4e8b4` | Horizontal logo for light surfaces | `0 0 3011 873`; 2 paths | Monocle `#354F98`; wordmark `#4C4C4C` |
| `Logo_Oscuro.svg` | `15e6c61ccea2134c546ee34cf3d64e6761b34a3278d71642133ee97946ad8fcf` | Horizontal logo for dark surfaces | `0 0 3011 873`; 2 paths | Monocle `#354F98`; wordmark white |
| `rrss.svg` | `a685a164c1b05862da26825c0f74ed9228f6152ddef96f29a199dbbfe6dddd61` | Social/avatar/isotipo source | `0 0 901 900`; 1 path | Monocle mark, AXIGNAL blue `#354F98` |

All four sources are vector paths. They contain no SVG `<text>` or raster images.

## Brand semantics

The canonical isotipo is a **single observation monocle/lens**. It expresses
focus, observation, examination, evidence and contextual attention.

It is not an orbital X and no longer creates a requirement for X-prefixed product
terminology.

The same mark is the monocle held by **El Observador**. In character use:
- exactly one monocle;
- no chain/string;
- held with one hand;
- second eye remains visibly free;
- no mutation into glasses or a two-lens symbol.

## Generated web assets

`tools/brand_assets/generate.mjs` deterministically produces:
- `logo-light.svg`
- `logo-dark.svg`
- `isotope.svg`
- `favicon.svg`
- favicon PNGs at 16, 32, 48, 96, 180, 192 and 512 px
- `favicon.ico`
- `brand-assets.v1.json` provenance manifest

Distribution aliases include:
- `apple-touch-icon.png` (180×180)
- `icon-192.png`
- `icon-512.png`
- `organization-logo-512.png`
- `serp-logo-512.png`
- `social-avatar.svg`
- `safari-pinned-tab.svg`

`tools/brand_assets/generate-social.mjs` produces:
- `og-image-1200x630.png`
- `twitter-image-1200x630.png`
- `social-square-1200.png`

## Search / SEO requirements

The landing must expose:
- a crawlable square PNG favicon of at least 48×48 for search-result compatibility;
- SVG and ICO browser fallbacks;
- 180×180 Apple touch icon;
- 192/512 application icons;
- 1200×630 Open Graph/Twitter sharing artwork;
- a crawlable 512×512 Organization logo for structured data;
- absolute canonical URLs in social metadata and Organization/WebSite JSON-LD.

Search-result rendering remains controlled by search engines; AXIGNAL supplies
eligible, crawlable assets and structured metadata but does not claim guaranteed
SERP appearance.

## Reproduction

```powershell
node tools/brand_assets/generate.mjs `
  --source 'D:\AXIGNAL\LOGOS' `
  --output 'apps/web/subscriber/assets/brand' `
  --chrome 'C:\Program Files\Google\Chrome\Application\chrome.exe'

node tools/brand_assets/generate-social.mjs
```

The same approved derivatives are distributed to the landing brand directory.

## Prohibitions

- Do not recolor the canonical source SVGs ad hoc.
- Do not restore gold `#AFA68A` or the orbital-X artwork as current identity.
- Do not regenerate the wordmark with live text as a substitute for official artwork.
- Do not infer a second lens from the Observer's free eye.
- Do not use old assets from historical specs as active brand sources.
