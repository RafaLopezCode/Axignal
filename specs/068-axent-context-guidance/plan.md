# Plan and architecture review

Graphify query completed before changes. Existing boundaries: subscriber read authorizes first, Python grounded service receives one reading, browser endpoint rechecks revision; illustrative demo is separate.

Use a packaged application JSON resource as the single reviewed product guide; web imports a generated, checked-in snapshot of this resource so its standalone bundle needs no Python filesystem. A deterministic parity test rejects drift; regenerate with uv run python -m tools.sync_axent_product_guide. Application never imports web. HTTP adapter returns existing wire shape with optional productGuide, and fresh read is required before any private response. Deterministic fallback and public illustrative endpoint use the same catalog. UI reuses existing question buttons and evidence callbacks. Product content never enters EVIDENCE or continuity authority.

Constitution check: no canonical write, scope expansion, provider coupling, truth editing, UNKNOWN coercion or new runtime dependency. Existing opt-in model rollout remains intact. Guidance is presentation/approved product documentation; signal/evidence data remains governed runtime projection.

Retrieval prioritizes meaningful lexical matches within the already-authorized scope and retains configured ceilings. Numeric verification checks cited text and limitations; does not claim complete natural-language entailment.
