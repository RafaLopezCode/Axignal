# Additive private report contract

`FirstProof.publicUnderstanding` is optional; absent when the opt-in is disabled. Existing economic classification and opportunity DTOs are unchanged.

A report carries an immutable fingerprint ID, source acquisition/measurement/validity/expiry times; a versioned instrument/evaluator/model/representation/interpretation; source URLs, exact quotations and content fingerprints; bounded coverage; surface/persona/market/language/sample conditions; per-page rights references; three typed dimensions; and an authorized distribution/selected/resolution/reuse trace. Public subscriber reads omit the trace.

Each dimension selects an exact quotation or NOT_STATED/AMBIGUOUS/CONFLICTING/UNKNOWN. Python determines STRENGTH, CONSTRUCTIVE_GAP, UNCERTAIN or UNRESOLVED. The report authority is `DERIVED_CONDITIONED_NOT_CANONICAL`. Controls and an experimental confidence/margin policy cannot establish independent model correctness. A constructive absence claim requires stable judgment **and** complete bounded acquisition; it remains a possible representation limitation within that sample, with alternative explanations and a conditional human-reviewed proposal.

`fo_understanding_history` is an additive private SQLite table, keyed by tenant + target + report ID with subject, report JSON and retention deadline. Worker completion requires an owned lease and commits the report/history with the existing proof transaction. Keep eight reports per exact tenant/target/subject. Expiry purges history and removes citation-bearing current content without rewriting economic truth. Replaced subjects and foreign tenants cannot read history.

Comparison requires MEASURED, non-expired reports with identical instrument/model/method/source-set/locale/persona/market/sample contracts. Content changes are intentional, so content fingerprints are excluded from compatibility. Compare dimension state/cause and exact URL/text basis, ignoring acquisition time and citation ordering/IDs. Basis-only change is explicit and never claimed to be commercial improvement. AXENT selects only interpretations available at its knowledge cut; older citations cannot backdate a future interpretation.

No new public endpoint, domain entity, workflow, provider hardwiring or production migration is introduced.
