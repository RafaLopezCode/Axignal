> **SUPERSEDED 2026-10-03:** Historical record only. Current authority is
> [BRAND_ASSET_AUTHORITY_V2.md](./BRAND_ASSET_AUTHORITY_V2.md). The gold/orbital-X
> artwork documented below is retired and must not be used by current runtime.

# AXIGNAL Brand Asset Authority V1

`D:\AXIGNAL\LOGOS` is the authoritative, read-only artwork source. The SVGs
were inventoried, hashed, and rendered against light and dark browser
backgrounds before integration. No source SVG was changed.

## Source inventory

All five SVGs use a transparent canvas, contain vector paths only, and have no
embedded raster images or SVG `<text>` nodes. Their intrinsic geometry is
defined by `viewBox`; explicit `width` and `height` attributes are absent.

| Source file | SHA-256 | Role and composition | ViewBox / paths | Rendered artwork | Use |
|---|---|---|---|---|---|
| `axignal_isotipo.svg` | `b205bb55c8d9adc952ad2ce6219848bb37b99eaee9711cc9b724bce4ac482d63` | AXIGNAL isotope; square | `0 0 3000 3000`; 1 path | Monochrome brand gold `#AFA68A` | Canonical UI isotope on light and dark backgrounds; no recoloring |
| `favicon.svg` | `aa3bf8a91bba84f02f1319b38bbc8cce30007843acbbb45314f11fcf8bbfbd67` | Browser isotope; square | `0 0 3000 3000`; 1 path | Monochrome brand gold `#AFA68A`; source geometry has more interior padding than the main isotope | SVG favicon and direct raster source |
| `logo_horizontal_light_fraunces.svg` | `721b0fe9d610a2387f44ef08059a8099b0b0b9afb7e21321bfab9c15b964a2b9` | AXIGNAL wordmark + isotope; horizontal | `0 0 1542 389`; 14 paths | Isotope `#AFA68A`; wordmark `#4C4C4C` | Light-background UI |
| `logo_horizontal_dark_fraunces.svg` | `a60e6389320ae4dd1afc3d477e5e51ca11adf6afdca961bed65b6f816bc9e77a` | AXIGNAL wordmark + isotope; horizontal | `0 0 1542 389`; 14 paths | Isotope `#AFA68A`; wordmark white | Dark-background readiness |
| `rrss.svg` | `0f6f7be0ca0915d1e1376962a55295945c87017508db943b14f2d164af3ff92b` | Social/profile isotope; square | `0 0 3000 3000`; 1 path | Monochrome brand gold `#AFA68A` | Not copied; no current consumer |

The horizontal logo wordmark is outlined vector artwork, not live text. The
light and dark logo variants preserve the same geometry and differ only in
their official wordmark treatment. The single official isotope treatment is
used unchanged in both contexts; the UI image is decorative because its
containing link already has the accessible name `AXIGNAL · Today`.

## Integrated assets and provenance

Generated/copied outputs live in
`apps/web/subscriber/assets/brand/`. The generator is
`tools/brand_assets/generate.mjs`; SVG derivatives normalize line endings to
UTF-8/LF and remove trailing horizontal whitespace only. Vector paths, colors,
viewBox and artwork remain unchanged. It uses headless Chrome Canvas to
rasterize each PNG directly from the authoritative `favicon.svg` source.
`favicon.ico` wraps the generated 32×32 PNG. No raster is resized from another
raster, no runtime image dependency was added, and the originals remain
untouched.

`brand-assets.v1.json` records each source filename and SHA-256, output name,
dimensions, format, transformation and output SHA-256. It also records the
rasterizer user agent.
Reproduce with:

```powershell
node tools/brand_assets/generate.mjs `
  --source 'D:\AXIGNAL\LOGOS' `
  --output 'apps/web/subscriber/assets/brand' `
  --chrome 'C:\Program Files\Google\Chrome\Application\chrome.exe'
```

The current subscriber demo references the official light logo and isotope,
and the SVG/PNG/ICO favicons. Dark logo support is prepared as an asset; the
subscriber demo has no dark theme. Apple touch/PWA icons are not generated
because there is no installable-app manifest or consumer. No generic OG image,
public URL, social profile, structured data, or production identity is
invented; none has a current canonical consumer.
