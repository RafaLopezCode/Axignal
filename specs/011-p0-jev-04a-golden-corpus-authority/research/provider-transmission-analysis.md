# Provider transmission analysis

**Reviewed:** 2026-09-26. Official TypeSafe [Master Customer Agreement](https://typesafe.ai/legal/mca), [Data Processing Addendum](https://typesafe.ai/legal/data-processing), [Privacy Policy](https://typesafe.ai/legal/privacy-policy), and [Acceptable Use Policy](https://typesafe.ai/legal/acceptable-use-policy).

| Required field | Official evidence | Status |
|---|---|---|
| `PROVIDER_INPUT_LICENSE_REQUIRED` | MSA §5 warrants customer has rights/permissions for the rights granted; §4.1 grants service-processing rights over Input. | CONFIRMED |
| `PROVIDER_PROCESSING_RIGHTS` | MSA §4.1 permits TypeSafe to use/copy/store/disclose/transmit/transfer/display/modify/derive/process Input during term to perform service, including generating Output. | CONFIRMED for stated service purpose |
| `PROVIDER_STORAGE_RIGHTS` | Processing license includes storage for service; MSA §10.3 says no general obligation to retain and permits deletion. | CONFIRMED, limited; no guaranteed corpus retention |
| `PROVIDER_DERIVATIVE_PROCESSING` | MSA §4.1 service processing includes modification/derivation; §4.3 separately allows telemetry use. | CONFIRMED for stated scopes |
| `PROVIDER_TELEMETRY_RIGHTS` | §4.3 allows use of telemetry for service metrics/fraud/law and service/product improvement; separate from customer input model-weight training. | CONFIRMED |
| `PROVIDER_TRAINING_POLICY` | §4.1 says no model-weight training on Customer Data without prior consent. | CONFIRMED; does not mean no processing |
| `PROVIDER_RETENTION` | No general retention promise; data may be deleted, with limited backup/confidentiality treatment. Privacy policy describes service/account data processing. | CONFIRMED that indefinite retention is not promised; precise content lifecycle is limited/conditional |
| `SUBPROCESSOR_IMPLICATIONS` | DPA references subprocessors and personal-data processing. The trust subprocessor register was not confirmed in this review. | UNKNOWN where material |
| `MODEL_PROVIDER_TRANSMISSION_ALLOWED` | MSA §2.3 prohibits use of Services or Output to develop or facilitate development of a similar/competing service; §4.1 allows processing to perform service. The agreement does not resolve whether AXIGNAL benchmark evaluation and product-development use of Output falls within that restriction. | **UNKNOWN — HARD FAIL** |

The “no model-weight training” term is not a no-processing term: request content is processed to provide service and telemetry has separate uses. Since the future research purpose may use provider outputs to inform AXIGNAL development, no narrower interpretation is asserted. No clarification was requested from TypeSafe, no provider endpoint was contacted, and no input was sent.

This is an engineering rights gate, not legal advice. Until official terms or written contractual clarification make the intended use unequivocally permitted, no candidate may be transmitted in a future live experiment.
