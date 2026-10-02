# P0-SOURCE-01D data model

The experiment reuses application.source_acquisition.SourceRequest and SourceObservation as the semantic boundary.

Experimental measurement records may add:

- provider: obscura | chromium
- provider_version
- executable_digest
- run_id
- workload_id
- iteration
- browser_required_reason
- rendered_dom_fingerprint
- normalized_text_fingerprint
- normalized_markdown_fingerprint
- network_request_count
- discovered_public_endpoints
- elapsed_ms
- cpu_ms
- peak_rss_bytes
- transferred_bytes_observed
- watchdog_triggered
- fallback_reason
- useful_observation_slots
- provenance_complete

These are benchmark/operational fields. They are not FAXT, INXIGHT, CLAIM or canonical AXIGLAND state.

## Provider contract

A future production BrowserAcquisitionProvider must be replaceable and expose only AXIGNAL-owned request/observation semantics. Provider-native CDP/MCP objects do not cross the adapter boundary.
