# AXIGNAL Landing — Preview Asset Manifest V1

**Status:** CONFIRMED — STORYBOARD PREVIEW ONLY
**Runtime authority:** NONE
**Repository inclusion:** NO — preview binaries remain outside repository/runtime

## Canonical preview set

- Source masters: 15/15 SHA-256 verified before conversion.
- Source dimensions: 1920×1080 PNG.
- Source total bytes: 45,988,828.
- Tool: ffmpeg version 9.0-full_build-www.gyan.dev Copyright (c) 2000-2026 the FFmpeg developers
- Encoder: `libwebp`.
- Preset: `picture`.
- Quality: `88`.
- Compression level: `6`.
- Base output dimensions: 1920×1080.
- Canonical base preview count: 15/15.
- Canonical base WebP total bytes: 5418926.
- Byte reduction vs source masters: 88.22%.
- SSIM minimum: 0.98252.
- SSIM average: 0.984754.

These settings are evidence for storyboard review only. They do not freeze production encoding settings.

## Canonical base files

| # | Preview file | Bytes | SHA-256 | SSIM |
|---:|---|---:|---|---:|
| 01 | `landing-01-outside.webp` | 519776 | `10E40522CA773E104374CCF0C885241E61C8B89F885411BA82B64D37AB9EFE71` | 0.984293 |
| 02 | `landing-02-observe.webp` | 366666 | `ABCAA7BCE7A6AB1690ACDA401763E25EC47572EFE633B95C983679DDFE64020C` | 0.983978 |
| 03 | `landing-03-understand.webp` | 354100 | `41DF3D8AACAD0012D5C775688390DC39684D6E3E43CF55DB08121791ACA9B4E0` | 0.983723 |
| 04 | `landing-04-axigland.webp` | 374212 | `931520E561F9C3800E85F32B9B61312AD9C662BA94E29168A73713FF30613A23` | 0.984678 |
| 05 | `landing-05-xignal.webp` | 380454 | `621584F85C588393202B0CD4C856C3E2150ABE9EEF3136C7CCA023C2A24039B9` | 0.984088 |
| 06 | `landing-06-first-map.webp` | 447572 | `4CED10A93B158214627719BED3EF575F5C206BA10C2DA6F53E5F4B6DBE9BF3B1` | 0.983214 |
| 07 | `landing-07-evidence.webp` | 257626 | `2B087FA321DF29D9CDBAD61526C047F999459A5A37C0A8D3FB8D9C9B07A4A8F5` | 0.986036 |
| 08 | `landing-08-discover.webp` | 426950 | `21E118EF8961A00A330FB830A6761503A9098319237F3136C66877BFDCD142EC` | 0.982593 |
| 09 | `landing-09-digital-representation.webp` | 268434 | `7B0B92B04FB67F1979E36F2771255A4D2BF6525F12CDE632E18A1EBE6FDDC044` | 0.987598 |
| 10 | `landing-10-time.webp` | 522032 | `E7E9FE2A8DF3FFAF6C56D7D1F46F1E46C3118465D3925F7270EF80A1DDDE684A` | 0.98252 |
| 11 | `landing-11-axent.webp` | 267756 | `35AE2D0F5C46A606F6B6AAD3024C52B62123D55D43EA0A0D2A52252253535279` | 0.986693 |
| 12 | `landing-12-independence.webp` | 320888 | `7288060DD983DC8ACF9953341C0D009849FA41816F17D0322A0A7A23D70DFD03` | 0.985956 |
| 13 | `landing-13-use-cases.webp` | 304482 | `EF0F9A2D6B03F74D7DBE8350629F2D2B3870B1754C0E035DCF78075352A9E751` | 0.985299 |
| 14 | `landing-14-pricing.webp` | 297328 | `9F5D646D9BA577D7939C96A14F565B199E70103C9C9D270BC653F23F045D17CD` | 0.986032 |
| 15 | `landing-15-start.webp` | 310650 | `0BDF2F8688328FA42ABFCC5022E87002F2D373F9A539F06E2E930833FE15F27F` | 0.984612 |

## Responsive review derivatives

Chapter 12 requires portrait compositions to preserve the investigator/payment relationship while reserving lower mobile/tablet space for copy. These two derivatives are explicit storyboard-review assets, not extra chapters and not production authority.

| Purpose | File | Dimensions | Bytes | SHA-256 | Deterministic source transform |
|---|---|---|---:|---|---|
| Chapter 12 tablet | `landing-12-independence-tablet.webp` | 768x1024 | 149234 | `83461CD671C0DC1B50E73165F5A3352B06DBD59E890898B9DBA7DF532C8613BD` | `crop=1080:1080:560:0, scale=768:768 lanczos, pad=768:1024 top-aligned black; libwebp picture q88 level6` |
| Chapter 12 mobile | `landing-12-independence-mobile.webp` | 390x844 | 64124 | `287D1CB44CF09DB15B639ED6E4145BCA276879B2AFDBA494D8614E1034F30061` | `crop=810:1080:700:0, scale=390:520 lanczos, pad=390:844 top-aligned black; libwebp picture q88 level6` |

- Actual external review directory WebP count: 17 = 15 canonical base + 2 governed responsive Chapter 12 derivatives.
- Actual external review directory WebP bytes: 5632284.

## Guardrails

- Preview derivatives are disposable review evidence, not product runtime assets.
- Source masters remain untouched outside the repository.
- Production WebP generation must rerun from verified source masters after STORYBOARD_FREEZE.
- Responsive production derivatives, if still required after implementation QA, must be regenerated through the governed production pipeline rather than copied blindly from preview.
- AVIF remains optional and evidence-gated.
- No preview hash or encoding setting may silently become production authority.
