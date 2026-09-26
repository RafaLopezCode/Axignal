# P0-JEV-04 Corpus Recovery Assessment

**Assessment date:** 2026-09-26
**Status:** Candidate assessment only; no dataset downloaded, gold created, or experiment executed.

## GLEIF Global LEI Index — Candidate A

- **License:** GLEIF's current LEI Data Terms of Use state data available through the Access Service are under CC0 1.0. CC0 permits commercial reuse; trademark, privacy/publicity, and other non-copyright rights remain separate. Users must not imply GLEIF endorsement or affiliation. See [GLEIF LEI Data Terms of Use](https://www.gleif.org/en/meta/lei-data-terms-of-use) and [CC0 deed](https://creativecommons.org/publicdomain/zero/1.0/) (checked 2026-09-26).
- **Domain/provenance:** Strong authoritative business/legal-entity reference domain. GLEIF says Level 1 covers who-is-who records and includes historical and current records; Level 2 reports direct and ultimate accounting-consolidating parent relationships. Reporting exceptions include no parent, permitted exceptional opt-out, or parent lacking an LEI. See [Level 1](https://www.gleif.org/en/lei-data/access-and-use-lei-data/level-1-data-who-is-who), [Level 2](https://www.gleif.org/en/lei-data/access-and-use-lei-data/level-2-data-who-owns-whom), and [concatenated files](https://www.gleif.org/en/lei-data/gleif-concatenated-file/download-the-concatenated-file) (checked 2026-09-26).
- **Semantic realism:** Real organization records and declared corporate relationships, but coverage is limited to LEI-registered population and the defined accounting-consolidation/fund/branch relationship scopes. Records are entity-reported and can have gaps/exceptions.
- **Textual evidence quality:** Predominantly structured reference data. Provider-visible semantic evidence can be deterministically rendered from source fields with provenance, but such renderings are procedural and are not naturally occurring prose passages.
- **Label independence:** Directly observable source statements are not automatically objective truth labels. Independent adjudication or a separately authoritative external comparator and time-aware policy would still be required. A source's own assertion should not be used as independent gold for itself.
- **Claim/evidence fitness:** Limited for P0-JEV-04 as currently scoped. May be a strong separate future `ENTITY_ALIGNMENT` or `ECONOMIC_RELATIONSHIP` dataset; do not silently change the declared family. It is insufficient alone to establish representative natural-language claim-evidence support quality without a validated extraction/label protocol.

## Wikidata — Candidate B

Wikidata states structured data in the main, Property, Lexeme, and EntitySchema namespaces is CC0; its developer materials describe structured statements and references. See [Wikidata licensing](https://www.wikidata.org/wiki/Wikidata:Licensing) and [developer portal](https://www.wikidata.org/wiki/Wikidata:For_developers/en) (checked 2026-09-26). CC0 permits commercial reuse, but source references, statement completeness, community edits, and per-statement provenance quality vary. It is useful for discovery and structured corroboration, not inherently independent gold. Structured-to-text rendering would be procedural. Keep reference-rich statements separate from unsupported or weakly referenced statements.

## Wikipedia — Candidate C

Wikipedia text is generally available under CC BY-SA 4.0 (plus legacy GFDL conditions applicable to certain material). Commercial reuse is permitted with attribution, indication of changes, and share-alike obligations for adaptations; page revision/authorship attribution must be preserved. See the [Wikipedia reuse guidance](https://en.wikipedia.org/wiki/Wikipedia:Reusing_Wikipedia_content) and [CC BY-SA 4.0 deed](https://creativecommons.org/licenses/by-sa/4.0/) (checked 2026-09-26). Use only small, necessary excerpts; maintain revision URL/date and attribution. It offers naturally written business prose, but should not be mixed with CC0 datasets without an explicit compatibility and storage policy.

## Public-sector open business data — Candidate D

The UK [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) allows commercial reuse with source attribution and prohibits implying official endorsement. Specific datasets may contain excluded/third-party rights; license must be verified per dataset. The Companies House [PSC snapshot](https://download.companieshouse.gov.uk/en_pscdata.html) is a candidate source endpoint, but its exact dataset-specific license, field coverage, temporal semantics, evidence text, and reuse conditions must be verified before admission. Public accessibility alone is not licensing evidence. OGL datasets are promising for business relationships, yet often structured and self-reported, so independent labels and claim/evidence representativeness remain open.

## Corpus construction constraints and recommendation

- No LLM may create claims, evidence, negative examples, adjudications, or gold labels.
- Deterministic rendering of structured records must carry `PROCEDURALLY_CONSTRUCTED_CLAIM=YES`; these examples must be measured separately from naturally occurring text.
- No attempt to balance or force six answer classes. Any future coverage report must list observed classes and mark others `NOT_ESTABLISHED`.
- No naturally occurring independent business claim/evidence corpus is accepted by this assessment. `GOLDEN_CORPUS_ACCEPTED=NO`; `LIVE_EXPERIMENT_ELIGIBLE=NO`.
- Recommended next P0-JEV-04 corpus search: seek a naturally occurring public business-information QA/verification source with explicit permissive per-record licensing, original evidence documents, independent labels and temporal provenance; use GLEIF/Wikidata only as structured candidate/provenance enrichment, not as an automatic gold-label source. Keep procedural structured-data cases in a separate stratum. CTO authorization is required before resuming P0-JEV-04.
