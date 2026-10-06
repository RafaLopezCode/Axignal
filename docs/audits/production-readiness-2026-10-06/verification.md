# Verification log and boundaries

Campaign `AXIGNAL-PR-2026-10-06-01`; final target code SHA `016235736db002038f8063f3abd311ba5dca110c`. Most specialist tests ran at the parent SHA; the only changed code slice is covered by VER-13 below.

## Environment and failures

- Windows / PowerShell; repository `.venv` uses CPython 3.12.11 per agent run; `uv 0.12.15`; Node `v24.14.1`.
- First Orchestrator `uv run pytest` attempt failed before test collection because `uv` could not write interpreter cache under sandbox `%LOCALAPPDATA%`. Rerun used a new workspace-local `UV_CACHE_DIR` and new `--basetemp`.
- In the selected suite, the local Stripe HTTP integration case was denied at `127.0.0.1` by sandbox (`WinError 10013`). It is recorded as environment-blocked for that invocation. The exact same test passed once when run with narrowly scoped loopback permission. This confirms only its fixture HTTP route.
- An identity agent likewise reported one AO-24A local HTTP case blocked; the Admin agent separately reran five relevant HTTP cases with loopback permission and reports all five passed. Do not interpret setup/socket failures as application failures.
- The security/reliability package's broader attempted batch had 35 setup errors from sandbox temp restrictions after 17 passed and was stopped; do not count that batch. Its bounded 13-test Compose/RBAC selection passed.

## Executions

| Run | Command/scope | Result | Coverage limit |
|---|---|---|---|
| VER-01 | Graphify broad readiness query, existing graph | 1,357 matches, 56 shown; truncated; index 13,005 nodes | Navigation only; verified against source; not a complete inventory |
| VER-02 | Orchestrator selected Python tests: `test_first_vertical_e2e.py`, adversarial, `test_market_planning.py`, semantic claim candidates, AO-10 billing contracts, EB-08 ops | 52 passed, 1 sandbox loopback failure | Focused contracts only; not full suite |
| VER-03 | Exact failed AO-10 signed webhook HTTP test, with loopback permission | 1 passed | Test fixture/local server only; no external Stripe |
| VER-04 | Identity agent focused tests: Xeed authority/read and Customer Zero attention suites | 47 pass; one HTTP case sandbox-denied; EB-08 synthetic suite 3 pass | Agent-reported; no auth provider, subscriber flow or 100 real observations |
| VER-05 | Billing agent AO-10 contracts + Landing tests | 32 pass; loopback integration deliberately omitted | Fixtures/static Landing tests; no checkout creation, sandbox or live payment |
| VER-06 | Admin agent: roadmap/Customer Zero/FR-30/Admin RBAC focused set | 62 pass after rerunning five loopback tests; 5/5 pass | Reported test selection; no human visual acceptance or subscriber signup |
| VER-07 | Security agent: `test_production_docker_isolation.py` and `test_ao01_admin_identity_rbac_boundary.py` via repository `.venv` | 13 pass | Contract/topology/RBAC code only; not production host or network |
| VER-08 | F/G agent: memory/Prime/scheduler/batch/runtime/budget/canary and EB-04 selected Python cases; frontend `npm test` | 148 focused Python PASS; 51/51 frontend PASS | Agent-reported tests; no canary on host, no subscriber read model, no Human First study |
| VER-09 | Full deterministic repo gate (`uv sync --frozen`, Ruff, mypy, all pytest, Architecture Guard, governance) | Not run as a full campaign gate | Audit did not modify implementation; cannot claim full-suite or release-candidate verification |
| VER-10 | Frontend full build/typecheck/browser tests in this campaign | Not independently rerun by Orchestrator | Existing AO-24A/QA docs are historical evidence; production UI still fixture-only and human visual acceptance pending |
| VER-11 | Production environment health, digest, config, DB, backup restore | Not run | Deliberately no credentials/probes; live release state remains UNKNOWN |
| VER-12 | Jev/other provider, Stripe sandbox/live, public form submission, outbound email | Not run | No provider call, external write, form submission or email. Jev remains authority-blocked, sandbox/live state unknown. |
| VER-13 | On the final commit `0162357`, `tests/contracts/test_production_docker_isolation.py` using `.venv` pytest | 9 passed in 0.11s | Revalidates the only changed files since agent snapshot: optional canary's additional secret group and its contract assertion; it does not verify deployed canary activation. |
| VER-14 | `$env:UV_CACHE_DIR='D:\AXIGNAL\Axignal\.uv-cache-cto-20261006'; uv run axignal-governance` after authoring campaign docs | PASS: architecture, deps, docs, graphify, hygiene, no-generated-data, spec, terminology | Governance suite passed on the final SHA/doc checkout. Does not substitute for the full Python/frontend/test/release gates listed in VER-09/10. |

## Orchestrator reproducible command

The selected test set, run from repository root with a fresh workspace-local cache and basetemp:

```powershell
$env:UV_CACHE_DIR = 'D:\AXIGNAL\Axignal\.uv-cache-cto-20261006'
uv run pytest tests/economic_discovery/test_first_vertical_e2e.py tests/economic_discovery/test_first_vertical_e2e_adversarial.py tests/economic_discovery/test_market_planning.py tests/semantic_extraction/test_semantic_claim_candidates.py tests/contracts/test_ao10_stripe_billing.py tests/contracts/test_eb08_product_proof_ops.py -q --basetemp='D:\AXIGNAL\Axignal\.tmp-cto-audit-20261006'
```

The socket-only rerun:

```powershell
$env:UV_CACHE_DIR = 'D:\AXIGNAL\Axignal\.uv-cache-cto-20261006'
uv run pytest tests/contracts/test_ao10_stripe_billing.py::test_runtime_stripe_webhook_http_flow_is_signed_and_replay_safe -q --basetemp='D:\AXIGNAL\Axignal\.tmp-cto-loopback-20261006'
```

Temporary test basetemps were created at new paths after confirming they did not exist. The final campaign report does not count the failed first invocation as a test pass. Generated basetemps are test artifacts only; the cache is retained for workspace reuse.
