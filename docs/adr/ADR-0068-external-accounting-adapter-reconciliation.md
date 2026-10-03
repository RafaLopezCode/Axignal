# ADR-0068 — External Accounting Adapter and Reconciliation Boundary

**Status:** ACCEPTED  
**Date:** 2026-10-03  
**Scope:** AO-18, AO-20, AO-21

## Decision

AXIGNAL will use an external accounting-provider adapter governed by AO-18 for accounting records and reconciliation. This decision does not authorize an AXIGNAL-owned accounting ledger.

The concrete accounting vendor is configuration, not domain authority. AO-21 is provider-neutral: imported entries and settlements must identify the AO-18 integration that supplied them, and that integration must be registered, enabled and credential-configured before imports are accepted.

AO-20 financial documents remain distinct from provider accounting entries. AO-21 links them through explicit references and reconciles them without mutating either source.

Chart-of-accounts mappings are versioned. Categories cover revenue, refunds, processor fees, settlement/cash, infrastructure costs, business expenses and tax. Imported accounting entries preserve external account code, category, currency, signed amount, source reference and optional financial-record/settlement links.

Processor settlements preserve gross, fee and net values with gross minus fee equals net. Reconciliation compares billed, paid, refunded, settled and accounted evidence by currency. Credit notes are documentary/accounting adjustments and are not treated as cash refunds for settlement arithmetic.

Any unmatched source, missing mapping, currency/amount mismatch or settlement mismatch remains an explicit unresolved discrepancy. AXIGNAL must not generate balancing entries to make reconciliation appear complete.

Period close is operational state only. Open discrepancies block close. A closed period requires an external accounting source reference.

All accounting mutations and reconciliation operations require finance-write authority with STEP_UP assurance and produce Admin governance audit records.

## Consequences

- AXIGNAL does not silently become accounting software or the legal accounting book.
- The vendor can change without changing the AO-21 domain contract.
- Accounting-provider credentials remain in AO-18 secret references, never AO-21 records.
- Billed, paid, settled and accounted values remain separate inspectable evidence streams.
- Imported expenses and infrastructure costs retain provenance and do not become AXIGLAND truth.
- Unknown and unmatched values remain unresolved rather than FALSE, zero or auto-balanced.
- AO-22 may evaluate VeriFactu/SIF providers separately without assuming the accounting adapter is a compliant SIF.
