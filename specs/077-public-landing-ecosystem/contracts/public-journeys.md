# Public journey contracts

Planned routes: `/`, supported locale home variants, `/data`, `/industries`, `/industries/[industry]`, their published locale variants, and existing `/pricing`. Final localized path details follow existing Next locale conventions and must be checked against the `[locale]` route boundary before implementation.

- “Ver un ejemplo” → `/demo`; family deep links use only existing canonical family/channel values.
- “Empieza con tu organización” → existing `/signup`; access stays governed by the existing runtime. Invitation-based access is explained; no newly promised public checkout.
- Current Design Partner access request → existing `/contact`, with current enabled/disabled channel behavior retained.
- Trust/data rights → `/policies` and `/gdpr`; Knowledge retains its published locale URL contract.
- New catalog filters act on static editorial content, never trigger fabricated research or mutate business truth.
- Header/footer route changes must retain login/start telemetry identifiers and keyboard/mobile navigation.
- Home anchors `how`, `proof`, `audience`, `trust`, `pricing` retain existing chapter semantics where the corresponding sections remain; no arbitrary new AO-12 event kinds.

All metadata/JSON-LD follows actually published text; no review stars, customer counts, claims of integrations or fabricated results. No private runtime, Admin projection or subscriber company data is exposed.
