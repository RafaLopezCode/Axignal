# Renderer Boundary

Architecture: canonical AXIGLAND → AXIGNAL graph projection → AXIGNAL semantic
cartography → AXIGNAL renderer contract → replaceable renderer adapter → initial
Sigma + Graphology implementation. AXIGNAL owns meaning; the renderer draws its
projection.

The boundary is conceptual in this slice. Do not freeze a contract schema from
an illustrative example or implement the runtime here. No Sigma/Graphology
types may leak into canonical domain entities, Evidence, FAXTs, INXIGHTs,
PATHXs, Knowledge Frontier, cognition, JEV state, temporal authority, source
acquisition, entity resolution, claim review, or anomaly authority. Graphology
may be an in-memory structure/algorithm substrate behind the adapter, but it is
not a canonical store or semantic authority.

Renderer-local mechanics include GPU buffers, primitive drawing, low-level
camera mechanics, hit testing, render scheduling, and library lifecycle. Keep
projection meaning, semantic LOD, relationship interpretation, epistemic/time
grammar, focus, labels, accessibility and provenance outside Sigma/Graphology.
No production renderer dependency or adapter is introduced by ADR acceptance.
