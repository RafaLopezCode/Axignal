# Presentation data model
All sample economics are FIXTURE_ONLY. This file creates no domain entities.
- Organization: id, human name, sector. Economic subject; does not own canonical world.
- Focus: id, organizationId, persistent attention status. Private allocation separate from Organization.
- Snapshot: asOf date, title; included signals satisfy availableFrom <= asOf. Explicit missing historical knowledge.
- Signal: id, family, organizationId, human title/summary, epistemic OBSERVED/POTENTIAL/UNKNOWN, eventAt, detectedAt, availableFrom, evidence IDs, limitation, derivation, attention.
- Evidence: id, source label, publishedAt, observedAt, description, basis, limitations, sample/instrument when applicable. Demo local source route; no fabricated external source URL.
- ProjectionContext: organizationId, family, signalId?, asOf, revision; scope validated against known demo options. No arbitrary client tenant identifiers.
- CompositionPlan: version 1; context revision must match; 1..3 items; registered component enum signal/evidence/context; reference IDs must be in authorized projection; no duplicate references; priority enum primary/supporting; output strings/HTML are not component props.
- AdminReadModel: operational domain, record, owning service, illustration label, command authorization requirement. Read models are not economic facts.
- Navigation, time, evidence and chat records are distinct. URL is presentation state, not evidence.
