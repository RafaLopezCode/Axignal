# Demand: is the call mainly about the activity? (flywheel, 2026-10-15)

## Found on AXIGNAL itself

AXIGNAL observing axignal.com (self-check `self-truth-v1`, 92.3 %) still showed 4 of 5
open calls unrelated to market research:

- an electricity supply;
- Andalusia's emergency management;
- foster-family recruitment;
- quality-control assistance.

Each listed a survey code (CPV 79311000/79313000), but only among its **additional** codes.
The buyer's main classification was electricity (09310000), project-management consulting
(72224000), business services (79000000) and technical assistance (71356200).

## General rule

A call is matched by any of its codes. The buyer's own main classification says what the
call is mainly about, and when it is known, AXIGNAL now says so:

| Reading | When | Shown |
|---|---|---|
| `MAIN` | The procedure's or a lot's main code lies within the activity, or is its parent group (≥ 3 significant CPV digits) | First, as today |
| `ADDITIONAL` | The main code is known and outside the activity, or there is no main code and the declared contract nature (supplies / services / works) is one the activity cannot have | Labelled "Parte secundaria", after the others, with the reason |
| unknown | No main code or nature published, or the main code is a whole CPV division ("business services") | Unchanged: unknown is never turned into `ADDITIONAL` |

Nothing is hidden: recall is unchanged, and the label and the order carry the difference.

## Sources

- **TED v3:** `main-classification-proc`, `main-classification-lot`, `contract-nature`.
  Verified against the live API on 2026-10-15. eForms notices carry them; older notices
  return null, which reads as unknown.
- **PLACSP (CODICE):** no main/additional flag. `ProcurementProject/TypeCode` gives the
  nature: 1 supplies, 2 services, 3 works. Concessions, mixed, special and private
  contracts read as unknown.
- **Duplicates:** when a call is in both sources, the national entry is kept and keeps what
  TED says about its main object.

## Blast radius, all organizations

Measured read-only on the production index on 2026-10-15: 17,348 open calls (13,081
PLACSP, 4,267 TED). The main object was approximated from the TED title's category,
matched to the official CPV 2008 labels in 24 languages (EU Publications Office SPARQL
endpoint).

Of the 3,583 TED matches across 48 catalog capabilities:

- **862 (24 %)** are `ADDITIONAL` only;
- 107 have a main code too broad to judge.

| Capability | Matches | Additional only |
|---|---:|---:|
| electrical-installation | 11 | 100 % |
| security-systems | 23 | 74 % |
| cybersecurity | 15 | 60 % |
| market-research | 19 | 47 % |
| building-construction | 295 | 40 % |
| management-consulting | 71 | 39 % |
| software-development | 197 | 34 % |
| it-services | 348 | 25 % |
| medical-devices | 277 | 9 % |
| insurance | 71 | 0 % |

## Rejected alternative

A guard comparing the title against the CPV labels was measured first. At the CPV group
level it was right in only about half of the calls it flagged. For example, it would have
demoted "Servicio de Agencia de Comunicación" for a marketing firm and building
rehabilitation works for a builder. The buyer's own main classification is evidence;
lexical similarity is not.

## Rollout

Daily ingestion is a delta, so calls already stored carry no main code and read as
unknown until replaced. `python -m tools.runtime.demand_refresh` re-reads each complete
open-demand slice's window and updates only the records, never a slice's state. It is
operator-run only, with explicit authorization.
