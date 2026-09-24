# Quickstart: Graph Architecture and Skill

1. Read the MASTER, Engineering Constitution, ADR-0001 through ADR-0009, and
   `docs/design/DESIGN_GOVERNANCE.md` before graph implementation.
2. Activate `.opencode/skills/axignal-graph-design/SKILL.md` for any graph work.
3. Load only the relevant reference(s); do not use a renderer object as canonical
   meaning or authority.
4. For this slice's deterministic checks, run:

```powershell
uv run pytest tests/architecture/test_axignal_graph_design.py
uv run axignal-governance spec
uv run axignal-governance docs
uv run architecture-guard --root .
```

The skill provides architecture guidance only. It is not an implementation
authorization and no graph UI or runtime is present after this slice.
