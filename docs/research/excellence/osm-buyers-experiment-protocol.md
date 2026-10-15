# Experiment: OpenStreetMap establishments as potential buyers (protocol, 2026-10-14)

## Question

Does adding OSM establishments to the `SECTOR_BUYS_FROM_ITS_SECTOR` route give small subscribers useful local buyers that the Wikidata route does not already give, accurately enough and lawfully?

The Wikidata route is the one deployed in `d16a0c1`, and it leans towards large, well-documented groups.

## Design

- **Subscribers:** up to 10 from the golden set, chosen round-robin by country. They need a known industry, and their buying sectors (Eurostat input-output) must have OSM equivalents. Those that already have Wikidata candidates come first, so both sources can be compared.
- **Area:** one bounded urban area per country (Madrid, Berlin, Paris, London, Manhattan, Oslo, Toronto, Sydney). It stands for a local market, not the subscriber's whole reach.
- **OSM side:**
  - named establishments of each buying sector, using the tags listed in `tools/evaluation/osm_buyers.py` (`OSM_TAGS`);
  - read from the public Overpass instance within its usage policy (free slots checked, stop on 429, 40 queries at most);
  - deduplicated by name;
  - 20 sampled at random per subscriber.
- **Wikidata side:** the Wikidata sector-route candidates AXIGNAL already shows that subscriber, 20 sampled at random.
- **Blind sheet** (`annotation-sheet.csv`): both sources shuffled, with the source and links held apart in `key.json`. Each row is labelled by **two people independently**:
  - `real_active_organization` (Y/N/?): it exists and operates today. Its website, a recent listing or the register shows it.
  - `correct_sector` (Y/N/?): it belongs to the stated buying sector.
  - `natural_person` (Y/N/?): it names an individual (a sole trader or a professional by name).
  - `plausible_buyer` (Y/N/?): it could plausibly buy what the subscriber's activity offers.

## Measures

The **useful** rate is the share of candidates that are a real, active organization in the correct sector, with no natural person. Disagreements between annotators are resolved by discussion and reported.

The automatic metrics (`metrics.json`) only describe the sample: establishments found, share with a website, median last OSM edit, name overlap with Wikidata and "person-like" name hints. They decide nothing.

## Decision criteria (fixed before seeing the labels)

| | Accept (all of these) | Reject (any of these) |
|---|---|---|
| OSM useful rate | ≥ 70% | < 50% |
| New useful candidates per subscriber (OSM useful, not already given by Wikidata) | ≥ 5 | < 2 |
| Natural persons among OSM candidates (labels) | < 2% after the filter that production would apply | — |
| ODbL review | Favourable for AXIGNAL's intended use | Unfavourable |

Between those thresholds the result is **inconclusive**. The next step is then a second, larger sample, never integration.

## Licence review (ODbL 1.0): points for legal counsel

This is not legal advice. These are the questions the review has to answer:

1. **Combining data.** Combining OSM establishments with AXIGNAL's other data in a database that subscribers query: is it a *Derivative Database* (share-alike applies to it), a *Collective Database*, or does it produce *Produced Works*? Relevant OSMF guidelines: Substantial, Horizontal Layers, Collective Database, Produced Work.
2. **Showing candidates.** Showing a subscriber a list of named candidates with their OSM link: is it a Produced Work that needs only the attribution "© OpenStreetMap contributors"?
3. **Storing extracts.** Storing extracts per subscriber versus querying a dated extract at read time.
4. **Sole traders.** OSM may name sole traders, so GDPR applies to the extracts (legitimate interest, minimisation, retention).

## Personal data and retention

The sheet and key may name natural persons. They stay in `data/working/` (ignored by git), are never committed or shared outside the review, and are deleted when the review ends (30 days at most). This protocol and the aggregate results are the only artefacts committed.

## Not decided by this experiment

- Production infrastructure: a dated extract (for example Geofabrik) or a self-hosted Overpass instead of the public instance.
- The filter for natural persons that production would apply.
- Mapping OSM tags to sectors beyond the ones tested here.
