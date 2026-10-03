# AO-23 — Tax / VAT / AEAT Operations Baseline (2026-10-03)

**Status:** VERIFIED_OFFICIAL_RESEARCH_BASELINE  
**Jurisdiction:** Spain  
**Purpose:** operational architecture input for AO-23. This document is not legal or tax advice and does not replace an accountant/tax adviser.

## 1. Scope

AO-23 governs private operational tracking of tax obligations, evidence, preparation, filing receipts, AEAT acceptance/rejection and advisor exports.

It does **not** make AXIGNAL:
- a tax authority;
- an automated tax adviser;
- an AEAT filing agent;
- a source of legal applicability decisions;
- an authority over tax truth merely because accounting or invoice data exists.

## 2. Official baseline verified on 2026-10-03

### Modelo 303 — VAT self-assessment

AEAT 2026 guidance publishes:

- quarterly: days 1-20 of April, July and October for Q1-Q3;
- fourth quarter: days 1-30 of January;
- monthly: days 1-30 of the following month;
- January monthly period: through the last day of February;
- if the last filing day is non-working, the deadline moves to the immediately following working day.

Therefore AO-23 stores an instantiated due_at plus deadline_source_ref; it does not derive the final legal deadline from month arithmetic alone.

### Modelo 390 — annual VAT summary

The annual summary is conditional. AEAT material expressly identifies exemptions from filing model 390 in specified cases.

Therefore AO-23 never assumes that a taxpayer filing model 303 must also file model 390. Applicability remains UNKNOWN until evidenced.

### Modelo 349 — intra-Community recapitulative statement

AEAT publishes monthly and quarterly periodicities with specific calendar rules, including July/December and Q4 exceptions.

Therefore AO-23 models monthly and quarterly 349 rules separately and requires evidenced applicability/periodicity before an obligation is instantiated.

## 3. Official source ledger

| Ref | Authority | Source | Relevant evidence |
| --- | --- | --- | --- |
| AEAT-IVA-2026-DEADLINES | AEAT | https://sede.agenciatributaria.gob.es/Sede/ayuda/manuales-videos-folletos/manuales-practicos/manual-iva-2026/capitulo-08-gestion-iva/autoliquidaciones-iva/plazos-presentacion.html | 303 quarterly/monthly deadlines, Q4/January exceptions, non-working-day rule. |
| AEAT-IVA-2026-MODELS | AEAT | https://sede.agenciatributaria.gob.es/Sede/ayuda/manuales-videos-folletos/manuales-practicos/manual-iva-2026/capitulo-08-gestion-iva/autoliquidaciones-iva/modelos.html | 303 periodicity and presentation context. |
| AEAT-303-PRESENTATION | AEAT | https://sede.agenciatributaria.gob.es/Sede/iva/presentar-declaracion-iva-modelo-303/formas-presentacion-modelo-303.html | Electronic presentation and authentication requirements; page updated 2026-09-24. |
| AEAT-390-APPLICABILITY | AEAT | https://sede.agenciatributaria.gob.es/Sede/ayuda/manuales-videos-folletos/manuales-practicos/manual-iva-2026/capitulo-07-fiscalidad-pymes-regimen-simplificado/cuestiones-frecuentes-planteadas-capitulo.html | Annual-summary conditionality/exemptions and January filing window. |
| AEAT-349-DEADLINES | AEAT | https://sede.agenciatributaria.gob.es/Sede/todas-gestiones/impuestos-tasas/declaraciones-informativas/modelo-349-decla_____n-recapitulativa-operaciones-intracomunitarias_/plazos-presentacion.html | Monthly/quarterly 349 filing windows and exceptions. |

## 4. Canonical operational state model

Applicable obligation:

UNKNOWN -> DUE -> PREPARED -> FILED -> ACCEPTED

Alternative terminal/exception states:

- REJECTED
- NOT_APPLICABLE

Important distinctions:

- UNKNOWN applicability is not DUE.
- PREPARED is not FILED.
- FILED is not ACCEPTED.
- a generated calculation/export is not filing evidence.
- a filing receipt is not AEAT acceptance.
- missing documentation never renders COMPLETE.

For an applicable obligation, complete = true only with the required evidence set including AEAT acceptance.

A NOT_APPLICABLE closure requires applicability evidence.

## 5. Required preparation/completion evidence

Preparation evidence:

1. APPLICABILITY
2. SOURCE_DOCUMENT_SET
3. RECONCILIATION
4. HUMAN_APPROVAL

Completion additionally requires:

5. FILING_RECEIPT
6. AEAT_ACCEPTANCE

AEAT_REJECTION forces REJECTED and never complete.

## 6. Deadline architecture

Rule definitions retain the general official deadline policy and source references.

Each operational obligation retains:

- period start/end;
- exact due_at;
- deadline_source_ref.

The exact due date must come from an official calendar or authorized adviser source. AXIGNAL does not silently implement Spanish working-day/holiday law through a generic date helper.

## 7. Relationship with AO-20 / AO-21 / AO-22

- AO-20 supplies private financial-document evidence where relevant.
- AO-21 supplies accounting/reconciliation evidence.
- AO-22 governs SIF/VERI*FACTU provider compliance.
- AO-23 tracks tax obligations and filing evidence.

None of these private planes becomes AXIGLAND truth.

A compliant SIF provider does not prove a VAT return has been prepared/filed/accepted.

An accounting close does not prove a tax filing is complete.

## 8. Advisor/export boundary

AO-23 may prepare deterministic advisor/accountant exports containing:

- model;
- period;
- exact due date and source;
- current evidence-backed state;
- source/evidence references.

Exports do not submit to AEAT and do not assert legal conclusions.

## 9. Future expansion rule

Models/obligations such as 111, 115, 200, 202, 347 or other Spanish tax duties must be added only through:
- official-source research;
- versioned rule definitions;
- evidenced applicability;
- dedicated tests.

They must not be inferred from the taxpayer's name, company form or generic AI output.
