# AO-12 data model

## MarketingEvent
- immutable event ID;
- occurred/received timestamps;
- event kind;
- identity class: ANONYMOUS_SESSION or BRIEF_REQUEST;
- random session ref;
- surface, locale, path-only location;
- optional request ID only for BRIEF_REQUEST link event;
- optional chapter / stable CTA;
- referrer origin only;
- optional bounded UTM source/medium/campaign/content/term;
- attribution model version.

## MarketingAttributionSummary
- model version;
- event count;
- anonymous session count;
- linked request count;
- source counts;
- campaign counts.

No IP, user-agent, cookie, fingerprint, email, person name, company identity or free-text purpose belongs to MarketingEvent.
