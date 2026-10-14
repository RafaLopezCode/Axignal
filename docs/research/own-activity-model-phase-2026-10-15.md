# Phase proposal: an own model to read an organization's activity (2026-10-15)

**Status:** proposal for CTO decision. It does not authorize training, serving or integration. Integration needs its own ADR.
**Authority:**
- MASTER §13.1–13.2 (replaceable cognition, model swap test) and §54.4 (governed access);
- Constitution (evaluators replaceable and non-authoritative; no provider hard-wiring);
- ADR-0015 (instrument, version and rights on every observation);
- ADR-0090 (semantic layer) and ADR-0099 v1.3 (one reading of the organization's own industry).

## 1. What problem, and why this one

The golden set (2026-10-14) showed that reading what an organization does is the step every family depends on:
- value chain, potential buyers, competitors, regulation and context all start from it;
- the website lexicon misread Lightspeed's legal page as marketing;
- 6 of 30 organizations had a wrong or missing industry before ADR-0099 v1.3.

Today, when no register or Wikidata industry exists, the reading comes from a keyword lexicon (cheap, brittle) or from Jev, an external provider. Jev has three drawbacks:
- it costs per call;
- it sends website text to a third party;
- its terms restrict what its output may be used for.

The goal is narrow: **classify an organization's industry (the 64 industries of the EU-27 input-output table, plus "unknown") from its own public website text.** It is not a data collector, an agent or a chat model.

## 2. Non-goals and hard limits

- **No training or serving on the production VPS** (KVM2: 2 vCPU, 8 GB RAM, no GPU, 20 containers).
- **No autonomous browsing.** Inputs are only pages AXIGNAL already read through its governed reader (robots.txt, rights).
- **Model output is never canonical.** It is a `POTENTIAL` activity with method `OWN_MODEL`, instrument and version. It never overrides the register or Wikidata (ADR-0099 v1.3 order: it only replaces step 3, the website reading).
- **No subscriber-private data in training:** no tenant inputs, private analytics or account data.

## 3. Training data: where labels may come from

| Label source | Rights | Use |
|---|---|---|
| Official register activity codes (INSEE/RNE, Brønnøysund, Companies House SIC, SEC SIC, …) | Public official data, within each register's terms | Main weak labels. Head offices and holdings (70.10, 64.20) are excluded, as in ADR-0099 v1.3 |
| Wikidata industry (P452), translated through NACE (P4496 or the curated table) | CC0 | Second weak label. Where both exist, it is cross-checked against the register |
| Human review | Ours | The gold test set, and disagreements between the two weak labels |
| **Jev / TypeSafe outputs** | **Not allowed.** MCA §2.3(b) restricts using the Services or Output "to train a model to imitate the output of the Services" | Never used as labels or training data |
| Other model providers' outputs | Each provider's terms | Not used unless a written review allows it |

**Website text rights are a gate of their own.** Training copies and retains page text beyond the observation. Before any dataset is built, a decision is needed on whether the site-content rights policy (ADR-0015) allows that retention. The alternative is to train only on sites whose content may be retained. Until then this phase cannot start.

### Size

- **Training:** at least 2,000 organizations, from at least 8 countries, with at least 30 examples for each of the 25 most frequent industries.
- **Test:** 300 organizations verified by people, kept apart and never used to train or tune.
- **Golden set:** the 30 organizations stay as a smoke test.

Weak labels come cheaply from organizations that have a register or Wikidata industry and a readable website. The cost is the reading, at about one site per minute on the existing reader, and the human review of the test set (about 10–15 hours).

## 4. Model options, cheapest first

| Option | What | Training | Serving | Why |
|---|---|---|---|---|
| **A. Baseline** | A small multilingual text encoder (e.g. the multilingual-E5 or XLM-R family) with a linear classifier. No fine-tuning library needed | Minutes to an hour; CPU is possible, a rented GPU is faster | CPU, roughly a few hundred ms per organization, about 0.5–1 GB of RAM | Classification does not need text generation. This is the cheapest thing that could work |
| **B. Small generative model** | A 1.5–3B open model fine-tuned with LoRA/QLoRA through Soup (Apache-2.0), exported to GGUF Q4 | About 1–3 h on one 24 GB rented GPU for about 2,000 examples (estimate) | Needs its own machine: on 2 vCPU, reading 1–2k tokens of website text takes tens of seconds | Only if A fails on multilingual or ambiguous sites, or if an explanation sentence is needed |

Estimates to check when this starts:
- rented GPU time costs a few euros per hour, so a training run costs in the tens of euros;
- a small dedicated CPU server for option B costs about what the current VPS does.

The licence of any base model must allow commercial use, and is recorded in the model card.

## 5. Evaluation and decision criteria (fixed before training)

All are measured on the 300 human-verified test organizations, by country, and compared with the lexicon and with Jev on the same pages:

| Criterion | Accept (all) | Reject (any) |
|---|---|---|
| Top-1 accuracy on the 64 industries | ≥ Jev − 3 points **and** ≥ lexicon + 15 points | < lexicon + 5 points |
| Worst country | ≥ 60% | < 45% |
| Abstention | When it abstains ("unknown"), it is right to; when it answers, accuracy ≥ 80% | Confident answers below 70% accuracy |
| Cost per classified organization | ≤ 25% of Jev's | — |
| Latency, p95 | ≤ 2 s (option A on CPU) | — |

Between the thresholds the result is **inconclusive**, and the next step is more data, never integration.

## 6. Integration, only after acceptance and its ADR

- A provider under `cognition/providers/` implementing the existing semantic port, selected by the router. It stays replaceable (model swap test, MASTER §13.2).
- Output: a `POTENTIAL` activity with `method: OWN_MODEL`, model name and version, and the page it read. It takes the place of the lexicon, and of Jev, in step 3 of the industry reading (ADR-0099 v1.3).
- **Shadow mode first, for two weeks.** It runs next to the current reading without affecting any view. Then compare the disagreements and review a sample of them.
- Serving:
  - option A: a separate container with hard CPU and memory limits, after a load test that shows no effect on production;
  - option B: a separate machine.
- Model card, training data card (sources, rights, dates, label method), a retraining policy (when label sources or website language drift) and rollback to the lexicon or Jev.

## 7. Phases

| Phase | Work | Exit |
|---|---|---|
| 0. Rights | Decide whether website text may be retained for training (ADR-0015); confirm no Jev output is used | Written decision |
| 1. Dataset | Weak labels from registers and Wikidata; 300 test organizations reviewed by people | Data card; balance per country and industry |
| 2. Option A | Train and evaluate against section 5 | Accept / reject / inconclusive |
| 3. Option B (only if A is inconclusive) | Soup LoRA on a rented GPU, evaluated the same way | Same criteria |
| 4. Shadow | Two weeks next to the current reading | Disagreement review |
| 5. Decision | ADR for integration, or stop | — |

## 8. Risks

- **Weak labels inherit errors.** A register code can describe the legal entity, not the business; Wikidata is community-edited. Mitigation: cross-check the two, and use the human-reviewed test set.
- **Language and country imbalance.** Mitigation: measure per country and set a floor.
- **Website text rights:** they may limit the dataset to fewer sites (phase 0).
- **Maintenance:** a model is one more component to version, monitor and retrain. Option A keeps that cost lowest.
