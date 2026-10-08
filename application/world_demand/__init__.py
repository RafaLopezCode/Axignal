"""World demand index (spec 063 §8b): ingest a public demand source once, match many Foci.

Demand-materialized (MASTER §3.2, §8): a slice (source x country x notice kind) is
ingested only after at least one Focus asked a question it covers. Records are public
world observations; matching to a Focus stays POTENTIAL and tenant-private.
"""
