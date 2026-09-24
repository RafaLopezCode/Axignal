# Architecture Guard

`tools/architecture_guard` is a deterministic, AST-based guard. It parses every
Python file in the repository and rejects forbidden dependencies and drift. No
LLM, no network. Exit code is non-zero on any violation.

Run it:

```powershell
uv run architecture-guard --root .
uv run python -m tools.architecture_guard --json
```

## Rules

| Rule | Rejects | Doctrine |
| --- | --- | --- |
| `LAYER_IMPORT` | `domain/**` importing `pipeline`, `cognition`, `apps` or `tools`. | Constitution "Architectural Constraints" |
| `PROVIDER_SDK_IMPORT` | Importing a model-provider SDK outside `cognition/providers/` (openai, anthropic, google.generativeai, litellm, transformers, ...). | ADR-0006, MASTER §13 |
| `PROVIDER_CANONICAL_WRITE` | Provider adapters importing canonical writers. LLM output → canonical write without admission. | MASTER §14, §15.1 |
| `PROJECTION_CANONICAL_WRITE` | Projection packages (`domain/pathx`, `domain/inxight`, `domain/knowledge_frontier`) importing canonical writers. | ADR-0005 |
| `XIGNAL_ISOLATION` | `domain/xignal/**` importing `domain/organizations/**`. | ADR-0004 |
| `FORBIDDEN_DOMAIN_PACKAGE` | `crm`, `workflow`, `sponsored`, `pay_to_rank`, `advertising` packages/segments in the core. | ADR-0008 |
| `PARSE_ERROR` | Python that cannot be parsed. | CI hygiene |

## Runtime companions

The guard checks structure. The runtime invariants are checked by
`tests/contracts/`:

- canonical FAXT creation requires `EvidenceAdmission`;
- `PotentialRelationship` cannot materialize as `ObservedRelationship` without
  admission;
- UNKNOWN cannot be coerced to FALSE;
- Organization identity is canonical, not subscriber-scoped;
- Xignal cannot mutate Organization canonical facts;
- provider output is never canonical truth.

## Negative tests

`tests/architecture/test_architecture_guard.py` builds synthetic source trees
with each forbidden pattern and asserts the guard rejects them. Textual grep is
never used as a substitute for AST enforcement.
