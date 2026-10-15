# Admin transport hardening and frontend regression gates

## Problem and scope

The Admin review exposed inconsistent transport handling. Marketing reads an
entire request before checking a character count; several Admin proxies parse
unbounded upstream JSON, and their shared catch block mistakes upstream syntax
failures for invalid user input. CI validates Python but omits the existing
frontend tests, TypeScript, translations and production build.

The user requested detection and repair of technical debt with regression
protection. This slice repairs these evidenced defects. It preserves real-data
sources, command schemas, origin checks, HttpOnly credentials, primary/step-up
pairing, scopes and owner-service authority. The shared AXIGNAL tool and canvas,
provider activation, production deployment and executive metric producers are
outside scope. No new dependency or synthetic operational fallback is permitted.

## Acceptance and clarification

- Bound Admin commands by their existing byte limits, before full buffering.
  Exceeding a limit cancels the stream and returns 413 without contacting the
  owning service; non-ASCII data cannot bypass the byte limit.
- Bound upstream JSON and legacy projection payloads to 1 MiB. Corrupt, oversized
  or unreadable successful upstream bodies produce a generic 502, not a
  user-input 400. Known denial statuses remain denied even if their error body
  is unreadable; arbitrary error details are never forwarded to the browser.
- Valid payloads preserve existing response shapes, reason allowlists, status
  codes, private response headers and JSON/legacy migration behavior.
- Always release reader locks; cancellation failures cannot mask a known limit
  failure or leak an upstream body into an error message.
- Test the failure cases before and after the change using deterministic streams
  and HTTP requests. Test fixtures are regression inputs, never live UI data.
- CI runs the existing frontend tests, TypeScript, i18n inventory and production
  build using the same Node major as the experience Docker image (22), locked
  dependencies and no model/API key. Existing required gates remain intact.
- Do not claim impossibility of regressions. Report evidence and residual risk.
