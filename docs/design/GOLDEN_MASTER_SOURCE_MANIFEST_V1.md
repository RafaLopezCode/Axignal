# DeepSeek V2 Golden Master Source Identity, Manifest v1

**Status:** P0-HFX-00 reproducibility evidence; source identity only
**Golden Master:** the externally supplied, accepted DeepSeek V2 executable
**Historical digest:** `4ea6f03a8529b56998c5f24a4e418dfecc6617103aad6b2fc51d48130eb104c8`
**Historical recipe:** unrecovered
**Historical digest reproducible:** no

The historical digest remains valid historical evidence exactly as supplied.
Its construction was not recovered, was not guessed, and was not used to select
this recipe. It is not a future gate.

## Meaning and limits

Manifest v1 establishes only that the current files in its explicit source
inventory have the recorded bytes. It does not prove visual correctness,
behavioral correctness, product correctness, accessibility, or reproducible
compiled output. Human visual acceptance remains separate and authoritative.

The repository contains no Golden Master implementation copy. The manifest
stores path names and hashes only. The external root is supplied at invocation
time and is not part of the manifest or product configuration.

## Included inputs

The versioned file inventory is
[`GOLDEN_MASTER_SOURCE_MANIFEST_V1.json`](GOLDEN_MASTER_SOURCE_MANIFEST_V1.json):

- `index.html`, `package.json`, `pnpm-lock.yaml`, `tsconfig.json`, and
  `vite.config.ts`;
- `src/main.tsx` and `src/styles/v2.css`;
- all 20 files under active `src/v2/`, including its four transform modules.

The entry imports `src/v2/V2App.tsx`; its internal imports remain within the
V2 module tree and use the declared React, React DOM and Framer Motion packages.
V2 fixture/content modules are included because they determine the executable
reference, but their data is never a canonical subscriber projection source.
The prototype's SVG icon and CSS noise texture are embedded data URIs. It has no
required local image/font asset directory. `index.html` requests Fraunces,
Inter, and IBM Plex Mono from Google Fonts at runtime; those remote font bytes
are not local source inputs and their rendering environment is not controlled
by this digest.

V1 files (`src/App.tsx`, `src/components/`, `src/data/`, `src/lib/`,
`src/state/`, `src/views/`, and legacy styles) are excluded because the active
entry and TypeScript configuration do not import or compile them. Generated
`dist/`, installed `node_modules/`, coverage, caches, logs, editor state, OS
metadata, `.git/`, and local environment files are excluded. The tool reads
only its explicit inventory and active V2 source root; it never traverses
excluded trees.

## Deterministic recipe

1. Accept the external root as a command argument; require every inventory path
   and `src/v2/` to exist.
2. Represent each path relative to that root with `/` separators. Do not store
   the root path. Sort paths by ascending Unicode code-point order.
3. Reject symlinks in included paths and under `src/v2/`. Fail closed when a
   required path is missing or any unexpected file appears under `src/v2/`.
4. Read exact bytes. Do not normalize line endings, Unicode, or content. A
   CRLF/LF change is a source change. File timestamps, ownership, and
   permissions do not participate.
5. For each file, record its relative POSIX path, byte length, and lowercase
   SHA-256.
6. Sort records by path and form the aggregate byte stream for each record as
   `UTF8(path) + NUL + ASCII(byte_length) + NUL + ASCII(file_sha256) + LF`.
   The aggregate is SHA-256 of the concatenated stream.
7. The JSON manifest is UTF-8 without a BOM, two-space indented, LF-terminated,
   and is not itself an input to the source digest.

## Verification

Run from the AXIGNAL repository with Python 3.11+:

```powershell
python tools/governance/golden_master_manifest.py `
  --root "<external Golden Master root>" `
  --manifest docs/design/GOLDEN_MASTER_SOURCE_MANIFEST_V1.json `
  --verify
```

`--write-baseline` is the explicit maintenance operation. It updates only the
manifest file after enforcing the configured inventory and unexpected-source
policy; it never writes to the external root. Baseline changes require normal
review and must not be described as visual acceptance.

The initial v1 baseline contains **27 files** and aggregate
`1b4154dd152d9ecd20bfaeb7585daf78b4fbc79f182fce32a2f94ff017d6ad51`.
Verification must be repeated against the unchanged Golden Master. Change
sensitivity, stable ordering, generated-output exclusion, missing-input
failure, and unexpected-source failure are covered by isolated temporary-tree
tests; those tests do not mutate the Golden Master.
