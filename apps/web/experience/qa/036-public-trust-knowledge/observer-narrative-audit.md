# Observer / visual narrator audit — 2026-10-03

Implemented on `main`, at the human's explicit request. Exploratory visual refinement; **human visual acceptance remains pending**. This does not promote new Golden Masters or replace brand authority.

## Findings and repair

The previous implementation reused one character and extracted poses from character sheets with silhouette masks. Those masks clipped hats, shoulders and feet. Unrelated use cases reused identical gestures. The narrator also appeared ornamentally in operational panels and recovery states.

The replacement uses 23 independent transparent PNG illustrations, selected against the supplied character references. The original PNG bytes are preserved. Alpha bounds plus a 24-source-pixel margin define the viewport; no silhouette mask or pixel processing is applied. A shared 290 × 260 frame gives each context a stable layout. Visible illustrations load near the viewport. Decorative equivalents of nearby copy are hidden from assistive technology; optional meaningful image labels remain supported.

## Narrative assignment

| Scene | Surface | Visual action |
|---|---|---|
| discover | Hero: observe | Inspect an open notebook |
| connect | Hero: connect | Compare contextual notes beside a tablet |
| reason | Hero: understand | Contrast two source slips |
| strategy | Strategic direction | Study two paths on a map |
| business | Business development | Compare document slips with a notebook |
| ecosystems | Ecosystem analysis | Examine connected nodes |
| representation | Digital representation | Inspect a generic page on a tablet |
| marketing | Marketing | Read message cards before interpretation |
| communication | Communication | Study a quoted page |
| research | Research | Write patient notes on a stool |
| journalism | Journalism | Return to source documents |
| focus | Pricing | Consider the scope of attention on a desk map |
| dispatch | Weekly brief | REJECTED: missing shoulder. Removed; the centred editorial paper carries this scene. |
| journey | Closing invitation | Walk forward with notebook and monocle |
| contact | Contact | Read the visitor's letter while seated |
| welcome | Access | Welcome with the primary notebook identity |
| boundaries | Trust and policies | Read a book's fine print |
| explain | Axent | Explain the connection between two documents |
| certainty | Evidence editorial | Inspect a document's basis |
| layers | Organization/editorial | Look beneath the top page |
| time | Temporal editorial | Investigate a sequence on folded paper |
| unknown | Unknown editorial / unanswered states | Keep a blank question open |
| conversation | Axent editorial | Share a notebook in dialogue |
| memory | Memory editorial | Revisit retained source folders |

The same editorial illustration may accompany the same article in its index, preview and reading view. Unanswered states share the same meaning. They do not create new decorative poses. The design laboratory shows the hero illustration as a narrative example and labels it accordingly.

Ornamental repetitions were removed from Administration, the Panorama continuity note, the focus explanation dialog, the 404 page and loading/error/unavailable states. The human-supplied laptop illustration in the Panorama centre and the official logo/isotype remain untouched.

## Rejected variants — never distribute

These generated files remain outside the repository's public assets:

| Generated file | Reason |
|---|---|
| exec-c47efa8e-1036-4552-a5b0-489e742d3bf7.png | Human rejection: dispatch character has three arms |
| exec-2f052305-d045-4089-a71c-d8d495138ab8.png | Human rejection: pointed feet and missing shoulder |
| exec-52517c1e-f5cb-40d2-ac83-57f55a15af92.png | Human rejection: welcome character has three arms |
| exec-d1240932-58e1-4e7a-94a7-23877245bd40.png | Monocle unsupported by a hand; superseded |
| exec-7e6fdbf9-468c-4845-aa98-d6fecbe935aa.png | Monocle unsupported by a hand; superseded |
| exec-389801a2-1aea-4ad3-b3fb-4eaa6ab1df40.png | Furniture outside the restrained palette; superseded |
| exec-badab3bb-e5a4-4f01-a0e9-539f2c1cf1d7.png | Approval checkmarks imply unsupported certainty; removed in replacement |

All selected variants received agent visual inspection for two arms, one blue monocle, coherent shoulders, complete feet and contextual purpose. This inspection is not a substitute for the human's visual acceptance. Distributed asset hashes, original source paths and alpha bounds are recorded in `observer-narrative-provenance.json`.

## Epistemic and interaction boundaries

Every drawing is `PRESENTATION_STATE`, never evidence, a factual assertion, or an indication of live research progress. The laptop centre's existing illustrative label and pause/reduced-motion controls are preserved. No model provider, economic semantics, admission rule, data state, authentication authority or production deployment changes.

## Validation

- Browser: all eight use cases at desktop and 320px; equal frames of 240 × 215.16px and 180 × 161.38px respectively. Narrow document width does not exceed viewport width.
- Browser: six editorial reading frames at 1743 × 1188. Each complete frame stays inside its art container, with at least 12px bottom clearance.
- Browser: hero modes, Knowledge feature, Pricing, weekly brief, closing, welcome, contact, policies and Axent inspected; screenshots prefixed `037-` in this QA directory. Pricing's decorative illustration remains hidden below the existing 800px breakpoint.
- Build and TypeScript pass; 20 frontend tests pass; locale inventory has 916 entries and no missing translations.
- Repository gates pass: frozen sync, Ruff format/check, mypy, 945 pytest tests, Architecture Guard and all eight governance checks. AST-only Graphify update completed.

Older `036-observer-*` screenshots and records describe the earlier masked-sheet repair. They are historical evidence, not the final narrator implementation.

## Human correction — newsletter shoulder
The human identified exec-0b192695-6985-4f01-8a0d-a8b8baf20a8e.png as the previously rejected missing-shoulder character. The agent had wrongly associated that earlier rejection only with the walking variant. Dispatch-v2 is now rejected, absent from the runtime atlas and absent from public assets. Previous 037-narrator-dispatch screenshots are historical rejected evidence. The brief uses a centred editorial paper, without an unapproved substitute character.