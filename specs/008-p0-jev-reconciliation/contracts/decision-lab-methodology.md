# Decision Laboratory Methodology V-next

Every evaluated record binds case ID, golden target and provenance, decision/question/state/compiler versions, answerability verdict/reasons, primitive, pinned model and SDK, raw judgment/distribution, composition policy/result, metrics and failure class/basis. Records rejected before provider evaluation contain no fabricated judgment.

Only `ANSWERABLE` cases with a scoreable, provenance-bearing single target enter model-quality metrics. Report rejected/unanswerable counts separately. If answerability itself is an independent variable, predeclare it and report structural pass rates separately from quality. Synthetic contract fixtures establish code behavior only.

Failure taxonomy: `INPUT_STATE_ERROR`, `MISSING_INFORMATION`, `QUESTION_DESIGN_ERROR`, `PRIMITIVE_SELECTION_ERROR`, `OPTION_SPACE_ERROR`, `MODEL_JUDGMENT_ERROR`, `COMPOSITION_ERROR`, `POLICY_ERROR`, `SDK_ERROR`, `SERVICE_ERROR`, `NETWORK_ERROR`, `AUTHENTICATION_ERROR`, `MODEL_VERSION_DRIFT`, `CALIBRATION_ERROR`, `EVALUATION_DESIGN_ERROR`, `GOLDEN_LABEL_ERROR`. Every attribution states one basis: deterministic detection, human adjudication, experimental inference or unknown. Unknown remains explicit.

Historical replay loads the historical contract/compiler version as recorded; it does not recompile P0-JEV-03 under V-next or alter historical bytes. Separate answerability strata and immutable held-out data prevent invalid cases or tuning leakage from being called model-quality evidence.
The prior generic V0.1 live experiment route is disabled because it has no family DecisionContract or answerability verdict. V0.1 data remains replayable and immutable.
