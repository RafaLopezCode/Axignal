# Presentation data only
EditorialArticle: slug, topic, bilingual title/deck/sections/takeaway, doctrine source link, illustration kind. Minutes computed from body words. No artificial publish dates, bylines, views or score.
PolicyDocument: slug, bilingual title/sections, draft=true; unknown operator data is explicit text, not fabricated placeholders.
LocalDraft: topic/right, name, email, message; validated client-side and exact preview/download; ephemeral React state only. No network mutation.
AuthStartRequest: provider enum google/openai, intent enum login/signup. Strict schema; no scopes, identity, return URLs or role claims from caller.
AuthStartOutcome: UNAVAILABLE, HTTP503; verified=false, sessionCreated=false. Production AuthenticationPort/Principal mapping remains deferred. No storage or cookie.

Locale: closed enum es/en/de/pt/fr/it; six-language presentation catalog of 912 unique English keys, each with four additional translations. Canonical object references and economic states do not depend on locale. Original doctrine quotations retain their source language. Locale preference key axignal.locale.v1 stores only a valid language identifier; invalid values are ignored.
PrivacyPreference: key axignal.privacy-notice.v1, dismissedAt timestamp only, expires after 180 days. It records notice acknowledgement, not legal consent, account registration or optional tracking permission. Page drafts are never persisted.
ReferencePricing: 1..100 integer observation allocations; cents = 995 + 495 * (n - 1), presentation only. Human advisory scope and launch price are a separate service. No checkout or billing authority.
ObserverPose: viewBox and clipping mask referencing the unchanged human-supplied action sheet; masks exclude surrounding editorial annotations and pose captions. No source raster or canonical isotope alteration.
