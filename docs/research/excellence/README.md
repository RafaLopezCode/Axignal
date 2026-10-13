# Family excellence measurements

How AXIGNAL measures progress toward the roadmap
(`docs/product/AXIGNAL_GLOBAL_FAMILY_EXCELLENCE_ROADMAP_2026-10-13.md`). Never a CI
dependency: real public sources and the assistant are involved.

## Procedure

1. **Run the golden set** (`tools/evaluation/golden_set.json`: 30 public organizations in
   8 countries).
   - Use a throwaway container from the deployed image.
   - Mount the runtime data read-only at `/src` (the runner copies it and never writes to
     production).
   - Run: `python -m tools.evaluation.run_golden > views.json`.
2. **Report:**
   - `python -m tools.evaluation.excellence report views.json --baseline <previous>.json --out <date>.json`
   - The command exits 1 when a family's coverage drops by more than 5 points.
3. **Precision:**
   - `python -m tools.evaluation.excellence sample views.json --family <family> --n 20`
   - A person fills `verdict` (`CORRECT`, `WRONG` or `UNSURE`) for each sampled finding.
4. **Record:** commit the report (aggregates and per-organization observability only;
   never raw views). Update the roadmap's table.

## Measurements

| Date | Set | Report | Notes |
|---|---|---|---|
| 2026-10-13 | Production E2E, 10 organizations, 6 countries | `baseline-2026-10-13-prod-10orgs.json` | Before #229–#235. Reputation 0 %, Activity 0 %, Economics 10 %. |
