# Accessibility Architecture

No tested renderer establishes AXIGNAL's required graph accessibility
architecture. Accessibility is AXIGNAL-owned and empirical validation remains a
future requirement; this guidance is not proof of conformance.

Plan keyboard navigation for nodes, edges, clusters, path segments, selection,
focus/recenter, expansion, inspection, and return to context. Provide concise
text descriptions for a selected node and selected edge, including governed
meaning, direction, epistemic/currentness state, and evidence access. Expose a
PATHX as a readable ordered sequence and evidence trace as a navigable textual
provenance chain. Screen readers need a semantic projection that does not depend
on canvas pixels or spatial navigation alone.

Differentiate epistemic states without color alone. Support reduced motion and
non-animated alternatives to temporal transitions. Offer a textual or tabular
economic-neighbourhood representation that preserves relationship nature,
direction, relevant state and evidence links. Validate with assistive
technology and users; do not mark these requirements empirically satisfied
until tested.
