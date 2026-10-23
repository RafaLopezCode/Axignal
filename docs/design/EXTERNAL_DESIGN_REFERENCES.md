# Additional design references — 2026-10-15

These user-requested tools are advisory design intelligence. The MASTER,
Constitution, ADRs, contracts, active design brief and accepted AXIGNAL visual
evidence retain precedence. Installation makes no application or canvas change.

| Resource | Reviewed revision | Project use |
| --- | --- | --- |
| [Taste Skill](https://github.com/Leonxlnx/taste-skill/tree/f624f37a8c650b9cc550253104925efe4c8de246/skills/taste-skill) | `f624f37a8c650b9cc550253104925efe4c8de246` | Primary `design-taste-frontend` skill only. Upstream targets public pages and explicitly excludes dashboards and app screens. |
| [Web Design Guidelines](https://github.com/vercel-labs/agent-skills/tree/063bee94c3f4df8453406c830b0a7df0f2860278/skills/web-design-guidelines) | `063bee94c3f4df8453406c830b0a7df0f2860278` | `web-design-guidelines` skill for focused accessibility and interaction reviews. |
| [Awesome DESIGN.md](https://github.com/VoltAgent/awesome-design-md/tree/3b605329240ce735b510037cca322f1831fdd7f8) | `3b605329240ce735b510037cca322f1831fdd7f8` | Reference catalog; contains brand analyses, not an installable `SKILL.md`. No brand was selected or imported. |

Both skills have shared upstream content under
`.opencode/skills/<name>/`. Codex discovers thin entrypoints under
`.agents/skills/<name>/SKILL.md`; Claude Code discovers equivalent entrypoints
under `.claude/skills/<name>/SKILL.md`. Agent sessions may need to refresh before
the new skills appear. Existing skills retain their existing discovery paths.

The installation used `skills@1.7.2` from `vercel-labs/skills`, with npm lifecycle
scripts and installer telemetry disabled. Pinned GitHub blob snapshots were
downloaded as ordinary files, reviewed and passed to the CLI as local sources.
Only the selected skill directories were installed. The CLI's generated local
staging lock is replaced by the durable upstream revisions and file hashes in
`SKILLS.lock.json`; future updates must repeat review and refresh those hashes.

Taste Skill includes optional Node scripts, reference data and browser helpers.
Installation does not execute those helpers. Its asset helper uses public image
APIs without credentials; its inspector launches a separate Chromium profile.
Use host browser tools when required by the agent environment. Neither helper
becomes an application or required CI dependency. Upstream style rules and
generated directions remain subordinate to AXIGNAL's accepted design authority.

Web Design Guidelines is Markdown only, but its review instructions fetch the
latest Vercel guidelines. The pinned skill revision does not pin those remote
rules: record the source revision when using them as review evidence. Network
access follows normal task permissions and never becomes a required CI gate.

Taste Skill and Awesome DESIGN.md declare MIT licensing. The reviewed
`vercel-labs/agent-skills` revision does not declare a repository license; no
license is inferred from the separately maintained Web Interface Guidelines
repository. Provenance and this limitation are recorded in the toolchain lock.
