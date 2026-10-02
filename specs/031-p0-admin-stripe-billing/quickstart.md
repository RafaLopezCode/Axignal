# AO-10 implementation notes

Stripe provider ingress is deliberately disabled unless all four runtime values are present: merchant account ID, base price reference, additional-Xeed price reference and webhook signing secret. The signing secret is injected by deployment and is never committed.

The currently connected AXIGNAL Stripe account is a live merchant context, so this implementation does not perform live writes. Use a real Stripe sandbox/test context for external E2E before live enablement.
