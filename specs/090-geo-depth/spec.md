# Feature Specification: AI visibility as deep as specialist GEO tools

**Created**: 2026-10-17

**Status**: Implemented (this PR)

**Input**: CTO, 2026-10-17: "extremadamente potentes en cada familia"; SEO/GEO agencies as clients. The clean-room benchmark (public pages of Profound, Peec and the Semrush AI toolkit) measures presence, share of voice against competitors, position and cited sources, per client and over time.

## What changes
- **Six category questions** (formerly two) plus the brand question, last, in 6 languages. The category intents are: recommend, main providers, best for a small business, best reputation, who to ask for a quote, and alternatives to the big ones.
- **New measures over the category answers:**
  - **presence:** answers naming it;
  - **share of voice:** its mentions among every organization named;
  - **average position** when named;
  - **who it names instead**, with counts;
  - **websites cited**, with counts.

  A new `AI_CITED_SOURCES` finding shows where it pays to be present.
- **The instrument changes with the questions.** The timeline compares only measurements taken with the same questions and model (`_probe_instrument`), so no false change appears. Stored measurements with two questions still render.

## Measured live (2026-10-17, isolated, about $0.0015 per organization)
| Organization | Presence | Share of voice | Average position | Named instead |
|---|---|---|---|---|
| Human Level | 6/6 | 18.8% | 1.0 | Internet República (6), NeoAttack (4), Webpositer (3) |
| iPullRank | 1/6 | 3.0% | 11 | WebFX, SmartSites, Ignite Visibility, Victorious (5 each) |
| Atrevia | 6/6 | 14.3% | 2.7 | LLYC (5), Roman (4), Tinkle (4) |
| Builtvisible | 3/6 | 9.4% | 3.3 | Impression (5), The SEO Works (5) |

## Doctrine
MASTER §54: a measurement with its instrument, conditions, sample and uncertainty. A mention is not a citation, and a citation is not an endorsement. There is no universal score.
