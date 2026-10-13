# Plan and architecture review

Graphify consulted before architecture work. Application owns profile commands and provider-neutral billing management; pipeline owns SQLite persistence, raster sanitizer and Stripe transport; tools compose authenticated HTTP services; Next routes proxy strictly bounded same-origin requests. Profile store has no canonical writer imports. No generic PATCH endpoint or customer identity supplied by browser. Existing session resolver/purchase owner authorizes operations.

Pillow is locked in subscriber-auth (already included in dev and subscriber-runtime Docker); decoding imported lazily by image adapter. File bytes remain private SQLite data, not public object URLs; upload response is normalized bounded PNG only. Profile reads are private/no-store. LocaleProvider reads principal preference through authenticated endpoint and only reports successful persistence after server acknowledgement. Account-only profile panel mounts in the actual account source; not in demo/Admin.

Stripe Customer portal: verified restricted configuration permits payment-method update, invoice history, period-end cancellation, denies plan/quantity update. Session creation is distinct from cancellation confirmation; provider errors never become success. Official portal docs consulted. No live account changes in development.

Constitution check passes: Principal/Tenant/Organization/billing separated, no roles inferred from membership, no canonical write, no UNKNOWN coercion, no provider coupling in domain, no new LLM/network CI gate.
