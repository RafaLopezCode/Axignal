# AXIGNAL Landing — Browser QA Evidence Manifest V1

**Status:** TEMPLATE — populated during rendered storyboard and implementation QA

A browser QA result is not PASS unless this manifest links it to inspectable evidence.

## Run identity

```text
HEAD_SHA=
BRANCH=
BROWSER_TOOL=
BROWSER_VERSION=
RUN_STARTED_AT=
RUN_COMPLETED_AT=
EVIDENCE_ROOT=
```

`EVIDENCE_ROOT` may be a PR/CI artifact URL or a governed local review-bundle path.
Binary screenshots do not need to be committed to Git when that would create repository hygiene or weight problems.

## Required evidence row

| Phase | Viewport | Locale | Chapter(s) | Interaction/state | Evidence ref | SHA-256 if local | Console | Network/loading | Finding/repair | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
## Minimum storyboard-freeze evidence

- 15/15 chapters rendered at representative desktop.
- 15/15 chapters rendered at representative tablet.
- 15/15 chapters rendered at representative mobile.
- Chapters 08, 09, 12 and 15 explicitly reviewed for subject/copy collision.
- Longest-copy and CTA-heavy chapters explicitly reviewed for fit.
- Reduced-motion equivalent reviewed for representative transitions.
- No focal/crop claim is promoted from INFERRED to CONFIRMED without a corresponding evidence row.

## Minimum implementation evidence

- all required viewport matrix checks;
- locale visual checks required by the execution order;
- keyboard and direct pagination behavior;
- touch where available;
- route/history checks where addressable;
- console-clean evidence;
- no broken assets;
- network/loading evidence proving there is no 15-image high-priority initial burst;
- final repaired screenshots after each material visual defect.

Unsupported prose such as `DESKTOP_BROWSER_QA=PASS` without evidence references is invalid.
