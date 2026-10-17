# Feature Specification: This week, what matters

**Created**: 2026-10-17

**Status**: Implemented (this PR)

**Input**: CTO, 2026-10-17: a weekly "3 things that matter" is what justifies paying every month.

## What changes
- A card at the top of the summary, **"Esta semana, lo que importa"**, lists up to three findings from the last 7 days.
- The findings are chosen by a fixed, visible order:
  1. new calls that fit best (spec 087);
  2. measured setbacks;
  3. press;
  4. new regulation;
  5. measured progress.
- One finding of each kind comes first, so three different things are said when they exist.
- Each line opens the finding with its sources.
- If nothing new happened, the card says so, in 6 languages: "Nada nuevo que importe en los últimos 7 días".
- The card is never generated text and never filled with the usual findings. It only regroups what the reading already holds.

## Tests
`apps/web/experience/tests/week-highlights.test.ts` checks:
- the order;
- one of each kind;
- that nothing older than 7 days is shown;
- that a call that does not fit best is never news;
- the honest empty state.
