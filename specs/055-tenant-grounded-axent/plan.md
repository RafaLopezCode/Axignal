# 055 — Plan

| Layer | Module | Responsibility |
|---|---|---|
| application | `application/axent/grounded/corpus.py` | Authorized reading → sanitized evidence items |
| application | `intent.py` | Deterministic kind × family × geography × named subjects; compact memory |
| application | `retrieval.py` | Narrowing, ranking, dedup, budgeted packing |
| application | `answer.py` | Prompt sections, reasoner port, verification, grounded answer contract |
| application | `service.py` | One turn: authorize → retrieve → route → verify; cache; metrics |
| application | `coverage.py` | Family UNKNOWN reasons from the observation runtime digest |
| application | `cost.py`, `wire.py`, `copy.py` | Configured cost model, subscriber wire, six-language copy |
| cognition | `providers/luna_responses.py`, `axent_reasoner.py` | gpt-6-luna via Responses API behind the router |
| pipeline | `axent/research_ledger.py` | Tenant/Xeed-scoped research-request ledger |
| tools | `runtime/subscriber_axent.py`, `subscriber_http.py` | `POST /subscriber/organizations/{focus}/axent` |
| experience | `app/api/subscriber/axent/route.ts` | Grounded path behind `AXIGNAL_AXENT_GROUNDED` |

Risks: cross-tenant leakage (read boundary + tenant-bound cache), model
overclaiming (verification), prompt injection (sanitized quoted evidence),
prompt growth (explicit budget), stale reuse (fingerprint includes currentness).

## T10 / T11 composition

`application/axent/research.py` is the bounded attention consumer;
`pipeline/axent/research_ledger.py` stores lifecycle and append-only transitions.
`tools/runtime/observation_research.py` composes existing entitlement/Focus and
EB-07 authority; `observation_daily.py` reuses the existing evidence and Brain
continuity path. No new queue, scheduler, admission or canonical writer exists.

`grounded/model_budget.py` reserves a single model attempt through
`pipeline/axent/model_audit.py`. The audit stores hashed tenant/Focus correlation,
provider/model/purpose, usage, configured cost estimate, latency, outcome, error
class and verified answer route (including abstention); never raw prompt or key.
The concrete SDK alone reads the mounted secret file. Runtime and experience
use the existing flag in `compose.axent.override.yml`, default false.

Candidate-only validation uses `tools/runtime/axent_preflight.py`: one synthetic
authorized corpus, one live model attempt, one private research request and one
controlled source result. A replay refuses another provider attempt. Full real
subscriber authorization/evidence/Brain continuity is demonstrated by the
deterministic two-tenant HTTP integration test, not claimed from the synthetic
production-host probe. See the T10/T11 handoff for operator prerequisites.
