# EB-04 implementation plan

1. Reuse EB-03 Source Registry for both source authorizations.
2. Reuse HTTP source sensor and EB-02 representation/semantic grounding.
3. Materialize economic fields from grounded candidates without selecting ambiguous duplicates.
4. Admit only explicitly authorized canonical capability through EvidenceAdmission.
5. Reuse existing first_vertical.py for multi-axis reasoning; do not create another economic evaluator.
6. Expose exact representation/support spans in Human Output.
7. Reuse EB-01 GovernedExecutionController around source, semantic and evaluator dispatches.
8. Preserve explicit UNKNOWN cost when the port does not provide a contractual cost.
9. Add deterministic happy-path and adversarial tests.
10. Reconcile any EB-01 bug discovered by actual composition rather than weakening EB-04 tests.
11. Run full repository validation, Graphify, governance and diff checks.
12. Integrate only after composition is green on current main.

No live provider, network corpus, production scheduler or product UI is required by this slice.
