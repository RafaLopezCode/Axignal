# Clarifications

2026-10-06: Root found no durable canonical Organization reader for subscriber
composition. Existing identity governance handles merge/split but not admitted
legal-name materialization. This additive boundary stores an exact admitted name,
not a subscriber profile and not an automatic registry-search result.
`legal_identity` object is the exact legal name in the evidence; a registration
number alone cannot be repurposed as that name. Registry acquisition remains an
independently governed capability, never a claimed completed live observation.

2026-10-07 (ADR-0087): Subscriber locators may also carry a public website or an LEI.
A website resolves only through a registry-recorded `official_website` admission; a
site describing itself is never identity evidence. The OrganizationId is derived from
the registry identifier so concurrent or repeated admissions converge. Without a
configured registry source, unknown identities remain pending with an explicit reason.
