# 062 — Validation

Verified on 2026-10-08 on branch `feat/semantic-layer` reconciled with `origin/main`
`a97ab8b5713cbc9bd32937ddff807aae613d8cb2`. No real TypeSafe key was used and no call was
made to TypeSafe or Luna.

## Production image (the class of defect the CTO found)

The real `deploy/production/docker/subscriber-runtime.Dockerfile` was built from commit
`5138d32` on the server as `axignal-preflight-semantic:5138d32` (image 132 MB). The
candidates ran with `--network none --read-only`, user 33 with group 1991, a freshly
generated fake key mounted at `/run/secrets/typesafe_api_key` and a settings file mounted
where the runtime reads it. The image, directory and fake key were removed afterwards.

**Candidate A, `AXIGNAL_SEMANTIC_LAYER_ENABLED=false`**
(`python -m tools.runtime.semantic_preflight off`):
`ok=true`, nothing composed, no SDK module imported, no file created, 0 provider calls.
Importing `tools.runtime.service` and `tools.runtime.subscriber_composition` in the image
leaves `typesafe_sdk` unloaded.

**Candidate B, enabled, positive budget, Luna calls 0**
(`python -m tools.runtime.semantic_preflight on`), only the network replaced by an
in-process HTTP transport, so the SDK's own client serialised and parsed:

| Check | Result |
| --- | --- |
| `typesafe-sdk` in image | 0.7.1 |
| Mounted secret | absolute, regular, non-empty file (value never read by the probe, never printed) |
| Composition | `SemanticDemandScreen` with `TypeSafeSystemOneJudge`, model `jev-1.13.0` |
| Requests | 2, both `POST /v1/systemone` with a Bearer credential, 2 questions each |
| Solar notice | fit CORE, required modes `["CUSTOMER_SITE"]` |
| Unrelated notice (cleaning) | `unrelated=true` |
| Ledger | 2 calls, 4 questions, 709 input tokens as reported by the stand-in, USD 0.000029778 at the vendor-published price |
| Second run | 0 new requests, 4 memory hits |
| Luna | escalation not composed, call budget 0 |

The image has no `/run/secrets` and no TypeSafe variable in its environment.

**Compose render** (`docker compose -f compose.yml -f compose.subscriber.override.yml
-f compose.semantic.override.yml config`, nothing started): `typesafe_api_key` is mounted
only into `runtime` at `/run/secrets/typesafe_api_key` with group 1991; `experience` and
`landing` have no secrets.

## Repository gates

See the PR handoff for the exact final run (`uv sync --frozen`, ruff format/check, mypy,
pytest, architecture guard, `graphify update .`, governance).

## Not measured yet

Real Jev token counts, latency, accuracy and calibration on AXIGNAL data; the stand-in's
token counts above are not measurements of Jev. They require the separate CTO activation
and AXIGNAL-owned labels.
