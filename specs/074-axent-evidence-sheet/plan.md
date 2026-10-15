# Plan and architecture review

1. Inspect the current canonical Observatory in the browser and trace the shared
   account/demo/Admin entrypoints. Read AXIGNAL design authority and targeted
   sheet focus/scroll guidance; keep unrelated local changes isolated.
2. Separate the existing finding/evidence body from AXENT's sidebar. Constrain
   the canvas to available viewport space with its own scrolling content; dock
   the evidence layer inside it. Reuse all existing projections and callbacks.
3. Keep DepthAxent and RuntimeAxent behavior unchanged. Add an independently
   addressable sidebar and use the existing mobile focus containment when open.
   Keep the handwritten entry action keyboard accessible.
4. Exercise sheet focus, Escape, return, navigation, independent rail geometry,
   evidence/source preservation and shared entrypoint parity; test draft entry
   without issuing production questions or observation commands.
5. Run frontend and repository gates, render wide/narrow/reduced-motion states,
   refresh AST-only Graphify and record convergence and residual limits.

Architecture review: PASS. Graphify queried before source exploration. The
current implementation is Observatory, not the legacy RuntimeProductProjection.
Only presentation state/placement changes; canonical and derived data remain
the same governed objects. No backend or domain boundary changes are needed.
