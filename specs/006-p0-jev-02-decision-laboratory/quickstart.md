# P0-JEV-02 Decision Laboratory Quickstart

Default commands are offline and do not need `TYPESAFE_API_KEY`:

```powershell
uv run python -m experiments.decision_lab validate
uv run python -m experiments.decision_lab list-cases
uv run python -m experiments.decision_lab list-grammar
uv run python -m experiments.decision_lab replay --result <recorded-result.json> --output <external-result.json>
uv run python -m experiments.decision_lab compare <baseline.json> <candidate.json>
uv run python -m experiments.decision_lab report --result <result.json>
```

To install the optional SDK for authorized live lab work only:

```powershell
uv sync --frozen --group decision-lab-live
```

Live evaluation must pass `--live`, load `TYPESAFE_API_KEY` from the environment, identify a committed experiment definition, and pass its fixed preflight budget. No default/CI command can make a provider call. V0.1 live plans are synthetic-only, sequential, use one SDK attempt, and pin `jev-1.13.0`. The current local environment had no key, so no live experiment was run for this implementation.

Outputs require a caller-selected external result directory and are create-only. The result manifest identifies mode and source; fixture replay is contract validation, not a Jev quality result.

The offline validator accepts only implemented experiment types and verifies
their independent and controlled dimensions. The preflight report measures
encoded request bytes; token count and cost are `UNKNOWN` until a provider
returns authoritative usage. A versioned TypeSafe price record can estimate
cost from provider-reported input tokens, but never establishes invoice cost.
Every plan contains predeclared evaluation criteria, and replay preserves the
criteria snapshot and immutable result digest. Relationship decomposition
retains individual atomic judgments and adds only a deterministic,
experimental comparison outcome; it cannot write canonical state.
