# P0-HFX-01 Presentation Copy Leakage Register V1

This register records subscriber-facing copy defects found in the complete
loopback subscriber surface audit. Canonical values and identity remain in the
projection; this register governs only what the human-facing presentation emits.

| SOURCE_VALUE | CURRENT_RENDER | SURFACE | SEMANTIC_MEANING | USER_SHOULD_SEE | LOCALIZATION_REQUIRED | REPAIR |
|---|---|---|---|---|---|---|
| `MAINTAINS_STANDARD` and other predicate identifiers | Raw predicate string or composite projection label | Map, card, Bottom Context, focus trail, AXENT label, accessible name | Canonical predicate identity | A concise label from a presentation semantic key; unknown predicates receive neutral “Information” | Yes, through the BCP-47 locale catalog | Explicit canonical-predicate-to-semantic-key mapping, then locale copy; never mutate predicate identity |
| `OBSERVED`, `STALE`, other epistemic enums | Raw enum token | Card and Bottom Context | Epistemic state | Human-readable state such as “Observed” or “May be out of date” | Yes | Central state-to-key mapping; raw enum stays in projection and CSS state only |
| `Currentness=UNKNOWN` | Raw `UNKNOWN` | Bottom Context | Freshness has not been established | “How current this information is hasn't been verified.” | Yes | Map currentness independently; preserve canonical `UNKNOWN` |
| `Subject kind=UNKNOWN_UNSUPPORTED` | Raw implementation state and field label | Bottom Context | No supported subject-kind authority | Nothing; it is not actionable on this surface | No visible copy | Omit the field; retain `UNKNOWN_UNSUPPORTED` in the internal projection |
| `Subject resolution=UNKNOWN_UNSUPPORTED` | Raw implementation state and field label | Bottom Context | No supported subject resolver | Nothing; it is not actionable on this surface | No visible copy | Omit the field; retain `UNKNOWN_UNSUPPORTED` in the internal projection |
| `CANONICAL FAXT`, `GLOBAL ORGANIZATION`, “explicitly referenced FAXT” | Canonical class, identity, and membership-contract language | Header, card, summary, details, empty state, accessibility | Global knowledge object and private contextual membership | “Information”, “Organization”, and neutral “context” copy | Yes | Replace implementation nouns with neutral subscriber concepts without changing truth or membership |
| `Xeed`, `AuthorizedXeed`, “authorized scope” | Private-context identifier or authorization contract | Sidebar, AXENT scope, tooltips, metadata | Private context and access boundary | “Context” where useful; no authorization explanation | Yes where visible | Remove internal names and authorization narration from subscriber copy |
| Raw IDs such as `faxt-demo-a`, `subject-demo-a-unknown-kind` | Values only in projection identity/data attributes; prior accessible names could include derived machine values | ARIA names and generated labels | Stable internal identity | No raw ID as copy; a human label only | No visible copy | Keep IDs solely in internal identity/navigation state; guard values before rendering |
| `Unavailable`, “Connections are unavailable in this view”, disabled reader fields | Implementation/capability explanation | Sidebar, Connections, AXENT, timeline, missing fields | Empty, unsupported, or inactive capability | Quiet absence when it gives no actionable information; plain statement only for a load failure | Yes for any remaining statement | Remove non-actionable unavailable copy and omit missing fields; keep controls disabled and truth unchanged |
| `TEST / DEV · IN-MEMORY`, fixture/test terminology | Runtime environment diagnostic | Sidebar footer and initial page state | This page contains synthetic examples | “DEMO · EXAMPLE DATA” | Yes | Disclose demonstration data in concise product language |
| `AXIGLAND projection unavailable` | Server error payload | Error state | View failed to load | “This view couldn't be loaded.” | Yes | Keep internal error detail server-side; show a plain load failure |

## Field-by-field unknown decisions

| Field | Human value | Presentation decision | Canonical state |
|---|---|---|---|
| Currentness | Useful: recency affects how a subscriber weighs information | Show a concise localized explanation when `UNKNOWN`; show mapped copy for known currentness states | Remains `UNKNOWN` |
| Subject kind | Not actionable in this surface | Omit from primary UI | Remains `UNKNOWN_UNSUPPORTED` |
| Subject resolution | Not actionable in this surface | Omit from primary UI | Remains `UNKNOWN_UNSUPPORTED` |

The presentation catalog currently populates English (`en`) and resolves locale
tags using BCP-47-compatible language selection. Locale selection changes copy,
never canonical identity. Additional locales require translated catalog entries;
there is no predicate-token formatting fallback.
