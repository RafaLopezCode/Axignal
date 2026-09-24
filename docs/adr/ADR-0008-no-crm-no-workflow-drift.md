# ADR-0008: No CRM / No Workflow Drift

- **Status:** Accepted
- **Date:** 2026-09-24
- **Source doctrine:** MASTER §2.1, §22, §32, §38, §46.2, §46.35, §46.37, §46.38, §48

## Context

Product gravity pulls observation tools toward becoming CRMs, workflow suites or
business social networks. Each such feature adds participation dependencies,
moderation and poisoning surface, and moves AXIGNAL away from mapping the real
economy.

## Decision

AXIGNAL stops at explainable economic knowledge. Pipeline, tasks, tickets,
messaging, invoicing, negotiation, escrow, workflow engines and sponsored truth
are out of scope. Integrations are thin (API, webhooks, export, share) and must
not turn AXIGNAL into HubSpot, Salesforce, Pipedrive, Slack, Notion, n8n, Make or
Zapier. Advertising, if ever present, must be structurally separate from the
map.

## Consequences

- No `crm`/`workflow` packages in the core.
- Any such feature requires an explicit CTO change to the MASTER first.

## Enforcement

- Architecture Guard rule `FORBIDDEN_DOMAIN_PACKAGE`.
- `tests/architecture/test_architecture_guard.py` negative tests.
- `AGENTS.md` instructs agents to stop and report on conflict.
