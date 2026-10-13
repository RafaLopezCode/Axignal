---
name: axignal-marketing-pool
description: Protocol for Codex or Claude to operate, review and improve AXIGNAL's own marketing pool (autonomous discovery of agencies and consultancies worldwide, one evidence-backed study each, personalized email drafts in the organization's language, sent only after Admin approval). Use when asked to check the pool, review drafts, tune buyer personas, add a country, or diagnose why prospects are held or not qualified.
---

# AXIGNAL marketing pool — agent protocol

The pool is a **runtime**, not a script an agent drives. Once enabled it runs on its own in
the First Observation background loop:

```
discover (OpenStreetMap + Wikidata, per persona and country, never the same domain twice)
  → study (governed First Observation under the staff tenant `staff:marketing-pool`)
  → qualify (persona evidenced on its own site; ≥4 sourced findings in ≥3 families)
  → draft (cognition/router, JobKind.OUTREACH_DRAFT, in the site's language, citing findings)
  → DRAFTED | HELD (country channel policy, or no role address) | NOT_QUALIFIED
  → a person approves in Admin › Clients and access › Marketing pool
  → SENT (SMTP, daily cap, List-Unsubscribe one-click) → opt-out = permanent suppression
```

## What an agent may do

1. **Inspect, read-only.** On a host with the data directory:
   `python -m tools.runtime.marketing_pool status --data-dir <dir>`
   `python -m tools.runtime.marketing_pool drafts --data-dir <dir>`
   `python -m tools.runtime.marketing_pool show <domain> --data-dir <dir>`
   In production this is read-only SSH inspection only; never edit the SQLite file.
2. **Review draft quality** and report: does each email cite only its findings, phrase
   POTENTIAL as possibility, read naturally in its language, avoid claims about the
   recipient's needs? Report problems with the domain and the sentence.
3. **Improve the system through a PR**, with tests: buyer personas
   (`application/marketing_pool/personas.py`, bump `PERSONAS_VERSION`), country rotation
   and channel policy (`application/marketing_pool/policy.py`, bump
   `CHANNEL_POLICY_VERSION`), the email template
   (`application/marketing_pool/email_template.py`), the quality gate and drafting
   contract (`application/marketing_pool/prospect.py`).

## What an agent must never do

- Approve, send, or bypass the approval: `APPROVE` is a human Admin decision.
- Change a country from HOLD to EMAIL without the operator recording a reviewed legal
  basis in the policy (`basis` text) — the policy is conservative, not legal advice.
- Contact a suppressed domain or address, remove a suppression, or re-add a domain.
- Scrape search engines, maps or social networks, bypass robots.txt or anti-bot, or
  collect personal addresses: only role addresses the organization publishes on its own
  domain (`recipient()` enforces it).
- Write a prospect, lead or study into AXIGLAND, or treat it as an Organization, FAXT or
  Relationship (Admin §5.7: AXIGNAL CRM LEAD != AXIGLAND ORGANIZATION STATE).
- Hard-wire a model provider: drafting goes through `cognition/router`.

## Configuration (runtime settings file, all optional, off by default)

| Key | Meaning |
|---|---|
| `AXIGNAL_MARKETING_POOL_ENABLED=true` | discovery, studies and drafts run |
| `AXIGNAL_MARKETING_POOL_STUDIES_PER_DAY` | default 12 |
| `AXIGNAL_MARKETING_POOL_SIGNATURE` / `_SIGNATURE_ROLE` | e.g. `Rafael López` / `CEO` |
| `AXIGNAL_MARKETING_POOL_SEND=true` | sending allowed (still needs approval) |
| `AXIGNAL_MARKETING_POOL_SMTP_FROM` | e.g. `hola@axignal.com` |
| `AXIGNAL_MARKETING_POOL_SMTP_HOST` / `_PORT` / `_USER` | default `smtp.hostinger.com` / `465` / the from address |
| `AXIGNAL_MARKETING_POOL_SMTP_PASSWORD_FILE` | absolute path of a root-owned secret file |
| `AXIGNAL_MARKETING_POOL_SENDS_PER_DAY` | default 20 |

The sender also requires `AXIGNAL_LEGAL_ADDRESS` (identity and postal address in every
message) and SPF, DKIM and DMARC published for the sending domain.
