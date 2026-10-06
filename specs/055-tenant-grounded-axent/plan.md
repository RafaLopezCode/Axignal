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
