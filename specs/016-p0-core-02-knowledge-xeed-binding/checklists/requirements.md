# P0-CORE-02 Requirements Checklist

- [x] CTO semantics distinguish reference from ownership, truth, provenance,
  relevance, importance, discovery, derivation, source rights and promotion.
- [x] FAXT remains global and is the only supported type.
- [x] Each Xeed needs its own explicit reference; cross-Tenant reuse does not
  duplicate FAXT.
- [x] Private read requires AuthorizedXeed; raw IDs do not authorize.
- [x] Reference lookup precedes global FAXT lookup.
- [x] Missing reference and missing FAXT fail closed.
- [x] No FAXT epistemic/currentness/provenance copy or mutation.
- [x] Production writer/persistence and temporal/lifecycle semantics remain
  unimplemented/not established.
- [x] All applicable deterministic gates pass.
- [x] CTO self-audit passes; PR remains unmerged.
