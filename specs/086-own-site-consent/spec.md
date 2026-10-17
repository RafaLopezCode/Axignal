# Feature Specification: An owner's verified consent to keep its own public website

**Created**: 2026-10-17

**Status**: Draft for CTO review. No code until accepted, because it amends ADR-0091 §11.

**Input**: CTO, 2026-10-17. After the biocultor.com canary needed a content-rights entry added by hand on the server: "¿Los avances y correcciones son para todas las cuentas o estás arreglando solo Biocultor?" … "Ok" (to designing owner consent as a spec first).

## Problem
To keep a website's public pages as evidence, AXIGNAL needs a governed content-rights decision (ADR-0091 §11, ADR-0015). Seeding the Organization, sharing a reading across tenants, sending text to an evaluator and feeding the daily loop all depend on it.

Today only the operator can register that decision, by hand, in a file on the server, and none exists by default. That works for one canary and fails for hundreds of subscribers. The most common case is also the most legitimate: **a subscriber observing its own organization** wants AXIGNAL to keep and read its own public website.

## Principle
An organization may authorize AXIGNAL to keep and read **its own** public website, but only if it proves it controls that website.

The consent is **authority over content**, never truth:
- it does not verify identity: a web-anchored subject stays web-anchored, and only a registry verifies identity;
- it does not change any epistemic state;
- it does not mutate canonical facts (MASTER §182, AGENTS hard rule: input directs attention only).

Third-party websites (competitors, clients, any site the subscriber does not control) are unchanged: they are observed under robots.txt and not retained without an operator decision.

## User journey
1. On a Focus whose website the subscriber says it controls, an action reads: **"Autoriza a AXIGNAL a conservar y leer tu web"**. It explains what is kept, for how long, what the evaluator receives and how to revoke.
2. AXIGNAL issues a **verification token** bound to the tenant, the principal and the host. It is single-use and expires in 7 days.
3. The subscriber proves control **in one of three ways**, the same model as Google Search Console:
   - DNS TXT record `axignal-site-verification=<token>` on the host or its registrable domain;
   - `<meta name="axignal-site-verification" content="<token>">` on the homepage;
   - `https://<host>/.well-known/axignal-verification.txt` containing the token.
4. The subscriber accepts a **versioned consent text**, with two separate choices:
   - **(a)** keep and reuse the public pages as evidence (required);
   - **(b)** let the semantic evaluator read their public text (optional; ADR-0090 input rights).
5. AXIGNAL checks the proof (one bounded request, under robots for the HTTP methods) and records the consent.
6. The Focus shows the status ("Autorizada · verificada por DNS el 17 oct · revocar"). The next observation keeps the pages; no hand-made file is needed.

## What is recorded (append-only consent ledger, never edited)
- The consent id, tenant, principal, host (plus `www.`) and consent text version.
- The verification method, `verified_at`, the token's fingerprint (never the token) and the evidence location.
- The choices: reuse/retention (always), evaluator input (yes or no) and public-offer input.
- Retention: raw 90 days and metadata 365 days by default, never above the policy's ceiling.
- Revocation: `revoked_at` and the reason, either the subscriber or a lapsed proof.

## How it becomes authority
- A consent produces the same governed `SourceRegistryEntry` an operator would register:
  - rights `PERMITTED`;
  - basis `FIRST_PARTY_CONSENT:<consent id>`;
  - scope as for operator entries;
  - the recorded retention.
- The live rights policy reads **operator entries and consents together**. An operator decision always wins: a `PROHIBITED` or `INACCESSIBLE` entry for a host overrides any consent.
- Everything ADR-0091 §11 already guarantees applies unchanged:
  - the decision is taken again at every use;
  - lost rights purge shared content before any reuse;
  - seeds carry the rights, scope, provenance and retention references;
  - private citations are capped.

## Keeping it true
- **Re-verification every 90 days.** If the DNS record, meta tag or file is gone, the consent lapses. AXIGNAL warns the subscriber 14 days before.
- **Revocation at any time** from the Focus. It lapses immediately and the existing purge runs.
- **The subscriber leaving AXIGNAL or removing the Focus** also lapses the consent.
- A lapsed consent never deletes economic history already admitted under it. Only retained raw content is purged, per policy (ADR-0091 §11).

## Not in scope
- Consent for third-party websites. Agencies acting for a client are a later decision for the CTO; they would need the client's own proof.
- Private first-party analytics (Search Console, GA). They stay private, as ADR-0015 and MASTER §54 require.
- Any change to identity verification or to the registry path.

## Doctrine changes required
- **ADR-0091 §11:** "registered by the operator; none exists by default" becomes "registered by the operator, **or by the website's controller through verified first-party consent (spec 086)**; none exists by default". See the proposed amendment in this PR.
- **MASTER:** none required, in my reading. Consent is authority over observation inputs, not a canonical fact, and the subscriber's input still only directs attention. The CTO confirms.

## Decisions for the CTO
1. **Verification methods:** all three (DNS, meta tag, file), or DNS only for the first version?
2. **Retention defaults:** raw 90 days, metadata 365 days?
3. **Evaluator input as a separate, optional choice:** recommended (ADR-0090 input rights).
4. **Consent text:** it needs legal review before release (GDPR: public pages may contain personal data). Today the evaluator already receives text with contact data and sentences about people removed.
5. **Biocultor:** keep the hand-made operator entry, or replace it with a consent once this ships?

## Success criteria
- **SC-001:** a subscriber authorizes its own site without operator action, and the next observation seeds it (ledger: rights by `FIRST_PARTY_CONSENT`).
- **SC-002:** consent for a site the subscriber does not control is impossible. The verification fails and nothing is recorded as permitted.
- **SC-003:** revocation or a lapsed proof purges retained content before any reuse, and no economic history is deleted.
- **SC-004:** an operator `PROHIBITED` entry overrides any consent.
