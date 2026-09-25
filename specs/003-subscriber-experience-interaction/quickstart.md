# Contract Review Quickstart

This guide is for reviewing the specification, not running a product runtime.

1. Read [the candidate product specification](../../docs/product/AXIGNAL_SUBSCRIBER_EXPERIENCE_ASK_AXENT_PRODUCT_SPEC.md)
   and confirm its metadata is `0.1`, `PROPOSED`,
   `PRE_IMPLEMENTATION`, class `PRODUCT_INTERACTION_SPECIFICATION`.
2. Read [the architecture contract](../../docs/architecture/AXIGNAL_SUBSCRIBER_EXPERIENCE_INTERACTION_ARCHITECTURE_V0.1.md)
   and [the detailed contract catalogue](contracts/interaction-contracts.md).
3. Trace each FR in [spec.md](spec.md) to a numbered contract. Review producer,
   consumer, authority, success, unknown/failure and authorization semantics.
4. Walk these paper scenarios:
   - authorized subscriber opens Today with one new, one stale and one
     contradictory candidate;
   - germination worker is still discovering while one safe discovery is
     already displayable;
   - Ask AXENT receives an out-of-scope question requiring new evidence;
   - subscriber challenges a material claim;
   - Product MCP request is unauthorized and an export uses an earlier
     projection version;
   - actual model cost is unavailable.
5. Confirm each outcome remains distinct and no scenario promotes model output,
   user input or projection into canonical authority.
6. For implementation-time model budgeting, recheck official [model](https://developers.openai.com/api/docs/models/gpt-6-luna)
   and [pricing](https://developers.openai.com/api/docs/pricing) documentation.

No sample runtime, model request, database schema, or UI is created by this
quickstart.
