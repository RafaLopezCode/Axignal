# P0-SOURCE-01 experimental acquisition bakeoff

This experiment is an offline, standard-library-only reference harness. Its
fixtures are synthetic and authored for this repository; they are not claims
about any live source and are not production AXIGNAL components. The harness
measures fixture transport and checks the experimental observation boundary.
It does **not** claim comparative runtime measurements for the third-party
candidates documented in the research report.

Run from the repository root:

```powershell
python experiments/source-acquisition-bakeoff/run_bakeoff.py --iterations 3
```

Results are written to `experiments/source-acquisition-bakeoff/results/` as
JSON. The runner binds only to an ephemeral loopback port and uses only its
own fixture server. No external host, credentials, proxy, browser, model, or
candidate package is contacted or installed.

The deterministic corpus has twelve workload records (W1-W12). Per-run wall
time and retrieval timestamps are measurements and therefore vary. Fixture
content, workload IDs, expected outcomes, evidence-slot counts, and provenance
fields are stable. Run the experiment contract tests with:

```powershell
uv run pytest tests/experiments/test_source_acquisition_bakeoff.py
```

The separate project/research document explains why a live engine bakeoff is
deferred and what is still needed for candidate-specific measurements.
