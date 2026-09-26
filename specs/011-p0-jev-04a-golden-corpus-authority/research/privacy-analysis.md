# Privacy analysis

`PERSONAL_DATA_REQUIRED=NO`; `SENSITIVE_PERSONAL_DATA_ALLOWED=NO`.

| Source | Personal-data exposure | Future filter / disposition |
|---|---|---|
| SEC / EDGAR | Filings and enforcement materials may name natural persons, include contact details, signatures, exhibits or personal histories. SEC notes historical names remain in enforcement records. | Restrict to legal-entity statements and redact/exclude individual names and identifiers. Exclude records with sensitive personal data or third-party material unless separately cleared. If deterministic person-free filtering cannot be validated, exclude the case. |
| GLEIF | Reporting exception formats include natural-person parents and non-reporting exceptions; records can contain person data depending on relationship fields. | Use legal-entity LEIs only. Exclude `NATURAL_PERSONS` exceptions and any person name/identifier/address. Missing relationship is not a negative. |
| Wikidata | Broad entity scope includes people. | Query business/legal entities only; inspect every referenced source and statement context; exclude person-linked case content. |
| Companies House | Registry includes officers, persons with significant control, service/home addresses and dates/identifiers. | Do not use PSC/person data. Prefer legal-entity-level fields; exclude any record/document that cannot be isolated without person data. Public register availability does not remove downstream privacy obligations. |
| TED | Notice parties and contact details may identify natural persons. | Retain organization-level facts only after deterministic field-level filtering; exclude contact fields and person-bearing narrative if it cannot be reliably removed. |
| TypeSafe | Provider privacy/DPA governs personal data supplied and service/account telemetry. | Keep corpus person-free regardless; DPA is not a source-content rights license. Provider gate remains unknown. |

No individual-level information or dataset was collected in this slice. This review did not inspect `.env` or access provider credentials.
