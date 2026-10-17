# Feature Specification: Jev judges sector and regulatory headlines

**Created**: 2026-10-17

**Status**: Implemented (this PR)

**Input**: CTO, 2026-10-17: "el éxito del motor de AXIGNAL depende de usar Jev a la perfección". The per-family inventory found that Context and Regulation screened headlines with the generative assistant, in one opaque call returning "the indexes".

## What changes
- **`application/context/headline_judgment.py`** asks one Noul question per headline over a typed state. The state names the sector, what the briefing keeps and what it excludes; there is a news purpose and a regulation purpose.
  - Python keeps only usable `true` answers. An uncertain answer stays out: shown is what is judged relevant, never what is merely unrejected.
  - A headline judged once is remembered (judgment memory), so it is not paid for again.
- **The sector context and regulation runners** use Jev when it is configured (60k-token budget per run).
  - Otherwise they fall back to the governed assistant, as before.
  - When neither is available, the run stays queued, never "nothing relevant".
- **The instrument recorded** on each briefing names the evaluator and the method.

## Measured before promotion (production, read-only, 2026-10-17)
| Sector, country | Candidates | Assistant kept | Jev kept | Both |
|---|---|---|---|---|
| solar-pv-installation, ES | 33 | 8 | 9 | 8 |
| market-research, ES | 40 | 0 | 1 | 0 |
| landscaping-gardening, ES | 1 | 0 | 0 | 0 |

The 74 headlines cost $0.0004 of Jev in 3 calls. The added solar headline (renewables lowering electricity prices) is about the sector.

## Doctrine
The evaluator is replaceable and non-authoritative. It decides what is shown, never what is true. No provider is hard-wired: the semantic cascade is used, with the assistant as fallback (ADR-0090).
