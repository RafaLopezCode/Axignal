# Prior Art and Candidate Sensor Families

**Review date:** 2026-09-26  \
**Purpose:** Record relevant primitives and boundaries; not dependencies,
provider approvals, source-rights opinions or production recommendations.

No source code was copied, cloned or vendored. Repositories below are prior-art
references only. The license labels were observed on the linked repository
pages during prior-art review; they are not legal advice or a license review.

| Reference | Primitive / lesson | License | Adopt concept? | Copy code? | Rights caveat / production suitability |
|---|---|---|---|---|---|
| [OpenSEO](https://github.com/every-app/open-seo) | Broad SEO workflows and source/provider routing | MIT | Source selection as replaceable instrumentation, selectively | No | Vendor/product-specific architecture; not an AXIGNAL domain or production source policy |
| [SerpTrail](https://github.com/serpapi/serptrail) | Query/location SearchRun snapshots can be reused across sites and time | MIT | Shared observation/history primitive, subject to rights and comparability | No | SerpApi-bound implementation is not adopted; production rights/access unassessed here |
| [Lettertrace](https://github.com/letterstory/lettertrace) | Separates mentions from citations; informative conditions and uncertainty matter | MIT | Measurement distinctions only | No | Provider/model and opinion-score behavior is not adopted; no production evaluation |
| [LLM Visibility Framework](https://github.com/AntonioBlago/llm-visibility-framework) | Versioned prompt instruments, replicates, stability and time-series comparability | MIT | Frozen instrument and replicate principles | No | Its API calls and universal visibility scoring are not authorized/adopted |
| [OneGlanse](https://github.com/aryamantodkar/oneglanse) | Product UI can differ from model API output | MIT | Treat UI and API as different instruments | No | Browser automation is experimental-only pending rights/access review; none run here |
| [Harken](https://github.com/VladUZH/harken) | Source abstraction, normalization, deduplication and backfill for public mentions | MIT | Reusable observation and deduplication principles | No | Sentiment/mention aggregation does not establish market consensus or FAXT |
| [Twiligent](https://github.com/spacesdrive/twiligent) | First-party social analytics may derive from official authenticated access | MIT | Distinguish data/channel privacy | No | Authenticated analytics remain tenant-private; no account or API used |
| [RPSync](https://github.com/fluffyriot/rpsync) | Broad adapters demonstrate acquisition diversity | AGPL-3.0 | Source-family awareness only | **No — prohibited by default** | License implications and authenticated scraping methods require separate review; unsuitable as a default acquisition pattern |

## Public experience candidate source families

Trustpilot, Google Reviews / Business Profile, G2, Capterra, industry review
systems, public forums, specialized communities, marketplaces and public
consumer/business review sites are candidate sensor families only. This record
does not verify their current terms, APIs, collection permissions, database or
content rights, retention rules, deletion obligations, privacy requirements,
or provider-transmission permissions. No API call, scrape, account creation,
review download or sample-data acquisition was performed or authorized.

Source identity, authority, access method, terms, rights, retention, deletion,
privacy, subject scope, currentness and sensor economics require per-source
review before any future P0-DRI-01/provider work. `PUBLICLY_VIEWABLE` does not
mean `AUTHORIZED_FOR_AUTOMATED_COLLECTION`.

## Disposition

```text
RPSYNC_CODE_COPY=NO
ONEGLANSE_STYLE_BROWSER_AUTOMATION=EXPERIMENTAL_ONLY_PENDING_RIGHTS
MIT_REPOS=PRIOR_ART_ONLY_NOT_DEPENDENCIES
PRIOR_ART_NOT_AUTOMATIC_DEPENDENCIES=YES
EXTERNAL_REPO_CODE_VENDORED=NO
```

AXIGNAL must not become an OpenSEO + Lettertrace + Harken clone. Reusable
instrumentation primitives serve only the larger governed brain: economic
reality + digital representation + public experience + demand/opportunity +
temporal memory + explanation.
