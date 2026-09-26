# P0-HFX-00 Research Dossier

This Spec Kit dossier records research decisions and links to repository
evidence. The CTO source pack at `D:\AXIGNAL\HFX-RESEARCH-INPUT\` was reviewed
as reference-only input; its documents were not copied into the repository.

## Evidence synthesis

See [`HFX_COGNITIVE_PSYCHOLOGY_AND_HCI_RESEARCH.md`](../../../docs/research/HFX_COGNITIVE_PSYCHOLOGY_AND_HCI_RESEARCH.md)
for primary HCI papers, WCAG 2.2/COGA, official PostgreSQL/pgvector sources,
study/task limits and the distinction between empirical evidence, guidance,
AXIGNAL inference and CTO hypothesis.

See [`HFX_USER_RESEARCH_AND_VALIDATION_PROTOCOL.md`](../../../docs/research/HFX_USER_RESEARCH_AND_VALIDATION_PROTOCOL.md)
for future participant groups, repeatable tasks, acceptance scenarios A–J,
measures, instruments and ethics. No AXIGNAL participant research has yet
been performed.

## Source-pack convergence map

| Source-pack topic | Canonical/repository convergence |
|---|---|
| Human First north star, Expertise Tax, compression, semantic depth, no mental joins | MASTER §55; HFX product doctrine; ADR-0016 |
| Psychology and HCI bibliography | HFX research synthesis with checked source links and limitations |
| Taxonomy and Human Output Contract | HFX product doctrine, conceptual only |
| Navigation, continuity, provenance and AXENT | MASTER §55; ADR-0017; HFX architecture; Subscriber Experience addendum |
| Visual epistemic grammar | HFX product doctrine; Design Doctrine/Governance; future validation only |
| Research protocol and benchmark | HFX user-research protocol |
| PostgreSQL + pgvector recommendation | ADR-0017 non-decision and architecture benchmark hypothesis |
| Three context authorities and client router | ADR-0017 and HFX architecture |

## Technology decision status

PostgreSQL is a plausible structured starting point and pgvector a possible
auxiliary locator. Official docs expose relevant capabilities and limitations,
but no AXIGNAL production workload benchmark exists. No store, extension,
index, migration or embedding pipeline is selected by P0-HFX-00. A future
implementation proposal must include RLS roles, selective-filter behavior,
exact/approximate recall, deletion/offboarding, provenance traversal and
operational-cost evidence before any technology selection.
