# AXIGNAL UI/UX Design Intelligence

> These skills are **design intelligence**, not product authorities. Precedence is
> defined in [DESIGN_GOVERNANCE.md](DESIGN_GOVERNANCE.md): the MASTER wins.

## Installed skills (exactly two)

| Skill | Responsibility | Install path |
| --- | --- | --- |
| `frontend-design` | Visual direction, art direction, composition, typography, hierarchy, spatial rhythm, motion language, interaction polish, distinctive visual identity, avoiding generic AI aesthetics. | `.opencode/skills/frontend-design/SKILL.md` |
| `ui-ux-pro-max` | Information architecture, interaction design, usability, accessibility, responsive behavior, navigation, cognitive load, UX heuristics, consistency, component/state design, empty/loading/error states, data-density, dashboard ergonomics. | `.opencode/skills/ui-ux-pro-max/SKILL.md` |

Graph/network visualization UX is deliberately **excluded** from this pair. It is
reserved for the future `GRAPH_ENGINE_BAKEOFF` and an AXIGNAL-specific
graph-design skill (see [DESIGN_GOVERNANCE.md](DESIGN_GOVERNANCE.md)).

## Provenance (pinned upstream revisions)

| Skill | Upstream | Upstream revision | Install mechanism | Local `SKILL.md` SHA-256 |
| --- | --- | --- | --- | --- |
| `frontend-design` | [anthropics/skills](https://github.com/anthropics/skills) (`skills/frontend-design`) | `33375500bcea98d610eb30ce10ac4e59b89c390d` | Direct vendoring from the pinned revision (`SKILL.md` + `LICENSE.txt`) | `d91970639e9f5c37682ac7ab60094d35f1c7c1f38d731bd56396563aee10c1d3` |
| `ui-ux-pro-max` | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | source-of-truth repo `dcc40ff5133ef78276117db0cc34e7b83cc8aeba`; published package `ui-ux-pro-max-cli@2.15.0` | Official installer: `npx ui-ux-pro-max-cli@2.15.0 init --ai opencode --offline` | `fff1d6ffd0c5e2e121f83e4c5bdbf52f25695a4de37d445a7b2f3afa1de362d9` |

Machine-readable form: [SKILLS.lock.json](SKILLS.lock.json).

### Why these upstreams (super-skill selection evidence)

The previously remembered upstream was `Hitbullets/codex-skills` (a single-commit,
condensed adaptation of both skills). A selection pass evaluated maintained
alternatives; the canonical upstreams are clearly superior:

- **`frontend-design`** — the original is **anthropics/skills** (official,
  actively maintained). It is richer than the condensation: design-lead framing,
  an explicit anti-cliché calibration pass, writing-in-design guidance, CSS
  specificity pitfalls, and self-critique. The `codex-skills` copy is a lighter
  derivative.
- **`ui-ux-pro-max`** — the current upstream is
  **nextlevelbuilder/ui-ux-pro-max-skill** (`v2.15.0`): 79 searchable styles,
  192 product/palette reasoning profiles, 74 font pairings, 119 UX guidelines,
  105 icons, 25 chart types, 22 stacks, a local stdlib-only search/design-system
  engine, and an official multi-platform installer that supports OpenCode. The
  `codex-skills` copy is a single-file condensation without the data engine.
- Rejected notable alternatives: `obra/superpowers` (a broad framework with
  plugins/hooks, not a focused UI/UX skill), `addyosmani/agent-skills`
  `frontend-ui-engineering` (strong engineering/a11y reference, but overlaps
  `ui-ux-pro-max` and under-emphasizes art direction), and the many
  low-activity/duplicate `frontend-design` forks.

### Installer note

The `ui-ux-pro-max` official installer's OpenCode profile installs several
sibling skills (`brand`, `design`, `design-system`, `slides`, `ui-styling`,
`banner-design`) in addition to `ui-ux-pro-max`. Per the mission, only the **two**
selected super-skills are kept; the siblings were removed after install so the
repository exposes exactly `frontend-design` and `ui-ux-pro-max`.

## Discovery (OpenCode)

OpenCode discovers project skills at `.opencode/skills/<name>/SKILL.md`
(and `.claude/skills/`, `.agents/skills/`). Each skill is loaded on demand via
the native `skill` tool. Validation rules:

- `SKILL.md` must be upper-case.
- `name` in frontmatter must match the containing directory.
- `description` is required (1–1024 chars).

Both installed skills satisfy these rules. A **new agent session is required**
for newly installed skills to appear in the available-skills list; a session
started before installation will not surface them.

`ui-ux-pro-max` additionally uses local Python 3 (standard library only) helper
scripts under its own directory. These scripts install nothing and make no
network calls; they are covered by the skill's own guidance not to modify the
host system.

## Update procedure

`frontend-design`:

1. Pick the new `anthropics/skills` commit SHA.
2. Re-download `skills/frontend-design/SKILL.md` and `LICENSE.txt` from that SHA.
3. Update the SHA and local hash in this file and in `SKILLS.lock.json`.
4. Re-run deterministic validation.

`ui-ux-pro-max`:

1. Choose a newer published `ui-ux-pro-max-cli` version.
2. Run `npx ui-ux-pro-max-cli@<version> init --ai opencode --offline` in the
   repository, then remove the sibling skills it installs so only
   `ui-ux-pro-max` remains.
3. Update the version, revision and local hash here and in `SKILLS.lock.json`.
4. Re-run deterministic validation.

## Licensing

- `frontend-design`: MIT, © Anthropic. Full text vendored at
  `.opencode/skills/frontend-design/LICENSE.txt`.
- `ui-ux-pro-max`: MIT, © NextLevelBuilder (repository `LICENSE`). Bundled data
  catalogs carry their own provenance (`data/data-provenance.json`,
  `data/google-font-licenses.json`).

## Boundaries

- No AXIGNAL product UI is implemented by installing these skills.
- No graph engine is selected.
- These skills recommend; they never override the MASTER, the Engineering
  Constitution, ADRs, or architecture contracts.
