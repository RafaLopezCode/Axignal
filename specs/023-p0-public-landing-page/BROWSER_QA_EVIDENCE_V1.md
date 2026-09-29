# AXIGNAL Landing — Browser QA Evidence Manifest V1

**Phase:** RENDERED STORYBOARD REVIEW
**Runtime:** disposable external review harness; no product runtime implementation
**HEAD SHA:** `
e622b58ae9ec27fd84314434eba3defa7b0241ce
`
**Browser tool:** Playwright 1.55.0 using installed Chrome `
153.0.8010.53
`
**Evidence root (machine-local):** `D:\AXIGNAL\_source_assets\landing\storyboard-review-v1\`

## Summary

- Exact viewport emulation: Playwright browser contexts; no CLI minimum-window approximation.
- Locales rendered: `es`, `en`.
- Captures: 90/90 = 15 chapters × desktop/tablet/mobile × EN/ES.
- Layout/console automated failures: 0.
- Horizontal document overflow: 0/90.
- Copy box outside viewport: 0/90.
- Page console errors: 0/90.
- Initial visual defect found and repaired: mobile header omitted the required compact `+ Xignal` action and exposed a 15-dot rail; review harness was repaired to show `+ Xignal`, keep the locale selector and use the compact chapter counter on mobile.
- Chapters 08, 09, 12, 13 and 15 received explicit focal/copy review after the independent-review findings.
- EN and ES were both visually checked after COPY_FREEZE.

## Evidence

| Viewport | Locale | Chapter | Screenshot | SHA-256 | Copy fits | Console errors | Focal position |
|---|---|---:|---|---|---|---:|---|
| desktop | es | 01 | `screenshots/desktop/01-es.png` | `EC8DDE46F5A5656D51D255722DE5A8A3A953C7D66743D80BFFE95B28BA00113E` | PASS | 0 | `68% 50%` |
| desktop | es | 02 | `screenshots/desktop/02-es.png` | `B4AC82C236CC5CB37BF1AC19329BD661CBC2C77BE5AF83F7236278DD05007578` | PASS | 0 | `69% 50%` |
| desktop | es | 03 | `screenshots/desktop/03-es.png` | `E4F142DD82543A703381E090288B6B4CA1D44D76F1964A5B0D33D8CB5282E9A3` | PASS | 0 | `66% 50%` |
| desktop | es | 04 | `screenshots/desktop/04-es.png` | `E42FE0143C3B739BF4F0A355A12BBA2C3692F731E8135948B474F057EC33040F` | PASS | 0 | `62% 50%` |
| desktop | es | 05 | `screenshots/desktop/05-es.png` | `10898EE3BF42A70EC2C14E8B1F28BE73D311F827DBD1986ECC91C1BED07C9309` | PASS | 0 | `70% 52%` |
| desktop | es | 06 | `screenshots/desktop/06-es.png` | `4B26FD63CFFEB7FBA49A1F6A3CBC06C76AB01587A101418EB8045C259B63BA75` | PASS | 0 | `68% 50%` |
| desktop | es | 07 | `screenshots/desktop/07-es.png` | `7BC3ECBB67ED394590CC352F8AA58134F9BDC426BB93AE9C4E4E73EDFEDF3D9D` | PASS | 0 | `69% 50%` |
| desktop | es | 08 | `screenshots/desktop/08-es.png` | `CB5FA641768496B6DD31E36D45C1453AD264BCD6DD9EFCCD814DE11E26764154` | PASS | 0 | `56% 48%` |
| desktop | es | 09 | `screenshots/desktop/09-es.png` | `623313FDD51555BE3A34BC7281E94658ACCD0029D51CE144E6D594D5D033C4A8` | PASS | 0 | `56% 50%` |
| desktop | es | 10 | `screenshots/desktop/10-es.png` | `8F078522693A5A0C2A9A80BA19B7887BD668AD837E4B2544034EEE69072E3EB2` | PASS | 0 | `62% 50%` |
| desktop | es | 11 | `screenshots/desktop/11-es.png` | `BBD1E9C589E0FE3F134D1B3E034B60223CA0205BA7AB9BF8FD00BF40F786CF8A` | PASS | 0 | `68% 50%` |
| desktop | es | 12 | `screenshots/desktop/12-es.png` | `4712AE2A9F326EE80D6DDB8BAF5CCB5C94121AB5D83A1A1A3C87255D3BC81051` | PASS | 0 | `54% 50%` |
| desktop | es | 13 | `screenshots/desktop/13-es.png` | `039E377CA5B13FBF08D15818DFAA84C7EEC65664AF986E9226FACCB0379FEE6A` | PASS | 0 | `63% 50%` |
| desktop | es | 14 | `screenshots/desktop/14-es.png` | `9E55B46E4857D5AC4AAEEFB3BC217BF38FB8414E907126577CC6D23F168911A7` | PASS | 0 | `68% 50%` |
| desktop | es | 15 | `screenshots/desktop/15-es.png` | `0D5B06E857B5D6BD254B8FAFB04CDA611E02B7EB251BF053CA6C3DD8856E807A` | PASS | 0 | `56% 50%` |
| desktop | en | 01 | `screenshots/desktop/01-en.png` | `B859F656080D6E46B9758A4DF34773F03C0DB47B83DE61BD08AF4A74B7FBDFF9` | PASS | 0 | `68% 50%` |
| desktop | en | 02 | `screenshots/desktop/02-en.png` | `365E935F3CE5862DFDC7538BE00EF618A599EC57CCCD45FCE1DAC4A4CBC5441B` | PASS | 0 | `69% 50%` |
| desktop | en | 03 | `screenshots/desktop/03-en.png` | `2680A0AD7B76EEAC6A1DDA1EA47A451CC2AF49A782502A70A60261FBED2FCA2D` | PASS | 0 | `66% 50%` |
| desktop | en | 04 | `screenshots/desktop/04-en.png` | `B22EB670E9ABB12FF4EE8C6DA937E8799E1E5454B89DB0C3A64F82880FB3F15E` | PASS | 0 | `62% 50%` |
| desktop | en | 05 | `screenshots/desktop/05-en.png` | `CE92B2DDA07D2E80E3866A33191DF62D8FB157253BFA9A74F0E5068990F660AE` | PASS | 0 | `70% 52%` |
| desktop | en | 06 | `screenshots/desktop/06-en.png` | `958A3B89E55930E5081C717B3975D03C7ADAB2A2E1A9FA135348AAD70951369B` | PASS | 0 | `68% 50%` |
| desktop | en | 07 | `screenshots/desktop/07-en.png` | `7A8DBD871883FC12976056C66233DB2825F36DCD941F8AC1B4470F23CB653B75` | PASS | 0 | `69% 50%` |
| desktop | en | 08 | `screenshots/desktop/08-en.png` | `05FC220E72C30489CBDE3F773A93424B5026A79193E6560982C1281FD82A834D` | PASS | 0 | `56% 48%` |
| desktop | en | 09 | `screenshots/desktop/09-en.png` | `F46FF99110F68C018570AB3EBFAD3A4B51C96CFBD2EBA8D49925B4250644F9FE` | PASS | 0 | `56% 50%` |
| desktop | en | 10 | `screenshots/desktop/10-en.png` | `C72C6D15F88F9DAEE179D33962262AF29DE3632343C17C77B79978C0D1A6DC7A` | PASS | 0 | `62% 50%` |
| desktop | en | 11 | `screenshots/desktop/11-en.png` | `CA69E19CC1EE08712E0D3C2E046422474E01F2A8CFBF557F162D304620AE3FED` | PASS | 0 | `68% 50%` |
| desktop | en | 12 | `screenshots/desktop/12-en.png` | `FB998641B1D448C07598945B4A2A65A3DF4AF43034D0E43615C33DCDA91F42AE` | PASS | 0 | `54% 50%` |
| desktop | en | 13 | `screenshots/desktop/13-en.png` | `64D3B838A7A5DD050B8208FEB4A47A3B952BE60E87F7225478B4A71CD5E7A6C3` | PASS | 0 | `63% 50%` |
| desktop | en | 14 | `screenshots/desktop/14-en.png` | `2151F6EBB69DE8B2329A0428ECE85C1A018AD03927E1F39EE508C3FB07D84FCE` | PASS | 0 | `68% 50%` |
| desktop | en | 15 | `screenshots/desktop/15-en.png` | `EB6FDA91DBC010162FEA10A5F93FC4B419A4FB7FAC0B8AE46BD212E0CDB072E4` | PASS | 0 | `56% 50%` |
| tablet | es | 01 | `screenshots/tablet/01-es.png` | `9C386EA606D0156B5A318DD194699B4B3C1F0B291541B206EEC01CB127299661` | PASS | 0 | `72% 50%` |
| tablet | es | 02 | `screenshots/tablet/02-es.png` | `F97B485A8C8E9DAF201E8B39439C704E8E173653F70FFA157E423D5ED3FBCA87` | PASS | 0 | `72% 50%` |
| tablet | es | 03 | `screenshots/tablet/03-es.png` | `960CE74841369553AA0F0A447D25D7BA4B58CA06722E04F9FE8CFDE5D46BDF51` | PASS | 0 | `69% 50%` |
| tablet | es | 04 | `screenshots/tablet/04-es.png` | `38BF434699C6879269B7CAB835D63EFDA7D118A731455F5CBE59F75FF5703A53` | PASS | 0 | `64% 50%` |
| tablet | es | 05 | `screenshots/tablet/05-es.png` | `2E894D4197E392EFEE1C85B5152BEBB2F70C1B4779C1AEC7D01909A80C9A6ED2` | PASS | 0 | `73% 52%` |
| tablet | es | 06 | `screenshots/tablet/06-es.png` | `553171A26A1C786B87D40E24A94E82D0351DA68D5AE292FD256C5A3DA1B5ACE6` | PASS | 0 | `71% 50%` |
| tablet | es | 07 | `screenshots/tablet/07-es.png` | `620B030098A17620922558EBD9D6124AA7AD1D3570677879B5A15D0156921B84` | PASS | 0 | `72% 50%` |
| tablet | es | 08 | `screenshots/tablet/08-es.png` | `1B3FCCADA11273E6D054DAEF74D336ACA18B13B5E8D99864E08E206EB23AFB29` | PASS | 0 | `58% 48%` |
| tablet | es | 09 | `screenshots/tablet/09-es.png` | `2561DCA43C24C1B2F98D66750E6B7150F1A0C2BEC2D87CD4C1D545711A8B5FA1` | PASS | 0 | `58% 50%` |
| tablet | es | 10 | `screenshots/tablet/10-es.png` | `7C78A011AE529C2D7413BD8F518BA97F28430BE4EA8F9D83AE2C70D35271E44D` | PASS | 0 | `65% 50%` |
| tablet | es | 11 | `screenshots/tablet/11-es.png` | `64347DAC0EFC4BFB7106E49CAB10287930DEA23BC78F9496F48D6E53CDD8474B` | PASS | 0 | `71% 50%` |
| tablet | es | 12 | `screenshots/tablet/12-es.png` | `A020F57D8AC534958B4159D434EBBFBC6C96CC36E3AAC0E29F2FA48A4ED16E2A` | PASS | 0 | `56% 50%` |
| tablet | es | 13 | `screenshots/tablet/13-es.png` | `C6B0D122FFCE9DE911C2326CBD59FE0175EB998FC420D541439F917A8D192D7C` | PASS | 0 | `66% 50%` |
| tablet | es | 14 | `screenshots/tablet/14-es.png` | `41C908A61963237B0ABBE0B1C9B5C882879B6BFE0231CB69A34438C4CC74F1E5` | PASS | 0 | `70% 50%` |
| tablet | es | 15 | `screenshots/tablet/15-es.png` | `9B84BD365B0C28EC44AD83F008299064B80296F54B85946E71814C0A423EBB71` | PASS | 0 | `58% 50%` |
| tablet | en | 01 | `screenshots/tablet/01-en.png` | `CCA88ACE5B1D5C960275EF9F2DE7856652FAA9AE327FE513174A6B4F54E77159` | PASS | 0 | `72% 50%` |
| tablet | en | 02 | `screenshots/tablet/02-en.png` | `4CC399F0D6CB96EE973CAEE60720D3A4A985CFCDC5F511E2E7CE89BDC8573A93` | PASS | 0 | `72% 50%` |
| tablet | en | 03 | `screenshots/tablet/03-en.png` | `003D0C5EDE9F47C6714614E3C38C3E7D29AB7FE0B31A666AD16CBC003A422D6D` | PASS | 0 | `69% 50%` |
| tablet | en | 04 | `screenshots/tablet/04-en.png` | `AE718707DFA03431966F13B6764C5BEBE44E3982EF0FB43C3D5581AF58CF190A` | PASS | 0 | `64% 50%` |
| tablet | en | 05 | `screenshots/tablet/05-en.png` | `04B4D6B9798A6316468EF06967C68193D73D76392A377A9A9CA28330A345F436` | PASS | 0 | `73% 52%` |
| tablet | en | 06 | `screenshots/tablet/06-en.png` | `FA558D9571E497C2D782D4906829B3A7ECD21EBD19B3C5E3244E7C145C06FD90` | PASS | 0 | `71% 50%` |
| tablet | en | 07 | `screenshots/tablet/07-en.png` | `1661E386C63493EB49ED2F150022E271664E6880A4FAA225A54910EB68B13252` | PASS | 0 | `72% 50%` |
| tablet | en | 08 | `screenshots/tablet/08-en.png` | `36E6A1F587EB3E089DC3299B804DD1BBFC75919A6BDF49091740BAF9EF8BEDAC` | PASS | 0 | `58% 48%` |
| tablet | en | 09 | `screenshots/tablet/09-en.png` | `A864116527CAD314292ABBC776BB71C75D5FBC8AC63DEBDB4704B719DD69CAEB` | PASS | 0 | `58% 50%` |
| tablet | en | 10 | `screenshots/tablet/10-en.png` | `7841A4454EA3F80B6E6B4A4690353609FFD9691F6331C293AB17FEF5A3DD992E` | PASS | 0 | `65% 50%` |
| tablet | en | 11 | `screenshots/tablet/11-en.png` | `44E3886C95AD01CEF99B682F6CAB71CC12EC06E3FD5E5EB174DBA1A5D8D7F5EF` | PASS | 0 | `71% 50%` |
| tablet | en | 12 | `screenshots/tablet/12-en.png` | `0F062EC5C58590719CAB52063482E7BF9F925A95DB3E4D7F06D91ABD2E421B14` | PASS | 0 | `56% 50%` |
| tablet | en | 13 | `screenshots/tablet/13-en.png` | `040487FFB95B8CAAB3F0F24FE3A35DEF83BEA35C71EA99798C328A5DC8B8EE44` | PASS | 0 | `66% 50%` |
| tablet | en | 14 | `screenshots/tablet/14-en.png` | `A902D25D192F4461E40764407B5689442D471DABD360A00918C731935093B68E` | PASS | 0 | `70% 50%` |
| tablet | en | 15 | `screenshots/tablet/15-en.png` | `4A5593FB7E190091DC2F1BFE83EEEAB3CFA9C465212683E0267B458CFA764352` | PASS | 0 | `58% 50%` |
| mobile | es | 01 | `screenshots/mobile/01-es.png` | `DD30312854BFA3479CAB554CCFDFBA4EA767D3824A5B9BF19219A9648C037A13` | PASS | 0 | `76% 48%` |
| mobile | es | 02 | `screenshots/mobile/02-es.png` | `77C801FE2E47944848BA37218106A79DF7C6CB508BD22868D6B2C51CA87B8703` | PASS | 0 | `76% 50%` |
| mobile | es | 03 | `screenshots/mobile/03-es.png` | `011A50CCFA3F4C10E799BD2E849E8BB481F87041C27359407AB0176F321E331E` | PASS | 0 | `73% 50%` |
| mobile | es | 04 | `screenshots/mobile/04-es.png` | `81D5004E4CA401122F0A844FDFEDD1A50B6D39EF54B7F2C58E04313A2E04DAAA` | PASS | 0 | `68% 50%` |
| mobile | es | 05 | `screenshots/mobile/05-es.png` | `7DE21141636AB7AAF3501ECCB591C63D948A7A4A92EF8A22021F5C2858C026E1` | PASS | 0 | `76% 54%` |
| mobile | es | 06 | `screenshots/mobile/06-es.png` | `F8D930354F236DA4D2C838072004B427E2BA2D9331419C12C8758CB850DE45F4` | PASS | 0 | `74% 50%` |
| mobile | es | 07 | `screenshots/mobile/07-es.png` | `B85BCD9E6DDF01AF71F7275CA40161D81C86C913908F5D3CE3E7EEE74FE453FB` | PASS | 0 | `75% 50%` |
| mobile | es | 08 | `screenshots/mobile/08-es.png` | `E28E40E31B5A9CADBA5895593015BD8F19C4A40A93025671C44ED86FF968AE65` | PASS | 0 | `58% 48%` |
| mobile | es | 09 | `screenshots/mobile/09-es.png` | `B743BC3FE71D654D8EE188C087A2D096D365D84D9F1FBE5E113FBE39A831FAEA` | PASS | 0 | `58% 50%` |
| mobile | es | 10 | `screenshots/mobile/10-es.png` | `B5A01CAF9319BC9FC9AE387FBBD487969972081C44FE6A8541EB6F6075459ED3` | PASS | 0 | `68% 50%` |
| mobile | es | 11 | `screenshots/mobile/11-es.png` | `B74DAD2AFE73C28898EDC5A7114B037A0A0A9637B01BE0C9FCC74F9DE0544724` | PASS | 0 | `74% 50%` |
| mobile | es | 12 | `screenshots/mobile/12-es.png` | `BE4A2B1ED148231A4BC293895E44E7854A184A442A365E93B0CF3B2DE44DC1CC` | PASS | 0 | `56% 50%` |
| mobile | es | 13 | `screenshots/mobile/13-es.png` | `EAF6D89631B48BEBB6D47167302EEF706CD2B5AF27B4C161D5C06819A864C4D6` | PASS | 0 | `70% 50%` |
| mobile | es | 14 | `screenshots/mobile/14-es.png` | `F99CFE7A42B228208B22096A4922DB8848BAFFFD8A9627BF644712BAF207F05E` | PASS | 0 | `74% 50%` |
| mobile | es | 15 | `screenshots/mobile/15-es.png` | `8E88A15705A1975225558CB30FE3894F7D78E766F8F031083E25C1432F313560` | PASS | 0 | `58% 50%` |
| mobile | en | 01 | `screenshots/mobile/01-en.png` | `0F3D4AA96F97177BBA6FEB6FD3A591C673CAC0D1E66260856D5D44B1921A2211` | PASS | 0 | `76% 48%` |
| mobile | en | 02 | `screenshots/mobile/02-en.png` | `C123E024936DBF3BB65BE078162E02999AF7ABD88468B1F918CC44E27381663E` | PASS | 0 | `76% 50%` |
| mobile | en | 03 | `screenshots/mobile/03-en.png` | `9A0B5894759FA30BBB210CB54A92F43500AD4CD0E2A8E6760C12EACC45A11826` | PASS | 0 | `73% 50%` |
| mobile | en | 04 | `screenshots/mobile/04-en.png` | `4292B5383863D9ECCB39090AAA4F65B86C2AD4DDF301EFFE737C780299BC1234` | PASS | 0 | `68% 50%` |
| mobile | en | 05 | `screenshots/mobile/05-en.png` | `7B5B8F2313284E730A98C6C704598667BDD7884B2E8E15CA26E731E055B658EE` | PASS | 0 | `76% 54%` |
| mobile | en | 06 | `screenshots/mobile/06-en.png` | `DAB70D647494395B5C4EAD4EF09E4D2B2223451931A654BCCA776623FE33397E` | PASS | 0 | `74% 50%` |
| mobile | en | 07 | `screenshots/mobile/07-en.png` | `E7276C44F848E6B3F0D04C05F299BDAF65E568AF8B4937ABD4BDE518FB99D7CB` | PASS | 0 | `75% 50%` |
| mobile | en | 08 | `screenshots/mobile/08-en.png` | `E9C676A9485FBEEABCCD1CC6A031C8AAA426DBD2E74C7C6FFCE7272F49ED4B4A` | PASS | 0 | `58% 48%` |
| mobile | en | 09 | `screenshots/mobile/09-en.png` | `BF206019E31402A8287E2541AB8F64889C0A87CB7758A366DCFAF580B6EA87DB` | PASS | 0 | `58% 50%` |
| mobile | en | 10 | `screenshots/mobile/10-en.png` | `98BD4360552E3C21FE012DE04D0388B39C0541DB4444638B7812E4A96F924C92` | PASS | 0 | `68% 50%` |
| mobile | en | 11 | `screenshots/mobile/11-en.png` | `85B987466685AD6F8F5A72F935F2269CF628A793813D9D736E6523D57C3C71FC` | PASS | 0 | `74% 50%` |
| mobile | en | 12 | `screenshots/mobile/12-en.png` | `FE882645B6B5E14D9A8AFEB4D123BF5636696480D98DE9E26EA6DD5AC47E31B6` | PASS | 0 | `56% 50%` |
| mobile | en | 13 | `screenshots/mobile/13-en.png` | `07BB5D7976006BE9E9AA594848C4DC0FA54C2048D053A56C3A9BA7AA23D21490` | PASS | 0 | `70% 50%` |
| mobile | en | 14 | `screenshots/mobile/14-en.png` | `985888503248B9BA274FBC1DC8FF5B8AF7A3B531D56E78C08270C2178A496513` | PASS | 0 | `74% 50%` |
| mobile | en | 15 | `screenshots/mobile/15-en.png` | `D2720FF0118F78A0B38E7C6AAE5D2E0FF9D05B6DFF2821D819DDF9480DBD7198` | PASS | 0 | `58% 50%` |

## Contact sheets
- `contact-sheet-desktop-es.jpg` — SHA-256 `830AC56F24DABA5202637FE2164052C4BD20E4864F268FDC6045B8EFFE443A98`.
- `contact-sheet-tablet-es.jpg` — SHA-256 `020C70ECC5D78D52A6DBAE927F349CB5F72064AA97AF31232EFEC12991445BEA`.
- `contact-sheet-mobile-es.jpg` — SHA-256 `4CE3A6A0511BE644D4EADE980DEBE45DBC141C4940803839AC0DC4E4F55B053B`.
- `contact-sheet-desktop-en.jpg` — SHA-256 `B9F5539646D510FEC95BBF48E95FA8FAE22AF22026E3873E43D5E984C4F27D55`.
- `contact-sheet-tablet-en.jpg` — SHA-256 `5E354796B1601B4D755F8E05DA49B9E60856503F2C05E0F0058EF7F4534DAAE8`.
- `contact-sheet-mobile-en.jpg` — SHA-256 `512F92F55BF4C2DB3C6F1D15234DE9B0950CEFBD72AB702EFB8FEC50CB7114D3`.

## Current disposition

`CTO_RENDERED_STORYBOARD_REVIEW=PASS_BASE_90`

`HUMAN_STORYBOARD_ACCEPTANCE=PENDING`

`STORYBOARD_FREEZE=PENDING`

This evidence proves the preproduction composition review only. It does not prove production runtime interaction, final fr/de/it/pt localization, final asset loading/performance or deployment.

## Implementation QA template

A later runtime PASS must record the tested implementation HEAD, all required breakpoints/locales, interaction state, screenshot/recording reference, console/network evidence, defect/repair linkage and verdict. Unsupported PASS declarations remain invalid.
