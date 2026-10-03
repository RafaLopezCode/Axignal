# AO-22 — VERI*FACTU / SIF Compliance Baseline (2026-10-03)

**Status:** VERIFIED_OFFICIAL_RESEARCH_BASELINE  
**Jurisdiction:** Spain  
**Purpose:** architecture/compliance input for AO-22. This document is not legal advice and does not replace professional tax/legal review.

## 1. Current official baseline

The current consolidated Real Decreto 1007/2023, after the Real Decreto-ley 15/2025 extension, sets the adaptation deadlines at:

- **before 2027-01-01** for taxpayers in article 3.1.a) (corporate income tax taxpayers);
- **before 2027-07-01** for the remaining taxpayers in article 3.1.

The RDL 15/2025 was validated by Congress in December 2025. A constitutional challenge was admitted in March 2026; as of this baseline, the consolidated BOE text and AEAT 2026 guidance still publish the 2027 deadlines. AXIGNAL must therefore version this baseline and re-check official sources before live fiscal enablement.

## 2. Official source ledger

| Ref | Authority | Source | Relevant evidence |
| --- | --- | --- | --- |
| BOE-RD1007-CONSOLIDATED | BOE | https://www.boe.es/buscar/act.php?id=BOE-A-2023-24840 | Current consolidated RRSIF; 2027 deadlines; scope and SIF obligations. |
| BOE-RDL15-2025 | BOE | https://www.boe.es/eli/es/rdl/2025/12/02/15 | Extends adaptation deadlines to 2027. |
| BOE-RDL15-VALIDATION | BOE | https://www.boe.es/buscar/doc.php?id=BOE-A-2025-25695 | Congressional validation of RDL 15/2025. |
| BOE-HAC1177-2024 | BOE | https://www.boe.es/buscar/act.php?id=BOE-A-2024-22138 | Technical/functional/content rules: records, XML, chaining, QR and related SIF requirements. |
| AEAT-SIF-VERIFACTU | AEAT | https://sede.agenciatributaria.gob.es/Sede/iva/sistemas-informaticos-facturacion-verifactu.html | Current official SIF/VERI*FACTU hub; FAQs updated in 2026. |
| AEAT-RESPONSIBLE-DECLARATION | AEAT | https://sede.agenciatributaria.gob.es/static_files/Sede/Tema/IVA/Verifactu/EjemplosDeclaracionResponsable%28V0.5.1%29.pdf | Example producer declaration and version-specific responsibility posture. |
| AEAT-DEVELOPER-FAQ | AEAT | https://sede.agenciatributaria.gob.es/static_files/AEAT_Desarrolladores/EEDD/IVA/VERI-FACTU/FAQs-Desarrolladores.pdf | Clarifies SIF vs general invoice-management systems and delegated/third-party issuance scenarios. |

## 3. Compliance surface AXIGNAL avoids by not building its own SIF

If AXIGNAL were the producer of its own SIF, the regulated surface would include, among other applicable requirements:

- integrity, conservation, accessibility, readability, traceability and inalterability;
- billing-registration records and chaining/hash mechanics;
- XML content/format and generation requirements;
- cancellation records;
- event records for NO VERI*FACTU operation where applicable;
- QR and invoice wording requirements;
- AEAT remittance capability and authentication mechanics;
- per-taxpayer separation when one system supports multiple taxpayers;
- version-specific producer responsible declaration;
- test/evidence/retention duties and continuing regulatory maintenance.

AO-22 deliberately does **not** authorize AXIGNAL to own this surface.

## 4. Build vs integrate matrix

| Criterion | AXIGNAL-owned SIF | External compliant SIF provider |
| --- | --- | --- |
| Product focus | Poor fit; expands AXIGNAL into regulated invoicing software | Strong fit; keeps AXIGNAL focused on observing economic intelligence |
| Compliance burden | High and ongoing | Bounded to provider selection, adapter contract and evidence verification |
| Regulatory-change burden | AXIGNAL must continuously implement changes | Provider carries SIF implementation burden; AXIGNAL re-verifies provider/version |
| Failure blast radius | Can block invoice issuance and create direct regulatory exposure | Adapter/provider isolation; AXIGNAL can fail closed |
| Replaceability | Low if fiscal mechanics leak into domain | High through AO-18 provider-neutral boundary |
| Time/cost | Material engineering/compliance program | Lower; integration + verification program |
| AXIGLAND risk | High temptation to mix fiscal state into product truth | Lower; fiscal state remains private operational evidence |
| Decision | **REJECTED by AO-22** | **SELECTED architecture** |

## 5. Canonical AO-22 decision

**INTEGRATE_EXTERNAL_SIF_PROVIDER**

AXIGNAL will not be the producer of a SIF under AO-22.

A future decision to build an AXIGNAL-owned SIF requires a new ADR and a dedicated compliance project covering the then-current official rules, responsible declaration, integrity/traceability, records, hash/signature requirements, QR, AEAT remittance/testing, retention and producer obligations.

## 6. Live-enablement evidence gate

No provider/version may be treated as production-ready until AXIGNAL has recorded all of:

1. provider responsible declaration for the exact product/version;
2. technical adapter/contract evidence for the exact provider/version;
3. successful non-production integration/compliance test evidence;
4. explicit human approval under fiscal write authority.

Provider/version changes invalidate completeness until the new version has its own evidence set.

## 7. Authority boundaries

- SIF provider owns regulated SIF implementation mechanics for the selected version.
- AXIGNAL owns adapter configuration, references, reconciliation and operational evidence.
- The taxpayer/user remains responsible for its own tax obligations; third-party material issuance does not erase that responsibility.
- AO-20 financial documents are not by themselves legal/fiscal authority.
- AO-21 accounting adapter is not presumed to be a compliant SIF.
- Fiscal compliance evidence is private Admin state and never AXIGLAND truth.
