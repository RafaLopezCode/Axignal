# Feature Specification: Comparable evolution (day X versus day Y)

**Feature Branch**: `spec/evolution-comparable`

**Created**: 2026-10-15

**Status**: Draft

**Input**: CTO, 2026-10-15: "La línea temporal de evolución de datos es un pilar de AXIGNAL y no
lo veo bien reflejado en el Dashboard, donde me cuesta ver una comparativa de lo registrado un
día X con otro Y, como una evolución en SEO, GEO, reputación, etc."

## Authority

- **MASTER §20 (Temporalidad).** AXIGNAL must answer how an organization looked before and when
  something appeared, changed or stopped being observed. The preferred shape is current
  materialized state plus temporal history. `UNKNOWN_END` is never invented.
- **MASTER §22 and §54 (Digital Representation Intelligence).** A before/after is comparable
  only when question, surface, instrument, version, conditions, period and coverage are
  compatible. A result without instrument id and version is not comparable. A material change
  of instrument creates a discontinuity.
- **MASTER P10 (Temporal UX).** History, changes, before/after, return delta.
- **MASTER §56.17.** UNKNOWN is never rendered as FALSE.

## Measured state

- **The engine keeps history.** `application/timeline` condenses each family of a view into
  daily metrics (`fo_family_snapshots`, 31 metrics) and states CHANGE findings against a
  baseline at least a week old.
- **The web never shows it.** The web contract drops `timeline`. The Evolution tab lists events
  ("observation changed / unchanged") with no values, so day X cannot be compared with day Y.
  Only the product MCP reads the full history.
- **No instrument per metric.** Snapshots do not record which instrument or version produced a
  value, so a change of method cannot be told from a change in the world.
- **Thin presence coverage.** Presence has an audit-attention list, LCP and INP and two GEO
  numbers. It has no count of checks passed.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compare any two recorded days (Priority: P1)

The subscriber picks day X and day Y from the days AXIGNAL recorded. The default is the first and
the latest day. For each family (presence: SEO and GEO, reputation, demand, relationships,
activity, markets, value, economics, organization, context) they see, per metric:

- the value on X and the value on Y;
- what changed: the number and its direction, or the items that appeared or disappeared;
- whether the two values are comparable.

**Acceptance Scenarios**:

1. **Given** two recorded days, **When** a numeric metric moved beyond its threshold, **Then**
   the delta is shown. It is coloured better or worse only where the metric declares a polarity
   (faster, cited more); otherwise it is neutral.
2. **Given** a set metric (audit checks needing attention, competitors, buyers, languages),
   **When** compared, **Then** the items added and removed are listed.
3. **Given** a metric measured by a different instrument or version on X and Y, **When**
   compared, **Then** it says "not comparable: the instrument changed" and states no change.
4. **Given** a metric absent on one of the days, **When** compared, **Then** it is "not measured
   that day", never zero or empty.
5. **Given** only one recorded day, **When** the view opens, **Then** it says that evolution
   starts with the second observation, as today.

### User Story 2 - Every value carries its instrument (Priority: P1)

Each snapshot stores, per metric, the instrument and version that produced it:
- the web audit (`representation-audit.v1`);
- the generative probe (kind, model and a fingerprint of its frozen questions, language and
  live-search setting);
- otherwise the timeline definition version.

CHANGE findings are never stated across an instrument change.

### User Story 3 - More comparable presence metrics (Priority: P2)

- **Audit checks passed** (higher is better), alongside the checks needing attention.
- The AI-naming share and brand knowledge, each with its probe instrument.

## Requirements *(mandatory)*

- **FR-001**: Snapshots MUST store `_instruments` per metric. Older snapshots without it are
  comparable only with each other (unknown instrument versus unknown instrument).
- **FR-002**: `changes()` MUST skip a metric whose instrument differs between the two
  snapshots.
- **FR-003**: The view MUST carry a compact evolution:
  - the recorded days (up to 180);
  - versions, where consecutive identical days are collapsed into one (from, to) range;
  - a metric catalog (family, polarity, kind, thresholds).
- **FR-004**: The web MUST compute X/Y rows from the catalog and versions with the same
  thresholds as the engine. A parity test MUST pin them.
- **FR-005**: Labels MUST be human, with no metric keys or codes on screen, in six locales.
  Polarity colour is used only where the metric declares one.
- **FR-006**: Nothing compared is presented as a cause. A change is what differs between two
  readings by the same instrument, not why (as the CHANGE limitation states).

## Success Criteria *(mandatory)*

- **SC-001**: For AXIGNAL in Admin (three recorded days), the Evolution view shows X versus Y for
  every family with values.
- **SC-002**: An instrument change between X and Y is shown as not comparable, never as a change
  (test).
- **SC-003**: The view payload grows by no more than about 20 KB for 180 recorded days of a
  typical organization, thanks to the collapsed versions.
