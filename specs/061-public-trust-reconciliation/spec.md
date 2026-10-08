# 061 ? Public request channels: Contact and privacy rights

**Status:** IMPLEMENTED ? NOT ACTIVATED ? **Date:** 2026-10-08

## Authority

This slice is subordinate to MASTER, Constitution, ADRs and spec 060 Product Funnel.
It reconciles the preserved Codex backend with the UX contract established by spec 060.

## Goal

Provide real, private, non-canonical Contact and privacy-rights request channels without
turning AXIGNAL into a CRM and without claiming a channel is live before provider
authority is actually available.

## Public contract

- GET /api/contact/status
- GET /api/gdpr/status

Both return an enabled boolean plus the published controller boundary:
controller=AXIGNAL, country=Spain, and nullable publicEmail.
No public email is synthesized.

- POST /api/contact
- POST /api/privacy/request

A request is accepted only while the corresponding delivery integration is configured
and currently authorized by the governed integration registry. Success returns
status=received plus requestId. Rejection returns status=rejected plus a stable reason.

Every POST carries the notice version shown to the visitor. Contact/privacy input is
private service-operation data only: it is never AXIGLAND evidence, never tenant truth,
never newsletter consent and never a legal-resolution decision.

## Safety and persistence

Requests are validated, body-bounded, origin-checked, rate-limited, idempotent by
requestRef, persisted in a dedicated SQLite store and retained for 90 days.
Provider delivery uses a replaceable ContactDeliveryPort; the SMTP adapter requires
TLS plus existing governed integration authorization, healthy/fresh provider state,
email:send scope and a resolvable credential reference before secret read or network
transport.

If the channel is not authorized, status is disabled and POST fails closed before
persistence. Once a live channel accepts a request, durable receipt is authoritative
even if downstream provider delivery later fails; provider state remains private
operations data and is never exposed in the public receipt.

## Activation boundary

This code does not authorize or configure a provider. Production remains disabled until
an operator supplies approved SMTP configuration, registers/enables the integration,
provides a healthy/fresh health observation and publishes any verified public email.
No NIF, postal address, VAT number, registry data, DPO, telephone or email is invented.

## Funnel integration

Spec 060 owns narrative and presentation. Public forms must query status first and
remain hidden or unavailable when enabled=false. This slice exposes the backend and
edge contract only; visual wiring must preserve the Claude-owned funnel.
