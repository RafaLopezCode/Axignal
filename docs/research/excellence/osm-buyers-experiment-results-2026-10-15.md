# Experiment results: OSM establishments as potential buyers (2026-10-15)

Protocol: `osm-buyers-experiment-protocol.md`. Only aggregate figures appear here; the sheet, the key and the labels (which may name people) stay in ignored working data.

## Sample and labelling

- **Sample:** 9 subscribers in 8 countries. A tenth (Plexus) was left empty because both of its queries failed with HTTP 504, which is recorded as a failure, not as an absence.
- **Candidates:** 285, of which 163 came from OSM and 122 from the Wikidata sector route. The two sources barely overlapped: 4 names in common across all subscribers.
- **Labels:** applied blind to the source by Codex with a browser, in a second, verified pass. The first pass was discarded: it took about 3.6 s per row and used search-engine pages as evidence.
- **Checks on the second pass:** no search-engine evidence, 282 distinct descriptions of what was seen, and dead websites cross-checked. In 10 of 11 cases the OSM website tag was outdated and the organization's current site was found.
- **CTO decision (2026-10-15):** the planned human agreement check on 30 rows was waived.
- **Known limitation:** one candidate that appears twice was labelled inconsistently. Its website returns 403 to automated access.
- **Error corrected:** one subscriber's activity label in the sheet was wrong (imputed rents) and was fixed before the second pass.

## Results

| Measure | OSM | Wikidata |
|---|---|---|
| Useful (real, active, correct sector, not a natural person) | 90/163 = **55.2%** | 94/122 = 77.0% |
| Useful among rows that could be determined | 78.3% | 83.9% |
| Could not be determined | 48 (29%) | 10 (8%) |
| Natural persons | 9 = **5.5%** | 0 |
| Subscribers with ≥ 5 new useful and plausible candidates | **8 of 9** | — |

**OSM by website:**
- with a website: **72.0%** useful;
- without a website: 38.3% useful.

**A simple person filter** (a personal title, or a professional category with a name that has no firm or legal-form word):
- leaves 2.8% natural persons;
- removes 9 useful entries.

**With both rules (website required, plus the filter):**
- 73.6% useful and 2.8% natural persons;
- 6 of 9 subscribers keep ≥ 5 useful candidates in a sample of 20.

## Verdict

**Inconclusive under the protocol:**
- the useful rate falls between 50% and 70%;
- natural persons exceed 2%;
- the ODbL review is still pending.

The rules "website required" and the person filter were derived after the fact on these same data. They must be fixed in advance and confirmed on a new, larger sample before integration.

The signal is nevertheless strong: OSM brings local buyers that Wikidata does not (Wikidata leans towards large groups), and with a website they are useful about 72% of the time.

## Next

1. **A confirmation sample** with the rules fixed in advance: about 25 subscribers × 30 OSM candidates, read from a dated extract (for example Geofabrik), which is also what production would need. Labelled with the same verified procedure.
2. **Same acceptance criteria:**
   - useful ≥ 70%;
   - natural persons < 2%;
   - ≥ 5 new useful candidates per subscriber.
3. **The ODbL review, in parallel.**
