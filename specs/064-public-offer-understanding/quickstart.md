# Isolated review candidate

This procedure is exclusively for a disposable loopback candidate. It does not authorize production activation. The candidate labels the evaluator `SYNTHETIC-offer-rule-v1`, uses reserved example domains and controlled identity/source ports, and refuses an existing data directory. There are no real customer observations, Google credentials or live model calls.

## Reproduce

From this branch/worktree, install the frozen dev environment with Python 3.12 and `uv sync --frozen --python 3.12 --group semantic-layer-live`. The additional frozen SDK group exercises the installed question-shape contract; tests never call its external API. In `apps/web/experience`, run `npm ci`, `npm run typecheck`, `npm run check:i18n`, `npm test` and `npm run build`.

Run the built Next server on loopback port 3840 with these process-local values:

```text
AXIGNAL_RUNTIME_ORIGIN=http://127.0.0.1:3842
AXIGNAL_EXPERIENCE_ORIGIN=http://127.0.0.1:3841
AXIGNAL_AXENT_GROUNDED=true
```

Use `node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3840` in the frontend directory. In a separate terminal at repository root:

```text
uv run --group semantic-layer-live python specs/064-public-offer-understanding/candidate.py --data-dir D:/AXIGNAL/bidirectional-candidate/064-review-UNIQUE
```

Open `http://127.0.0.1:3841/__synthetic` first to establish the test-only session. Open subscriber and its reading. Initially, offer is a cited strength; audience and outcome have conditional clarification proposals. Choose clear communication on the candidate page, then use **Observe again**, **Refresh** and **Open the reading** in the portfolio. The new report has three strengths, retains history and compares compatible readings. Missing acquisition must produce uncertainty; instrument failure must withhold assessment. These are fixture conditions, not measured real-world model quality.

## Live composition boundary

The feature remains off by default. The existing First Observation flag and the new `AXIGNAL_PUBLIC_UNDERSTANDING_ENABLED` opt-in are required. A live instrument also needs the existing governed SemanticCascade configuration; missing provider configuration produces INSTRUMENT_UNAVAILABLE, never fallback invented findings. No provider SDK is imported by the new application module.

The operator rights file supports a distinct `publicOfferInput: true` purpose, in addition to `providerInput: true`. An existing routing-vocabulary grant does **not** authorize offering quotations. Each acquired page must have an applicable current grant. A governed decision must establish source rights, permitted provider-processing purpose, privacy review and retention, with an inspectable `rightsBasis`. Public availability and robots permission alone are insufficient. Provider state contains bounded public quotations and instrument conditions, never tenant, principal, focus, private analytics or user conversation. Structured identity/contact fields and Person-schema pages are excluded; patterns remove email/telephone/URL-bearing excerpts. This is deterministic minimization, **not** a general personal-data classifier: the richer purpose must cover reviewed offering content before live use.

The report retains exact citations, distribution trace and permission references privately. No probability is presented as truth and no report writes canonical business facts. History is capped at eight reports per tenant/target/subject and retention uses the earliest applicable page deadline. Reports go stale after seven days. Manual reobservation refreshes selected pages immediately and never treats exact judgment reuse as an independent replica.

## Validation on Windows

Use a new pytest `--basetemp` outside the checkout, e.g. `D:/AXIGNAL/064-pytest-UNIQUE`. The default machine Temp directory has an ACL limitation; experiment safeguards also require outputs outside the repo. Do not disable those safeguards. Five existing POSIX deployment/ownership tests require Linux and remain skipped on Windows.
