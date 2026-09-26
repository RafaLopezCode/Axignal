# ADR-0012: Economic Opportunity Intelligence Is a Core AXIGNAL Capability

**Status:** Accepted product doctrine; no implementation authorized by this ADR.\
**Date:** 2026-09-26\
**MASTER:** §46, §53

## Context

AXIGNAL's economic map and evidence-backed observation are cognitive
substrate. The product must interpret observable activity and explain what
may deserve attention without turning possible economic fit into canonical
fact, customer management, or an unsupported lead. A jurisdiction- or
portal-specific design would make the product's economic coverage narrower
than its doctrine and would confuse observed activity with a relationship.

## Decision

1. Economic Opportunity Intelligence is a core AXIGNAL capability. It
   interprets economic activity and demand against observed or justified
   capabilities and explains relevance, temporal context, uncertainty and
   evidence.
2. Latent demand is distinct from materialized economic demand. General
   demand, project, procurement and awarded-project signals are conceptual
   signal families. Project and procurement activity can show materialized
   activity without proving a customer, lead or relationship.
3. Global Economic Sensors and sensor discovery/registry are core product
   concepts. TED is one possible sensor example, not a privileged source,
   architecture or domain. No source-specific domain object follows from
   this decision.
4. Geography is reasoning context. Home jurisdiction does not define an
   organization's total market. Economic Reach is capability-specific and
   may be observed, potential or unknown. Sensor routing considers the
   relevant capability, justified reach and activity geography.
5. An opportunity is a derived, plausible, temporal and explainable
   compatibility between demand/activity and capabilities. It is not a
   FAXT, customer, lead, purchase or observed relationship. Its default
   epistemic class is `POTENTIAL`.
6. Procurement does not imply a customer or relationship; an award does
   not imply a subcontract; capability match does not imply commercial fit.
   An explainable Opportunity PATHX is a constituent route, not a direct
   relationship between path endpoints.
7. Opportunity reasoning uses inspectable typed dimensions and temporal
   context. No universal opaque opportunity score is authorized. Every
   surfaced opportunity requires a persistent explanation trace. No
   opportunity is preferable to a fabricated one.
8. These concepts do not create runtime classes, source integrations,
   crawlers, schemas, production behavior or provider authorization.

## Required invariants

```text
ECONOMIC_OPPORTUNITY_INTELLIGENCE=CORE
LATENT_DEMAND_DISTINCT_FROM_MATERIALIZED_DEMAND
PROJECT_PROCUREMENT_SIGNALS=CORE_SIGNAL_FAMILY
GLOBAL_ECONOMIC_SENSORS=CORE
TED_IS_EXAMPLE_NOT_DOMAIN
GEOGRAPHY_IS_REASONING_CONTEXT
ECONOMIC_REACH_IS_CAPABILITY_SPECIFIC
HOME_JURISDICTION_IS_NOT_MARKET_BOUNDARY
SENSOR_ROUTING_IS_CAPABILITY_AND_REACH_AWARE
OPPORTUNITY_IS_DERIVED
OPPORTUNITY_IS_NOT_FAXT
OPPORTUNITY_IS_NOT_CUSTOMER
OPPORTUNITY_IS_NOT_LEAD
PROCUREMENT_DOES_NOT_IMPLY_RELATIONSHIP
AWARD_DOES_NOT_IMPLY_SUBCONTRACT
OPPORTUNITY_REQUIRES_EXPLANATION_TRACE
OPPORTUNITY_REQUIRES_TEMPORAL_CONTEXT
NO_OPPORTUNITY_IS_BETTER_THAN_FAKE_OPPORTUNITY
```

## Alternatives considered

- Treat the economic map or a directory as the final product: rejected;
  mapping is the cognitive substrate, while explainable economic
  intelligence is the product.
- Treat procurement publication as a lead or relationship: rejected;
  activity and relationship have distinct evidence requirements.
- Make a particular portal or home jurisdiction the market boundary:
  rejected; sensors and reach must be selected for the economic question
  and relevant capability.
- Reduce opportunity to a single score: rejected; it hides distinct
  requirements, uncertainty and temporal evidence.

## Consequences and tradeoffs

Product, communication and subscriber experience documents must describe
opportunity as derived and explainable while preserving the no-CRM boundary.
This increases semantic discipline and makes unsupported opportunities
explicitly unavailable. Future contract design must choose minimal typed
representations and execution routes; this ADR intentionally does not decide
those technical shapes.

## Risks and rollback

False positive opportunity reasoning could compound into misleading economic
memory. Preserve provenance, epistemic state, currentness and derivation;
reinvestigate or abstain when answerability is insufficient. If this doctrine
is superseded, amend the MASTER first and preserve historical decisions.
