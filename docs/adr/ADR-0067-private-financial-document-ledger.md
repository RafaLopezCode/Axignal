# ADR-0067 — Private Financial Document Ledger Boundary

**Status:** ACCEPTED  
**Date:** 2026-10-03  
**Scope:** AO-20

## Decision

AXIGNAL maintains an internal append-only financial-document ledger that explains commercial money and document flows without becoming the legal, accounting or fiscal system of record.

AO-10 billing facts and AO-20 financial documents are distinct. A verified provider event may result in multiple AO-20 records. In particular, a paid Stripe invoice produces a distinct invoice record and payment record linked to the same verified billing event. Refunds and credit notes are separate records.

Every financial record preserves stable identity, account, kind/state, occurred/recorded time, currency, gross magnitude and source provenance. Provider object/event references and future accounting/fiscal adapter references are first-class metadata.

Corrections never overwrite prior records. A credit note is a new immutable record that points to the record it corrects.

Tax basis is explicit. KNOWN requires net plus tax to equal gross. If the source does not provide sufficient tax evidence, tax basis remains UNKNOWN and no VAT/tax amount is invented.

Exports are deterministic projections over immutable records. Refunds and credit notes use negative signed gross values in exports while stored record magnitudes remain non-negative.

External accounting/fiscal records require an explicit adapter reference and privileged finance authority. AO-21 will select and govern the accounting adapter/reconciliation strategy.

## Consequences

- Stripe payment state is not an invoice/document system of record.
- Admin rendering is operational visibility, not legal/fiscal issuance authority.
- Replay of one billing event cannot duplicate financial records.
- Same financial record identity with different content fails closed.
- Historical invoices remain inspectable after credit notes/corrections.
- Financial exports retain source-document provenance and can reconcile deterministically by currency/source.
- No AO-20 record may become AXIGLAND economic truth merely because it exists in Admin.
