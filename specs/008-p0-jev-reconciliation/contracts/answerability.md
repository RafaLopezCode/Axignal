# AXIGNAL Answerability Gate

The deterministic pre-provider gate answers only whether the request meets its declared minimum information contract. It returns `ANSWERABLE` or `NOT_ANSWERABLE` with structured reason codes. It performs no fuzzy truth assessment, evidence retrieval, provider call or research planning.

Reasons include invalid decision/state version, missing/empty required information, unresolved reference, insufficient cardinality, missing semantic content or provenance, invalid direction, missing required temporal reference, invalid answer space/primitive contract and non-distinct pair arguments.

`ANSWERABLE` is not a prediction of model correctness, truth, or canonical validity. `NOT_ANSWERABLE` excludes that case from model-quality metrics. Missing information may be projected as a structured `MissingInformationRequirement`; whether/how to investigate remains the future Research Planner's authority.
