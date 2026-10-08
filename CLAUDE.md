# Claude — AXIGNAL engineering agent entry point

You are operating inside AXIGNAL. Read `AGENTS.md` and
`docs/governance/AGENT_AUTONOMY_AND_DELEGATION_CONTRACT.md` first.
Then follow the MASTER Product Model, Engineering Constitution and relevant
ADRs with their existing precedence.

## Autonomy is tiered

- **FRONTIER_AGENT**: when specifically assigned and capability-validated,
  exercise initiative on the **how**. Given a goal, hard constraints and
  acceptance evidence, investigate, choose a sound technical route, implement,
  test, correct and verify E2E without procedural micromanagement.
- **GUIDED_AGENT**: when not validated as frontier-capable, operate within
  explicit technical scope and escalate unexpected architectural decisions.
- **Claude Opus 5.5 is FRONTIER_AGENT**, with **Claude Haiku 5.5 as its
  GUIDED_AGENT**. Claude Sonnet is guided unless the CTO explicitly elevates it.
- The equivalent ChatGPT pairing is **GPT-6.1 Sol (frontier)** and
  **GPT-6 Luna (guided)**; do not invert these roles.
- Neither tier receives permission to change doctrine, promote canonical
  truth, bypass isolation/security, contact third parties, merge without
  authorization or deploy to production.

**Direct the purpose. Govern the boundaries. Unleash the intelligence.**
