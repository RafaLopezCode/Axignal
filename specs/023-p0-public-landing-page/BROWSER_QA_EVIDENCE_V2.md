# AXIGNAL Landing — Browser QA Evidence Manifest V2

**Status:** CURRENT
**Supersedes:** `BROWSER_QA_EVIDENCE_V1.md` for rendered-storyboard hash provenance
**Phase:** RENDERED STORYBOARD REVIEW
**Runtime:** disposable external review harness; no product runtime implementation
**Rendered specification HEAD:** `83d2868ff4929e1e6d1ab4dfbe54dade6da6d01b`
**Browser tool:** Playwright 1.55.0 using installed Chrome `153.0.8010.53`
**Evidence root (machine-local):** `D:\AXIGNAL\_source_assets\landing\storyboard-review-v1\`

## Summary

- Exact viewport emulation: Playwright browser contexts.
- Locales rendered: `es`, `en`.
- Captures: 90/90 = 15 chapters × desktop/tablet/mobile × EN/ES.
- Layout/console automated failures: 0.
- Horizontal document overflow: 0/90.
- Copy box outside viewport: 0/90.
- Page console errors: 0/90.
- Chapter 12 tablet/mobile uses explicitly governed responsive review derivatives documented in `PREVIEW_ASSET_MANIFEST_V1.md`.
- Chapter 13 mobile keeps the normal mobile body scale and separates the agency proposition into a second paragraph without deleting qualifiers.
- Mobile exposes AXIGNAL, compact `+ Xignal`, locale selector, and an actionable chapter indicator; no 15-dot rail is exposed.

## Evidence

| Viewport | Locale | Chapter | Screenshot | SHA-256 | Copy fits | Console errors | Art source |
|---|---|---:|---|---|---|---:|---|
| desktop | es | 01 | `screenshots/desktop/01-es.png` | `6015E3A6BCA52C8A2A439111C20E04FEDCDA9C675D7C613D2748B9EEF57A0190` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-01-outside.webp")` |
| desktop | es | 02 | `screenshots/desktop/02-es.png` | `0A5CC9B378F358A3662AE3A5BA0A8E1A93091ED8169AEF235EADDCE432913422` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-02-observe.webp")` |
| desktop | es | 03 | `screenshots/desktop/03-es.png` | `52BC604817A3D585DA66EEB264D39DF805F3ECF32AF9F0F19FA70BA6CC17BF71` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-03-understand.webp")` |
| desktop | es | 04 | `screenshots/desktop/04-es.png` | `31CE2EDD3C85E102AD290961F2B3F1BE864DD62C1A8D9BF640B2B46E4D3CC7AD` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-04-axigland.webp")` |
| desktop | es | 05 | `screenshots/desktop/05-es.png` | `377B26985687E90C9BFDB0676A9D1F9E4E155D9EB0396EB41C3EBC62E1DE09CF` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-05-xignal.webp")` |
| desktop | es | 06 | `screenshots/desktop/06-es.png` | `CB478ADF763A9D833FCBAA14D5787410C595E9052DA0F5C2A4D21720F92DCB98` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-06-first-map.webp")` |
| desktop | es | 07 | `screenshots/desktop/07-es.png` | `C271D735BD445598A9F40B362252B245A46CC9EB6B475A38177C6F3C5056FC4B` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-07-evidence.webp")` |
| desktop | es | 08 | `screenshots/desktop/08-es.png` | `83D5BF97AC9FB6E31F9BEEA2A75AB9CD86D24996300387AC5C3A4AD4F4BCF22B` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-08-discover.webp")` |
| desktop | es | 09 | `screenshots/desktop/09-es.png` | `BC75F33AB2B0736F9DBD48F0D54DF6F753DA904AE393A7131D658E2BBFFCA49C` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-09-digital-representation.webp")` |
| desktop | es | 10 | `screenshots/desktop/10-es.png` | `5013E0C0AB8148173A5CE288E9D148E4644E4DE6D0B0E973E817E68D0031399E` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-10-time.webp")` |
| desktop | es | 11 | `screenshots/desktop/11-es.png` | `C6E646BE182CDDA1EE3DF017FDECB5B57C9849A5DB69C745D170DBFC69EE5932` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-11-axent.webp")` |
| desktop | es | 12 | `screenshots/desktop/12-es.png` | `7D3468BD6ED2C200605A8E1FB651632E56B8C017F8DE5CBB8925CACFE18BD587` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-12-independence.webp")` |
| desktop | es | 13 | `screenshots/desktop/13-es.png` | `A37A915D9964F5BBDF235E00C1EE2A5742E01797029B0DD55CEDA5470AC43167` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-13-use-cases.webp")` |
| desktop | es | 14 | `screenshots/desktop/14-es.png` | `D47624C2FBAD723074C63512BAFAB2206E10E3EAB971FCA8AC6A9CB769050F77` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-14-pricing.webp")` |
| desktop | es | 15 | `screenshots/desktop/15-es.png` | `8132ED792EFEF3DFA03FAE9A9BD5E39DE8C51F7D994BCBE3C34793F105C96C02` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-15-start.webp")` |
| desktop | en | 01 | `screenshots/desktop/01-en.png` | `59BBB6C3FDF46B47E0A5267309A7748175AC3CE44AC2FC0CE5B862AFBC3BF718` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-01-outside.webp")` |
| desktop | en | 02 | `screenshots/desktop/02-en.png` | `81EA2F40A77525584009318BF2B288B2D94C3A8C236CF41F671BCB6306D05A5D` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-02-observe.webp")` |
| desktop | en | 03 | `screenshots/desktop/03-en.png` | `BE4F03E7FC054D6C250AABF0BB86BC3ACD7C415A30254EF42DE866C4C85897AF` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-03-understand.webp")` |
| desktop | en | 04 | `screenshots/desktop/04-en.png` | `E70CED0F9ED540E7D6ACF805F601C21DD8675E9E4D0CFD49FF6E6846588784FF` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-04-axigland.webp")` |
| desktop | en | 05 | `screenshots/desktop/05-en.png` | `7E49D55487F007EC2D2044F15C94582B3562BFFBA0C0CF66A9981825F373D37F` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-05-xignal.webp")` |
| desktop | en | 06 | `screenshots/desktop/06-en.png` | `F5AC8218D493AB2783A83701C9B109C104285B99CA553B1A060EF7C53038A2C5` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-06-first-map.webp")` |
| desktop | en | 07 | `screenshots/desktop/07-en.png` | `85888B031ED4D5A70BA9F37FC5953E7B1C68C7A8EA4FB79CCCC14ABEF228423F` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-07-evidence.webp")` |
| desktop | en | 08 | `screenshots/desktop/08-en.png` | `2971452C9FA8E3FC9B7ADA1CE481FCA713FC8077B96E1222DDC882EC308D21E9` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-08-discover.webp")` |
| desktop | en | 09 | `screenshots/desktop/09-en.png` | `3628E3ED92DFFAB6FEA86A3733B0DAFDCE04CEEBB11984CA8DC12D4F3399297C` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-09-digital-representation.webp")` |
| desktop | en | 10 | `screenshots/desktop/10-en.png` | `39D5FE851CB16D0F0C2A86638E3E941B09A024C7209C49870C0C3B865203378A` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-10-time.webp")` |
| desktop | en | 11 | `screenshots/desktop/11-en.png` | `4891473F37B0964A0A64336E62A8E9CCD7E92FB5F51C21E29C3009A640FA1381` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-11-axent.webp")` |
| desktop | en | 12 | `screenshots/desktop/12-en.png` | `B65497DE279756890965A677375FB8651FCF253DBBAE62EFA29204BCA6591427` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-12-independence.webp")` |
| desktop | en | 13 | `screenshots/desktop/13-en.png` | `11E7D72F2F86E7B03A7FC302C4A118E9559421C76EAC72396DA703991C00A7E3` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-13-use-cases.webp")` |
| desktop | en | 14 | `screenshots/desktop/14-en.png` | `C2DDE5C0C671BBAE601D82A904C190FD221DD0AA7D38D58A1E24EDD2C8A9B52D` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-14-pricing.webp")` |
| desktop | en | 15 | `screenshots/desktop/15-en.png` | `FFC896B5F577ED3E35D39D5C399E627D2E62C5AC8097F921C91720680E7F255F` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-15-start.webp")` |
| tablet | es | 01 | `screenshots/tablet/01-es.png` | `412CAA97443E579F214ADB24516472BC09C20C80B095BEEABAAEEC64AB55F2EF` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-01-outside.webp")` |
| tablet | es | 02 | `screenshots/tablet/02-es.png` | `6757490C244B1FD14567E7B6692B5102D705F61EDD07DB5406D6025544E1B548` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-02-observe.webp")` |
| tablet | es | 03 | `screenshots/tablet/03-es.png` | `5D7BEF2EE90CE9346DD70B126275E1154D6234A6AC399AF1A57B5CBF682851A9` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-03-understand.webp")` |
| tablet | es | 04 | `screenshots/tablet/04-es.png` | `E70A1E64D2A6FEB1990FAC24AF2913949413CC43FF55B80CCDAEB566F1C12E1C` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-04-axigland.webp")` |
| tablet | es | 05 | `screenshots/tablet/05-es.png` | `709BB424D0355032DCEAF37671C810B496D994841CC52A43574330DAA39D9842` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-05-xignal.webp")` |
| tablet | es | 06 | `screenshots/tablet/06-es.png` | `3274C5CC0A264AAB2AB08FD966F6D8C956F18726961D05D73E9C862D66C70F97` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-06-first-map.webp")` |
| tablet | es | 07 | `screenshots/tablet/07-es.png` | `76DFB74C7036775E7BF7E5B893FCBE9F895A2CEB84CE2123031CD073E68327D0` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-07-evidence.webp")` |
| tablet | es | 08 | `screenshots/tablet/08-es.png` | `FECCCAFC2ACFBE6301309D2B5531C311C7C6FACE1600FA1B500AE98288BE483A` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-08-discover.webp")` |
| tablet | es | 09 | `screenshots/tablet/09-es.png` | `1BD42E8E40E3830D86D960691420F51EFC264D5CA02D715A14C99D8C6DF74958` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-09-digital-representation.webp")` |
| tablet | es | 10 | `screenshots/tablet/10-es.png` | `1E066621681BDBE2939423F92CCAC9E45E780B6747E68CEA909571E418017891` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-10-time.webp")` |
| tablet | es | 11 | `screenshots/tablet/11-es.png` | `F1A6942D1DD693D1FC6C91474AD93D9BFFBF949F0843C06E2BF24A0C1605106C` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-11-axent.webp")` |
| tablet | es | 12 | `screenshots/tablet/12-es.png` | `3C5B8DAFEC48BEDABAF2E4A2002D9D63E369EBD2A953083E29CDBFC842E9BB4C` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-12-independence-tablet.webp")` |
| tablet | es | 13 | `screenshots/tablet/13-es.png` | `52A6B8C97413B3DBD37689E5DEA61C583A2437208A50E2BE690918DAD2324069` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-13-use-cases.webp")` |
| tablet | es | 14 | `screenshots/tablet/14-es.png` | `685694038370A3613EC8A68F120BA7940ED49AB9053BCF620E24142580034D01` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-14-pricing.webp")` |
| tablet | es | 15 | `screenshots/tablet/15-es.png` | `6F0A148CCFEE9440F5B1BD78CD42748218154AD787E8EB75BC1676AF533C6099` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-15-start.webp")` |
| tablet | en | 01 | `screenshots/tablet/01-en.png` | `65737B16101D969BFB29D5E1851001D0CCDB6D6479F08A7901A47FE50004205C` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-01-outside.webp")` |
| tablet | en | 02 | `screenshots/tablet/02-en.png` | `6C1ACE59BE3D917C347036DCE0789C337AEB4F593156D91F4DF2635ADBFA2768` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-02-observe.webp")` |
| tablet | en | 03 | `screenshots/tablet/03-en.png` | `30FA0853DE2829C65A108B5E4B07B8D726AC81B51AB7A965877AB4ABE4EE3524` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-03-understand.webp")` |
| tablet | en | 04 | `screenshots/tablet/04-en.png` | `14490231D842774D5FE26F57D077D09AFB026ECF3D8418B1B9BB1F5DB39B60F0` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-04-axigland.webp")` |
| tablet | en | 05 | `screenshots/tablet/05-en.png` | `6007C859DB08B6E1D81342122DFBAFB6C07AC68184AD9364D62E78C2F90A245D` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-05-xignal.webp")` |
| tablet | en | 06 | `screenshots/tablet/06-en.png` | `401F715689AE8BCBB5AEDC0D62F432202F6F2A8EEABCC0C6A4E0C622CBA75BD1` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-06-first-map.webp")` |
| tablet | en | 07 | `screenshots/tablet/07-en.png` | `33624183D1DCA7D4397661EA79B251E4C046B2E2402CCDF02FC574432B35CC91` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-07-evidence.webp")` |
| tablet | en | 08 | `screenshots/tablet/08-en.png` | `1C77230F35F23DB3D7142FDCF029A9CBEBFDC9C92AC7808E8B7E9E73793CE97B` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-08-discover.webp")` |
| tablet | en | 09 | `screenshots/tablet/09-en.png` | `21039F69BCD3A9C5C6ECAE114B84FA7142F7C9421D711D3A8AC8AC486AE82053` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-09-digital-representation.webp")` |
| tablet | en | 10 | `screenshots/tablet/10-en.png` | `A7DB3534640500FE26EFA423272AE7B3646D34875083696DFAC09B6067063639` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-10-time.webp")` |
| tablet | en | 11 | `screenshots/tablet/11-en.png` | `B03D8982EE9FD187845819893845BD4CC244E0E354B3CF84925678D367FBC529` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-11-axent.webp")` |
| tablet | en | 12 | `screenshots/tablet/12-en.png` | `1311909D1B0DAF3DE4BA628E1644A90D02FDD99CB958F3CC5B1A0D65914AB79F` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-12-independence-tablet.webp")` |
| tablet | en | 13 | `screenshots/tablet/13-en.png` | `1F153084549508B02F3D0F700ED1911E6BC7C9BE02697C10E2FB32F900D72F0A` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-13-use-cases.webp")` |
| tablet | en | 14 | `screenshots/tablet/14-en.png` | `602A9B9FC2D88BBB170630CAF99C4600E6822838870006381B534623CFB74B98` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-14-pricing.webp")` |
| tablet | en | 15 | `screenshots/tablet/15-en.png` | `BF26572C1C636ECA920656C4447771AA5BA54B0F2ECD2DEFCB2DD14103347975` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-15-start.webp")` |
| mobile | es | 01 | `screenshots/mobile/01-es.png` | `D5FAC8F0390C229076069ED9994B53B6D6AED86D8EFD59B9108B989AD21FB776` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-01-outside.webp")` |
| mobile | es | 02 | `screenshots/mobile/02-es.png` | `70DFDC1C1BCF04243366B09917F3A2B87BB95C9B20B4ED32447AB5420F654DDA` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-02-observe.webp")` |
| mobile | es | 03 | `screenshots/mobile/03-es.png` | `E8FD396E037E4E19C791D6E727D9BAB82A24F60F5AC74223482596E109C841D9` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-03-understand.webp")` |
| mobile | es | 04 | `screenshots/mobile/04-es.png` | `1DBF7CD1891CE491A883F4BEEEE03027779A0785F6F6341D2EDA7ECD00B52A48` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-04-axigland.webp")` |
| mobile | es | 05 | `screenshots/mobile/05-es.png` | `174789995C662126BAB84132E9B3025E0ACCF03F7424133EADF85B1C7EE42E8D` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-05-xignal.webp")` |
| mobile | es | 06 | `screenshots/mobile/06-es.png` | `9E41212DE1C3A23B4597DC481C985BFB21D8EF2B2F6A5CF85BADC7277F958051` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-06-first-map.webp")` |
| mobile | es | 07 | `screenshots/mobile/07-es.png` | `239629222E2867AA8290F5174A4154317AAC3781E4B2D3EE1C56F9B71A771F75` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-07-evidence.webp")` |
| mobile | es | 08 | `screenshots/mobile/08-es.png` | `2300582C4D632F66D80A550C99B46B3A5ADF164FFC6722237C54051CF7F19B3E` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-08-discover.webp")` |
| mobile | es | 09 | `screenshots/mobile/09-es.png` | `48362A199175DCDF856D8C92E83BDA749C7967A63C94DD0E98EC280193B4515A` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-09-digital-representation.webp")` |
| mobile | es | 10 | `screenshots/mobile/10-es.png` | `017EE4433774D498421F0D63DB85124C7FC0AC314AA472E62D991E7808BF8553` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-10-time.webp")` |
| mobile | es | 11 | `screenshots/mobile/11-es.png` | `9EE1FD2724AAA4C4035AFF4FDC2641FADF3F9CF39C3021731AA2372303535F68` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-11-axent.webp")` |
| mobile | es | 12 | `screenshots/mobile/12-es.png` | `EFA1B441C9C1A07D1DC7F4EB06271B225E7B75A49E3314D192F0689D44202F3A` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-12-independence-mobile.webp")` |
| mobile | es | 13 | `screenshots/mobile/13-es.png` | `0FBB2C3967D4B21F5D87626F9A97408616915422CB78F17A0CAC227A27828C1B` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-13-use-cases.webp")` |
| mobile | es | 14 | `screenshots/mobile/14-es.png` | `9F0DA1ED41B60F10901F237697E6B13A4816E7A0126FDD241A5F145C90D5AD70` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-14-pricing.webp")` |
| mobile | es | 15 | `screenshots/mobile/15-es.png` | `81D7E3DA13462262003295AE5E269C62A387862BCB874D721C8B14A89021FCF0` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-15-start.webp")` |
| mobile | en | 01 | `screenshots/mobile/01-en.png` | `4E12E0BC73905386B797136517071D56A6EBFA9DE2701128D59C47B7B44EA6BB` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-01-outside.webp")` |
| mobile | en | 02 | `screenshots/mobile/02-en.png` | `9FBD56F765C515CEA29974E454BF878D69E2FFCDA58DA35D8C8ABE6AA91295EC` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-02-observe.webp")` |
| mobile | en | 03 | `screenshots/mobile/03-en.png` | `ECAA4F540B1E6B788275220488807D0AF13FC3039177DC2E0292C1F0634A33E5` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-03-understand.webp")` |
| mobile | en | 04 | `screenshots/mobile/04-en.png` | `5593CF8DEF96D52C9F88FC47F82AACC28CDF1A6E35B3844AA88023FC30B489D8` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-04-axigland.webp")` |
| mobile | en | 05 | `screenshots/mobile/05-en.png` | `C0E13A50248F29DA9EC75AAB35AB33E4D9D99AD0AAE655D1229DC4641D0511A7` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-05-xignal.webp")` |
| mobile | en | 06 | `screenshots/mobile/06-en.png` | `372D709943B68786F525B99C428B534613F43D8E0E6C2671B25477BAA1E42706` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-06-first-map.webp")` |
| mobile | en | 07 | `screenshots/mobile/07-en.png` | `2ADBED8E4A5A92C39E13DDA2DD491776E7B12663C69A60B3381418EA119FD3DA` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-07-evidence.webp")` |
| mobile | en | 08 | `screenshots/mobile/08-en.png` | `89EF057FDFBCF4EF6069684EB424347AB76A2413957340D184C45746643B3A3F` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-08-discover.webp")` |
| mobile | en | 09 | `screenshots/mobile/09-en.png` | `4B367C860B2F50B79732D9B55890497AF4AF6C70BE43E8C0F5823BD8A862AA42` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-09-digital-representation.webp")` |
| mobile | en | 10 | `screenshots/mobile/10-en.png` | `DEEAA2EF1B14BEA9B4B22153B915D577CFA2352967DF9296FED5E928AA363E4A` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-10-time.webp")` |
| mobile | en | 11 | `screenshots/mobile/11-en.png` | `93087B6A3B45E7B2D864F6F8D1FF37F43824A71EA1891FCA968F927013737BD2` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-11-axent.webp")` |
| mobile | en | 12 | `screenshots/mobile/12-en.png` | `E202D906ED2DA146A7837A8BC5FA7808CF61A924B87319D29FDC055D19FC112F` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-12-independence-mobile.webp")` |
| mobile | en | 13 | `screenshots/mobile/13-en.png` | `B30994EDE5EB288D3EABFFE5372D3B2BBE672A5F1DE9804469EB16D9DF289B58` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-13-use-cases.webp")` |
| mobile | en | 14 | `screenshots/mobile/14-en.png` | `6825A56A20E4D9EAB5B4F93A0C4C4DA7CA889070B63289B9ABE19767FE930B2E` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-14-pricing.webp")` |
| mobile | en | 15 | `screenshots/mobile/15-en.png` | `018509169F03AC1282689728337AB05AFAB7376794B4B1138A488DC02354EDB4` | PASS | 0 | `url("file:///D:/AXIGNAL/_source_assets/landing/storyboard-review-v1/assets/landing-15-start.webp")` |

## Contact sheets
- `contact-sheet-desktop-es.jpg` — SHA-256 `4BDBF142E02435CF5019C0621C13D653BC23DEF339D44582FA4B436F99EC1440`.
- `contact-sheet-tablet-es.jpg` — SHA-256 `158B98CC277BF09D1C1ACB0EAEB43CA7BBBDDFC89C68326C10EB1622806E9632`.
- `contact-sheet-mobile-es.jpg` — SHA-256 `50E4AEE11B1FAC72855CFFBA66045E400DF67D4ECC5DF37C5D51327B4BB76F17`.
- `contact-sheet-desktop-en.jpg` — SHA-256 `D83C1C432DCFFC73DDB244BABFDFB840A387D727F5E064E51CEB688E90106592`.
- `contact-sheet-tablet-en.jpg` — SHA-256 `9169AD17A0300505CA33B22324E3AB3DF622DEE3FD4C3A9BA04EEF2D86949041`.
- `contact-sheet-mobile-en.jpg` — SHA-256 `9843B1C18D7798EC1851E9EDF71E88344A0C3ECB6BC7F66344548A5806247B73`.

## Integrity rule

The screenshot hashes above were calculated after the final 90-capture rerun that produced the referenced `render-evidence.json`. A review claiming visual-evidence integrity MUST recompute the hashes of these exact files and compare them to this table.

## Current disposition

`CTO_RENDERED_STORYBOARD_REVIEW=PASS_BASE_90_EN_ES`

`HUMAN_STORYBOARD_ACCEPTANCE=PENDING`

`STORYBOARD_FREEZE=PENDING`

This evidence proves the preproduction composition review only. It does not prove production runtime interaction, fr/de/it/pt localization, final asset loading/performance or deployment.

## Implementation QA template

A later runtime PASS must record the tested implementation HEAD, all required breakpoints/locales, interaction state, screenshot/recording reference, console/network evidence, defect/repair linkage and verdict. Unsupported PASS declarations remain invalid.
