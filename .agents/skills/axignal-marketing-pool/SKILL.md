---
name: axignal-marketing-pool
description: Launch, follow and cancel AXIGNAL marketing campaigns, and review the marketing pool. Use when the user asks to start a campaign ("lanza una campaña de 50 agencias SEO en Canadá"), to see how the pool or a campaign is going, to review drafts, or to tune buyer personas or countries. The pool runs on its own (automatic mode); a campaign directs it. Agents never approve or send emails.
---

# AXIGNAL marketing pool — agent protocol

The pool is a **runtime**. It always runs on its own when enabled:

- **Automatic mode** (no active campaign): it rotates buyer personas and countries,
  open-channel markets first, and favours the persona × country pairs that have qualified
  best so far (it learns from its own history).
- **Campaign mode**: while a campaign is active, it gets the whole daily study budget for
  its personas and countries, until it reaches its target, its end date, or runs out of
  candidates. Then the pool returns to automatic mode by itself.

```
discover → study (once per domain, ever) → qualify → draft in its language
  → DRAFTED | HELD (country channel policy / no role address) | NOT_QUALIFIED
  → a person approves in Admin › Clients and access › Marketing pool → SENT
```

## 1. Launch a campaign from a request

Turn the user's words into a campaign, then **confirm with the user before running it**
(it is a production write):

| Field | Values |
|---|---|
| name | short, e.g. `SEO Canadá Q4` |
| personas | `SEO_GEO_AGENCY`, `DIGITAL_MARKETING_AGENCY`, `REPUTATION_PR_AGENCY`, `CONSTRUCTION`, `PRIVATE_SCHOOL`, `B2B_CONSULTANCY` |
| countries | ISO codes listed in `application/marketing_pool/policy.py` (`MARKETS`) |
| target | organizations to **study**, 1–500 (not emails: some will not qualify) |
| ends-on | optional `YYYY-MM-DD` |

Tell the user, before confirming, which chosen countries are **HOLD** in the channel
policy (e.g. ES, DE, IT): they are studied and drafted but **not emailed**.

Run it in production (the runtime container, its data directory):

```bash
ssh axignal-production "docker exec axignal-prod-runtime python -m tools.runtime.marketing_pool \
  campaign-create --data-dir /var/lib/axignal/runtime --name 'SEO Canadá Q4' \
  --personas SEO_GEO_AGENCY --countries CA,US --target 50 --ends-on 2026-11-30 \
  --actor claude:rafael"
```

`--actor` is mandatory and audited: `<agent>:<person who asked>` (`codex:…`, `claude:…`).
The answer is the campaign id. Cancel with `campaign-cancel <id> --data-dir … --actor …`.

### Segments and playbooks

Each persona belongs to a segment with its own playbook
(`application/marketing_pool/playbooks.py`): AGENCY (SEO/GEO, digital marketing, PR),
CONSTRUCTION, PRIVATE_SCHOOL, CONSULTANCY. A playbook fixes the hooks that may open the
letter (usually an INXIGHT crossing), the order of evidence, the pain and its own call
to action. A prospect without a hook waits up to 3 days for background measurements and
is then NOT_QUALIFIED (`NO_SEGMENT_HOOK`): no generic letters.

## 2. Report progress

```bash
ssh axignal-production "docker exec axignal-prod-runtime python -m tools.runtime.marketing_pool \
  status --data-dir /var/lib/axignal/runtime"
```

Report per campaign: found, studied, qualified, drafts waiting for approval, sent, held,
opt-outs; and remind the user that drafts wait in Admin for their approval.
`drafts` lists drafts waiting; `show <domain>` shows one prospect.

## 3. Review drafts (read-only)

Check that each draft cites only its findings, phrases POTENTIAL as possibility, reads
naturally in its language and claims nothing about the recipient's needs. Report the
domain and the sentence; never edit the database.

## 4. Improve the system (PR with tests)

Personas `application/marketing_pool/personas.py` (bump `PERSONAS_VERSION`), countries and
channel policy `application/marketing_pool/policy.py` (bump `CHANNEL_POLICY_VERSION`),
email `application/marketing_pool/email_template.py`, gate and drafting
`application/marketing_pool/prospect.py`.

## Never

- Approve, send, or bypass approval; `APPROVE` is a human Admin decision.
- Change a country from HOLD to EMAIL without a reviewed legal basis recorded by the
  operator (the policy is conservative, not legal advice).
- Contact, un-suppress or re-add a suppressed domain or address.
- Scrape search engines, maps or social networks, bypass robots.txt, or collect personal
  addresses (only role addresses the organization publishes on its own domain).
- Write a prospect into AXIGLAND (`AXIGNAL CRM LEAD != AXIGLAND ORGANIZATION STATE`).
- Hard-wire a model provider (drafting goes through `cognition/router`).

## Configuration (runtime settings file; off by default)

| Key | Meaning |
|---|---|
| `AXIGNAL_MARKETING_POOL_ENABLED=true` | the pool runs (discovery, studies, drafts) |
| `AXIGNAL_MARKETING_POOL_STUDIES_PER_DAY` | default 12 |
| `AXIGNAL_MARKETING_POOL_SIGNATURE` / `_SIGNATURE_ROLE` | `Rafael López` / `CEO` |
| `AXIGNAL_MARKETING_POOL_SEND=true` | sending allowed (still only after approval) |
| `AXIGNAL_MARKETING_POOL_SMTP_FROM` | e.g. `hola@axignal.com` |
| `AXIGNAL_MARKETING_POOL_SMTP_HOST` / `_PORT` / `_USER` | default `smtp.hostinger.com` / `465` / the from address |
| `AXIGNAL_MARKETING_POOL_SMTP_PASSWORD_FILE` | absolute path of a root-owned secret file |
| `AXIGNAL_MARKETING_POOL_SENDS_PER_DAY` | default 20 |

Sending also requires `AXIGNAL_LEGAL_ADDRESS` and SPF, DKIM and DMARC on the domain.
