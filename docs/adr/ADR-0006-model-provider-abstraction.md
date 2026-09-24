# ADR-0006: Model Provider Abstraction

- **Status:** Accepted
- **Date:** 2026-09-24
- **Source doctrine:** MASTER §13, §14, §30, §31.2, §43.2, §43.3, §46.28, §46.29, §46.31

## Context

Foundation models and JEV evolve quickly. If AXIGNAL's domain depends directly on
one provider SDK, a provider change or a dominant model owner can destroy the
product.

## Decision

The domain is provider-agnostic. `AXENT` is a product/domain object; the model is
a replaceable component reached through `ModelRouter` and a `CognitiveProvider`
interface. Concrete SDKs and provider-specific logic live only under
`cognition/providers/`. A model's structured output is never canonical truth.

## Consequences

- Model Swap Test and Model Upgrade Test are structurally supported.
- The domain cannot hard-wire to Luna, GPT, DeepSeek, or any vendor.
- JEV is likewise replaceable.

## Enforcement

- Architecture Guard rules `PROVIDER_SDK_IMPORT` and `PROVIDER_CANONICAL_WRITE`.
- `tests/contracts/test_provider_abstraction.py`.
- `cognition/providers/echo.py` demonstrates the adapter boundary offline.
