# Research: Subscriber Experience Interaction Contracts

**Status**: Supporting research; not product or architecture authority.\
**Checked**: 2026-09-25

## Repository authority review

The candidate was reconciled against the MASTER Product Model, Engineering
Constitution, accepted ADRs (including ADR-0006 provider abstraction and
ADR-0008/0009/0010), Logical Architecture Atlas, Brain/Xeed Germination
architecture reference, Communication Strategy, Living Xeed appendix, Admin
Product Specification and documentation authority map. No material conflict
was identified. The subscriber proposal is subordinate to those sources and
does not authorize implementation. The Admin and subscriber projections remain
separate.

## External model facts

Mutable model/API/pricing claims were checked against official OpenAI API
documentation only:

- [GPT-6 Luna model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna)
- [API pricing](https://developers.openai.com/api/docs/pricing)
- [API changelog](https://developers.openai.com/api/docs/changelog)
- [Latest model guidance](https://developers.openai.com/api/docs/guides/latest-model)

The official materials list the identifier `gpt-6-luna`, Responses and Batch
support, function calling, structured outputs, 1,050,000 input context tokens
and a 128,000 maximum output. Standard short-context rates are $0.10/M input,
$0.01/M cached input and $0.50/M output. Cache writes have separate pricing.
Above 272K input tokens, input and cache rates are 2x and output rates are 1.5x
for the request. Batch and Flex are 50% of applicable Standard rates. These
claims are a dated operational snapshot; runtime policy and cost estimation
must use current provider documentation/pricing.

The request's division between provider policy and domain authority is
preserved: OpenAI/GPT-6 Luna is a current default mapping under cognitive roles,
not a permanent provider lock-in, canonical truth authority or AXIGLAND domain
concept. Model changes require representative evaluation.

## Design choices and non-goals

- One consolidated architecture contract carries the 15 required interaction
  contracts; the feature directory maintains traceability and conceptual data
  model without inventing endpoint or persistence schemas.
- UX and cognitive economics are expressed as interpretable measures. No
  aggregate WOW, truth or materiality score is defined.
- No production UI, API, model call, Batch job, Brain, JEV, Source Router,
  Product MCP, export runtime, dependency or database migration is included.
- Public documentation facts do not alter AXIGNAL's accepted architecture.
