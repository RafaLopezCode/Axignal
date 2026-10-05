# EB-03 architecture review

## Authority check

Compatible with MASTER observation/reuse doctrine and Constitution. The registry governs permission to observe/reuse; it does not establish economic truth, identity truth, relevance, relationship state or canonical writes.

## Boundary decision

The new registry lives in application/economic_discovery because it composes existing source-acquisition and observation-reuse contracts. Network enforcement remains in pipeline/source_acquisition. Observation Memory remains append-only and is not made a rights authority.

## Reuse over creation

Existing SourceDispatchPolicy, ObservationReuseAuthority, TemporalCurrentnessPolicy and ReusePurpose are retained. EB-03 consolidates their issuance rather than replacing them.

## Explicit non-authority

SOURCE_REGISTRY_AUTHORIZED != EVIDENCE_ADMITTED
REUSE_PERMITTED != TRUE
PUBLICLY_ACCESSIBLE != REUSABLE_FOR_ANY_PURPOSE
ROBOTS_METADATA != LEGAL_CONCLUSION

## Deferred

Persistent/admin-managed registry, robots retrieval/parser, actual host rate buckets, retention deletion jobs, conditional GET scheduling, shared monitoring and legal-policy automation remain future slices. The current single-document FirstProof robots exemption does not authorize crawling or subresource acquisition.
