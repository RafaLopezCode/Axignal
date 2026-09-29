# P0-HFX-01 Synthetic UX Laboratory Matrix V1

**Purpose:** exercise the shared subscriber presentation with deterministic
fictional data. This matrix is test infrastructure, not AXIGNAL semantic
authority. Only the loopback `tests.support.hfx01_server` accepts the
allowlisted `scenario` query. Unknown scenario names fail closed; the normal
subscriber projection never falls back to a synthetic scenario.

## Scenario sizes

Counts include the visible Organization plus FAXT nodes. They exclude the
private Xeed context, which is shown in the sidebar but is not an AXIGLAND
field node.

| Scenario | Visible objects | Synthetic edges | Rationale |
|---|---:|---:|---|
| `SYNTHETIC_SPARSE` | 3 | 0 | Existing root + two referenced FAXTs; baseline low-knowledge layout. |
| `SYNTHETIC_NOMINAL` | 9 | 8 | Fills the eight existing field slots and exercises ordinary labels, regions, Bottom Context, timeline marks, and AXENT states. |
| `SYNTHETIC_DENSE` | 17 | 24 | One pass through the current eight slots plus a second partial pass; 24 edges exercise a high-degree root and mixed edge patterns without random growth. |
| `SYNTHETIC_EDGE_CASES` | 12 | 7 | Nine additional FAXTs cover long/German/CJK/RTL labels, blank optional value, mixed currentness, presentation-only UNKNOWN/POTENTIAL, isolated nodes, and deep focus history. |

All Organization/FAXT objects are assembled through the existing test/dev
domain and application contracts and explicitly tagged
`CANONICAL_CONTRACT_BACKED_SYNTHETIC`. Their values and evidence are fictional
fixture content, not world truth. Synthetic relationship edges, timeline
marks, AXENT transcript/replies, and extra sidebar context labels are tagged
under `uxLab` as `PRESENTATION_CONTRACT_ONLY_SYNTHETIC`; they never enter the
canonical projection's top-level `relationships`, persistence, or evidence
admission. AXENT interactions append fixed fixture strings only. No runtime,
Jev, OpenAI, or external provider is called.

## Coverage

`CANONICAL_CONTRACT_EXISTS` means a canonical contract supports that concept;
it does not mean the synthetic example is a canonical record. `B-*` names are
local browser scenarios. Every browser result is structural/interaction
evidence only; human perception checks remain pending until a person reviews
the scenario in a normal browser.

| Presentation state / primitive | CANONICAL_CONTRACT_EXISTS | SYNTHETIC_PRESENTATION_TEST_ALLOWED | Scenario | BROWSER_TEST | RESULT |
|---|---|---|---|---|---|
| Root Xeed context | Yes: AuthorizedXeed | Yes | Sparse | B-SPARSE | Scenario smoke PASS; row-level QA pending |
| Organization | Yes: global Organization reader | Yes | Sparse/Nominal | B-SPARSE, B-NOMINAL | Scenario smoke PASS; row-level QA pending |
| Knowledge node | Yes: global FAXT reader | Yes | All | B-ALL | Scenario smoke PASS; row-level QA pending |
| Selected node | Presentation state | Yes | Nominal/Edge cases | B-NOMINAL, B-EDGE | Scenario smoke PASS; row-level QA pending |
| Protagonist | Presentation state | Yes | All | B-ALL | Scenario smoke PASS; row-level QA pending |
| Attenuated node | Presentation state | Yes | Dense | B-DENSE | Scenario smoke PASS; row-level QA pending |
| Relationship | No authorized subscriber Relationship reader | Yes, presentation-only edge layer | Nominal/Dense/Edge cases | B-EDGES | Scenario smoke PASS; row-level QA pending; never canonical |
| High-degree node | No domain cardinal authority required | Yes, fixture topology | Dense | B-DENSE | Scenario smoke PASS; row-level QA pending |
| Isolated node | Not a domain semantic | Yes | Edge cases | B-EDGE | Scenario smoke PASS; row-level QA pending |
| Signals region | Presentation contract | Yes | Nominal/Dense | B-NOMINAL, B-DENSE | Scenario smoke PASS; row-level QA pending |
| Capabilities region | Direct Organization capability fields | Yes | Nominal/Dense | B-NOMINAL, B-DENSE | Scenario smoke PASS; row-level QA pending |
| Markets region | Direct Organization market fields | Yes | Nominal/Dense | B-NOMINAL, B-DENSE | Scenario smoke PASS; row-level QA pending |
| Activity region | Presentation region only | Yes | Dense | B-DENSE | Scenario smoke PASS; row-level QA pending |
| Meaning | Presentation depth label | Yes | Sparse | B-SPARSE | Scenario smoke PASS; row-level QA pending |
| Context | Authorized private Xeed context | Yes | All | B-ALL | Scenario smoke PASS; row-level QA pending |
| Inference | Presentation depth only; not an inference claim | Yes | Edge cases | B-EDGE | Scenario smoke PASS; row-level QA pending |
| Evidence | Evidence access remains unavailable; axis is presentation only | Yes, unavailable state | Sparse/Edge cases | B-SPARSE, B-EDGE | Scenario smoke PASS; row-level QA pending |
| Unknown state | UNKNOWN remains distinct from FALSE | Yes, presentation override only | Edge cases | B-EDGE | Scenario smoke PASS; row-level QA pending; canonical FAXT unchanged |
| Potential state | No FAXT epistemic enum authority | Yes, presentation-only override | Edge cases | B-EDGE | Scenario smoke PASS; row-level QA pending; not canonical truth |
| Observed state | EpistemicState contract | Yes | Sparse/Nominal | B-SPARSE, B-NOMINAL | Scenario smoke PASS; row-level QA pending |
| Current / stale | Currentness contract | Yes | Nominal/Dense/Edge cases | B-NOMINAL, B-DENSE, B-EDGE | Scenario smoke PASS; row-level QA pending |
| Short label | Presentation contract | Yes | Sparse | B-SPARSE | Scenario smoke PASS; row-level QA pending |
| Long label | Presentation contract | Yes | Edge cases | B-EDGE | Scenario smoke PASS; row-level QA pending |
| Multilingual label | Locale stress, identity unchanged | Yes | Edge cases | B-EDGE | Scenario smoke PASS; row-level QA pending |
| UI locale preference | User override > browser preference > English fallback; partial copy profiles only | Yes, loopback UX Lab only | Nominal | B-LOCALE | Manual profile switching PASS for en/es/de/ja/ar and Automatic; translated-copy completeness is not claimed |
| Focus Trail short | Session navigation state | Yes | Sparse | B-SPARSE | Scenario smoke PASS; row-level QA pending |
| Focus Trail long | Session navigation state | Yes | Edge cases | B-EDGE | Scenario smoke PASS; row-level QA pending |
| Back | Session navigation state | Yes | Edge cases | B-EDGE | Scenario smoke PASS; row-level QA pending |
| Forward | Session navigation state | Yes | Edge cases | B-EDGE | Scenario smoke PASS; row-level QA pending |
| Home | Organization focus action | Yes | All | B-ALL | Scenario smoke PASS; row-level QA pending |
| Reset | Camera/focus presentation action | Yes | Dense | B-DENSE | Scenario smoke PASS; row-level QA pending |
| Pan | Camera presentation state | Yes | Nominal/Dense | B-NOMINAL, B-DENSE | Scenario smoke PASS; row-level QA pending |
| Zoom | Camera presentation state | Yes | Nominal/Dense | B-NOMINAL, B-DENSE | Scenario smoke PASS; row-level QA pending |
| Minimap | Derived presentation | Yes | Dense | B-DENSE | Scenario smoke PASS; row-level QA pending |
| Bottom Context sparse | Authorized direct fields + unknowns | Yes | Sparse | B-SPARSE | Scenario smoke PASS; row-level QA pending |
| Bottom Context rich | FAXT/Organization direct fields | Yes | Nominal/Dense | B-NOMINAL, B-DENSE | Scenario smoke PASS; row-level QA pending |
| AXENT empty | No reasoning authority | Yes, empty fixture | Sparse | B-SPARSE | Scenario smoke PASS; row-level QA pending |
| AXENT contextual | Active identity presentation | Yes | Nominal | B-NOMINAL | Scenario smoke PASS; row-level QA pending |
| AXENT long content | No reasoning authority | Yes, fixed transcript fixture | Dense | B-DENSE | Scenario smoke PASS; row-level QA pending |
| AXENT composer | No production composer authority | Yes, local canned reply only | Nominal/Edge cases | B-AXENT | Scenario smoke PASS; row-level QA pending |
| AXENT disabled move | Capability state | Yes | Sparse/Edge cases | B-SPARSE, B-EDGE | Scenario smoke PASS; row-level QA pending |
| AXENT available move | No reasoning claim; canned fixture response | Yes | Nominal/Dense | B-AXENT | Scenario smoke PASS; row-level QA pending |
| Timeline empty | No historical authority | Yes | Sparse/Edge cases | B-SPARSE, B-EDGE | Scenario smoke PASS; row-level QA pending |
| Timeline populated | No historical authority | Yes, decorative marks only | Nominal/Dense | B-DENSE | Scenario smoke PASS; row-level QA pending; control remains unavailable |
| Sidebar sparse | Current test/dev context | Yes | Sparse | B-SPARSE | Scenario smoke PASS; row-level QA pending |
| Sidebar populated | No multi-context reader | Yes, fixture labels only | Nominal/Dense | B-SIDEBAR | Scenario smoke PASS; row-level QA pending |
| Multiple Xeeds | No multi-Xeed list authority | Yes, 101 explicitly synthetic labels in Nominal; only the Xeed already represented by the authorized projection is selectable | Nominal/Dense/Edge cases | B-SIDEBAR | Browser interaction PASS; human visual QA pending |
| Context search | No production search contract | Yes, local fixture-label filter with a bounded scroll list | Nominal/Dense/Edge cases | B-SIDEBAR | Filtered a 101-row fixture; human visual QA pending |
| Recent | No recent-context contract | No | Not representable | — | Not implemented; authority absent |
| Governance available | Research depth presentation control | Yes | Nominal/Dense | B-SIDEBAR | Scenario smoke PASS; row-level QA pending |
| Governance unavailable | Capability unavailable state | Yes | Sparse/Edge cases | B-SIDEBAR | Scenario smoke PASS; row-level QA pending |
| Long localized sidebar labels | Layout stress only | Yes | Edge cases | B-EDGE | Scenario smoke PASS; row-level QA pending |
| Account identity available | No account identity reader | Yes, synthetic QA label only | Nominal | B-SIDEBAR | Scenario smoke PASS; row-level QA pending; not account authority |
| Account identity unavailable | No account identity reader | Yes | Edge cases | B-SIDEBAR | Scenario smoke PASS; row-level QA pending |
| Responsive | CSS presentation contract | Yes | All | B-RESPONSIVE | Scenario smoke PASS; row-level QA pending |
| Reduced motion | OS preference presentation contract | Yes | All | B-REDUCED-MOTION | Scenario smoke PASS; row-level QA pending |

## Not representable as product state

- Recent-context ordering, actual multiple-Xeed access, real workspace and
  account identities: no corresponding reader exists. The laboratory may
  filter or select fictional sidebar labels only.
- Canonical semantic Relationships, provenance, historical events, Evidence
  dereferencing, source rights, and AXENT reasoning: the synthetic layer may
  exercise their visual pressure only. It must not present them as canonical.
- `POTENTIAL` and `UNKNOWN` test overrides are carried only in `uxLab` and do
  not mutate the underlying FAXT state.
- Dense placement intentionally reuses the existing field slots. Any overlap,
  congestion, or minimap limitation is a reported renderer limitation; this
  fixture does not authorize a new layout system.

## Acceptance status

The API contract is deterministic and isolated. The scenario-level browser
smoke and representative interactions have run locally with all non-loopback
requests blocked. The row-level status below means scenario smoke succeeded;
it does not certify every listed micro-interaction or human perception. Normal-
browser human review remains pending before considering the laboratory fully
exercised. Synthetic UX coverage never implies production data, Relationship
authority, provenance, AXENT reasoning, or production readiness.

### Automated browser evidence

- Sparse: HTTP 200; 3 visible objects (Organization + 2 FAXTs), 0 synthetic
  edges, 1 context label, empty synthetic transcript, and no page errors.
- Nominal: HTTP 200; 9 visible objects, 8 field/minimap edges, 3 context
  labels, 2 initial transcript messages, and 2 decorative timeline marks.
- Dense: HTTP 200; 17 visible objects, 24 field/minimap edges, 8 context
  labels, 3 initial transcript messages, and 2 decorative timeline marks.
  The original 1280×720 capture showed label collisions in Nominal and Dense,
  with greater congestion in Dense; the lab toolbar also obscured the
  breadcrumb/session header. This is the pre-repair baseline, not the current
  acceptance result.
- Edge cases: HTTP 200; 12 visible objects, 7 field/minimap edges, 4 context
  labels, multilingual and long labels, deep focus history, and presentation-
  only epistemic overrides. Selecting the overridden FAXTs showed “Not
  established · synthetic” and “Possible · synthetic”; raw
  UNKNOWN/UNKNOWN_UNSUPPORTED copy was absent.
- Nominal move and composer interactions appended only fixed synthetic replies;
  context search filtered only the allowlisted local fixture labels.
- At 390×844 the document had no horizontal overflow. Reduced-motion
  preference was detected and transition duration reduced to effectively zero.
- The default route hid lab controls, kept the composer disabled, and rendered
  no synthetic edges. The run attempted zero external requests and produced
  zero browser page errors.
- A run with corrected selectors counted FAXT node-value elements separately
  from the Organization anchor; scenario object totals above come from the
  fixture API contract and DOM contents, not the FAXT-only selector count.

| QA evidence | Result |
|---|---|
| API isolation and scenario determinism | PASS; deterministic contract tests |
| Browser scenario interaction checks | Scenario smoke PASS; row-level human QA remains pending |
| Sparse / nominal / dense / edge-case human QA | Required; pending |
| Production readiness | Not inferred |

## Synthetic UX findings repair

The pre-repair 1280×720 browser findings above remain as historical evidence.
The scenario selector is now selected only by the loopback server's
allowlisted `scenario` query parameter. There is no visible lab toolbar in the
application viewport, and the default route still hides synthetic content.
The harness therefore adds no product overlay or layout reservation.

### DeepSeek V2 mechanism inspected

The executable reference inspected was `D:\AXIGNAL\UX DEEPSEEK\src\v2\Field.tsx`
and `D:\AXIGNAL\UX DEEPSEEK\src\v2\data.ts`. V2 authors stable normalized
world coordinates in its fixture and keeps label dimensions in screen space.
Label side is selected from authored position thresholds; the inspected
renderer does not implement general label collision solving, wrapping,
truncation, or alternate-side search for arbitrary dense graphs. Its authored
fixture geometry avoids many collisions. It does implement attention-aware
semantic zoom: ordinary labels reduce at `k < 0.78`, and further tiers change
detail at `k < 1.2`; directly relevant/focused/near/lens content receives
different visibility and edge attenuation. The static V2 `EDGES` data is
illustration input, not AXIGNAL Relationship authority.

The subscriber repair keeps the fixed world positions and topology stable,
then adds a deterministic screen-space label pass: try the authored preferred
side, then other sides; reject candidates outside the field or colliding with
other labels, node marks, or fixed controls; prioritize focus, Organization,
then synthetic edge-neighbors, then ordinary context. At overview zoom it
hides ordinary labels while retaining every node. If an attention-priority
label has no candidate clear of a synthetic edge, it may remain visible over
that edge rather than disappear. This is a narrow density extension; it does
not relocate nodes or add a layout dependency.

### Repaired findings and evidence limits

| Finding | Repaired behavior / evidence | Status |
|---|---|---|
| Harness overlaid navigation | Query-selected scenario; no product toolbar | PASS by source and contract tests |
| Node-position collision / spatial memory | Fixed deterministic world positions and topology; no jitter or focus-triggered re-layout | PASS by source/contract inspection; exact 1280×720 human check pending |
| Label-label collision | Deterministic side search avoids occupied label rectangles; lower-priority labels are decluttered if no valid placement remains | Browser inspection at the available 1872×1244 viewport showed no obvious overlap; exact counts at 1280×720 pending |
| Label-node collision | Candidate placement rejects other node-mark rectangles | Same viewport limitation as above |
| Focus-transition / camera changes | Label layout is recomputed on camera updates using stable world positions | Contract/source verified; full human navigation sequence pending |
| Zoom collision / overview legibility | Below `0.78`, ordinary/context labels are hidden while node marks remain; focus and Organization labels retain priority | Zoom-out capture showed reduced labels with nodes present; zoom-in/reset and exact counts pending |
| Dense edge/label pressure | Edges attenuate; focus-connected synthetic labels get presentation priority and may tolerate edge overlap | Dense capture showed nodes/labels remain present at the available viewport; high-degree hairball judgment at 1280×720 pending |
| Minimap and camera synchronization | Existing minimap is redrawn from the unchanged world nodes and current camera | Full pan/zoom/resize synchronization sequence remains pending human QA |
| Bottom Context / AXENT / Focus Trail | One selected-node interaction synchronized protagonist, camera, trail, Bottom Context and AXENT context | One interaction observed; multi-step Back/Forward sequence remains pending |

Collision taxonomy: the pre-repair screenshots showed label-label and
label-node crowding, not evidence that node positions collided. The repair
does not claim zero edge-label intersections: an explicit attention fallback
can tolerate a synthetic edge passing beneath a priority label. Static,
focus-transition, zoom, pan, viewport-resize, and exact 1280×720 collision
counts have not all been independently measured after repair. The current
browser capture viewport was 1872×1244, so the requested 1280×720 acceptance
remains a human check.

```text
LAB_UI_OVERLAPS_PRODUCT=NO
LAB_UI_AFFECTS_PRODUCT_GEOMETRY=NO
DEFAULT_ROUTE_LAB_HIDDEN=YES
GOLDEN_MASTER_DENSE_LAYOUT_LIMITATION=YES
NOMINAL_NODE_POSITION_COLLISIONS=NONE_OBSERVED; 1280x720 HUMAN CHECK PENDING
NOMINAL_LABEL_LABEL_COLLISIONS=NONE_OBVIOUS_IN_1872x1244_CAPTURE; 1280x720 HUMAN CHECK PENDING
NOMINAL_LABEL_NODE_COLLISIONS=NONE_OBVIOUS_IN_1872x1244_CAPTURE; 1280x720 HUMAN CHECK PENDING
DENSE_NODE_POSITION_COLLISIONS=NONE_OBSERVED; 1280x720 HUMAN CHECK PENDING
DENSE_LABEL_LABEL_COLLISIONS=NONE_OBVIOUS_IN_1872x1244_CAPTURE; 1280x720 HUMAN CHECK PENDING
DENSE_LABEL_NODE_COLLISIONS=NONE_OBVIOUS_IN_1872x1244_CAPTURE; 1280x720 HUMAN CHECK PENDING
ZOOM_OUT_LEGIBILITY=ORDINARY LABELS REDUCE; ALL NODE MARKS REMAIN
NOMINAL_ZOOM_LEGIBILITY=NO OBVIOUS LABEL COLLISIONS IN 1872x1244 CAPTURE
ZOOM_IN_LEGIBILITY=HUMAN CHECK PENDING
PROTAGONIST_PRIORITY=FOCUS LABEL NEVER DECLUTTERED
SPATIAL_MEMORY_STABLE=YES
LAYOUT_JUMPING=NO EVIDENCE; WORLD POSITIONS ARE FIXED
RANDOM_POSITIONING=NO
NOMINAL_EDGE_READABILITY=INSPECTED; EXACT 1280x720 HUMAN CHECK PENDING
DENSE_EDGE_READABILITY=ATTENUATED; HAIRBALL HUMAN CHECK PENDING
HAIRBALL_CONTROL=ATTENUATION AND ATTENTION PRIORITY; HUMAN JUDGMENT PENDING
NOMINAL_MINIMAP=NOT FULLY VERIFIED
DENSE_MINIMAP=NOT FULLY VERIFIED
BOTTOM_CONTEXT_COORDINATION=ONE SELECTION OBSERVED; FULL NAVIGATION PENDING
AXENT_COORDINATION=ONE SELECTION OBSERVED; FULL NAVIGATION PENDING
FOCUS_TRAIL_COORDINATION=ONE SELECTION OBSERVED; FULL NAVIGATION PENDING
FIXTURE_SPECIFIC_LAYOUT_HACKS=NO
CANONICAL_TRUTH_CHANGED=NO
PRODUCTION_PATH_CONTAMINATED=NO
```

Human QA remains required for Nominal and Dense at zoom-out, nominal zoom,
and zoom-in; selection → second selection → Back → Forward → pan → zoom out →
zoom in → reset; minimap bounds and synchronization; and edge/hairball
readability at 1280×720. No screenshot-derived count or automated interaction
is treated as human acceptance.

### Expanded minimap fit correction

The human screenshot comparison showed that fixed minimap bounds left excessive
unused space beside the rendered graph. The map now derives padded x/y extents
from the current `worldNodes`; the same coordinate transform is used for node
marks, synthetic edges, the camera window, and click-to-center input. Its
8-unit SVG inset leaves a deliberate perimeter while the graph uses the
available container. The graph itself and its world positions do not change.
The reloaded `SYNTHETIC_NOMINAL` browser view shows the node/edge map fitted
inside the minimap frame. Pan/zoom/resize interaction fidelity and human
acceptance at 1280×720 remain pending.

### Focus connections and label visibility

The subscriber demo exposes pills only for UX-lab edges marked
`syntheticFixture=true` that touch the current focus. Each pill is labeled as a
synthetic demo link and navigates to its fixture endpoint; these edges remain
outside the canonical projection and assert no production Relationship. A
scenario with no fixture edge shows an explicit empty state. The “Hide text”
control hides node labels while preserving node marks, edges, focus, and camera;
it is reversible and presentation-only. Browser inspection at 1280×720
confirmed the toggle and pill navigation. Production relationship support is
still `UNKNOWN_UNSUPPORTED`.
