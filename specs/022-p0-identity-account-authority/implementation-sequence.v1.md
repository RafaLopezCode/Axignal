# Conditional Implementation Sequence

This order is planning guidance only. Q2 authorizes no runtime.

1. Resolve provider/data-location/session requirements and select an auth provider in a separate decision. Keep the domain port provider-independent.
2. Define a deterministic verified-external-identity → Principal mapping contract and tests. Do not add provider IDs to domain types.
3. Implement an adapter that establishes authenticated Principal context, then retain the existing membership-first AuthorizedXeed checks. Do not add membership roles or writers without separate authority.
4. Implement the password path with verified email, mandatory TOTP enrollment, and provider-owned recovery codes; keep credential creation separable from TOTP enrollment. Preserve the Google-first path without AXIGNAL-managed TOTP for P0.
5. Resolve payer/cardinality and Xignal-capacity mapping before billing or entitlement persistence. A Tenant consumption scope does not make Tenant the payer.
6. Define the provider-independent entitlement decision and its UNKNOWN behavior before consuming paid capacity.
7. Implement only Principal-owned preferences needed by approved Settings fields; UI-locale catalog/fallback and device-vs-account scope are presentation decisions.
8. Reconcile Settings against finalized field owners and authorized commands; defer Tenant/Workspace settings until product authority exists.
9. Define membership, offboarding, private-history, account, Tenant, Xeed, and billing retention/deletion policies before lifecycle writers.

Authentication, Settings, persistence, and billing remain separate reviewed slices. Payer or profile gaps do not change current canonical Xeed authorization or grant Organization writes.
