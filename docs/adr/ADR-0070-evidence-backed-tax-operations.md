# ADR-0070 — Evidence-Backed Tax / VAT / AEAT Operations

**Status:** ACCEPTED  
**Date:** 2026-10-03  
**Scope:** AO-20, AO-21, AO-22, AO-23

## Context

AXIGNAL needs a private operational view of tax obligations and evidence without becoming a tax authority or silently inferring Spanish filing duties from invoices, accounting data, company form or model output.

Spanish VAT filing calendars and applicability contain conditional rules and calendar exceptions. In particular, model 303 may be monthly or quarterly, model 390 has filing exemptions, and model 349 may be monthly or quarterly. Exact deadlines may move when the final day is non-working.

## Decision

AO-23 is an evidence-backed tax-operations ledger, not an automated tax-advice or tax-filing engine.

Tax rules are versioned by jurisdiction/effective baseline. Rules describe official general deadline/applicability policy, but operational obligations are instantiated only with explicit applicability and exact deadline evidence.

The operational states are distinct:

UNKNOWN, DUE, PREPARED, FILED, ACCEPTED, REJECTED, NOT_APPLICABLE.

UNKNOWN applicability never becomes DUE merely because a calendar date passes.

For applicable obligations, PREPARED requires applicability, source-document-set, reconciliation and human-approval evidence. FILED additionally requires a filing receipt. COMPLETE/ACCEPTED additionally requires AEAT acceptance evidence.

AEAT rejection overrides positive intermediate state and remains incomplete.

NOT_APPLICABLE requires explicit applicability evidence.

AXIGNAL does not calculate final legal due dates from a generic month formula. Each instantiated obligation stores exact due time plus deadline source reference from an official calendar or authorized adviser source.

AO-23 exports are preparation/adviser artifacts only and cannot claim submission or acceptance.

## Initial canonical rule scope

The 2026-10-03 baseline includes:
- Modelo 303 quarterly;
- Modelo 303 monthly;
- Modelo 390 annual/conditional;
- Modelo 349 monthly/conditional;
- Modelo 349 quarterly/conditional.

Other tax models require separate official-source research and versioned rules before operational use.

## Authority boundaries

- AEAT/official rules: authority for filing rules/status.
- Accountant/adviser: human professional approval and applicability evidence where applicable.
- AO-20: financial-document evidence, not tax authority.
- AO-21: accounting/reconciliation evidence, not filing authority.
- AO-22: SIF/VERI*FACTU compliance, not tax-return completion.
- AO-23: private operational tracking and evidence projection.
- AXENT/LLMs: explanation/orchestration only; no tax/legal authority.
- AXIGLAND: no tax filing authority.

## Consequences

- Missing evidence stays UNKNOWN/incomplete.
- Tax completion cannot be inferred from accounting close, invoice generation or a model calculation.
- Filing and AEAT acceptance remain distinguishable and auditable.
- Deadline provenance survives into Admin/adviser exports.
- New tax models cannot enter the system without explicit versioned research/rules/tests.
