# P0-SOURCE-01 acquisition experiments

All code and results in this directory are experimental. None of the candidate
libraries is an AXIGNAL production dependency or source of canonical truth.
The experimental adapter maps AXIGNAL-owned `SourceRequest`-shaped inputs to
`SourceObservation`-shaped records and retains raw bytes, hashes and retrieval
provenance.

## Reference fixture

The standard-library-only reference harness is retained as its own baseline:

```powershell
python experiments/source-acquisition-bakeoff/run_bakeoff.py --iterations 3
```

It uses the repository's synthetic loopback fixture only and writes
`results/latest.json`. Its original result is not overwritten by candidate
runtime experiments.

## Candidate runtime matrix

Five exact, hash-locked candidate environments are described under
`candidates/<name>/requirements.in` and `requirements.lock`. They are installed
outside the repository and outside AXIGNAL's production environment. The
candidate pins are Scrapling 0.4.15, Crawlee 1.10.2, Crawl4AI 0.9.4, Scrapy
2.19.0, and Playwright 1.63.0. The isolated controller uses Python 3.12.11 and
psutil 7.2.2 for process-tree RSS and CPU sampling.

From PowerShell, choose a task-local directory outside the repository and run:

```powershell
$env:P0_SOURCE01B_ROOT = 'C:\path\outside\the\repository\p0-source01b'
./experiments/source-acquisition-bakeoff/setup_candidate_envs.ps1
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $env:P0_SOURCE01B_ROOT 'browsers'
& (Join-Path $env:P0_SOURCE01B_ROOT 'controller\.venv\Scripts\python.exe') `
  experiments/source-acquisition-bakeoff/run_candidate_bakeoff.py --iterations 5
```

The setup script downloads candidate packages and browser binaries. During the
benchmark, request targets are limited to the fixture server bound to
`127.0.0.1`; the Playwright direct adapter aborts non-loopback browser
requests. Crawl4AI's data directory and Crawlee's storage directory are
redirected into the task-local experiment directory.
Each worker's current directory is separately created under that isolated
root, so candidate default storage cannot spill into the repository.

Each candidate receives a common W1–W12 request set, five measured iterations
after one excluded warm-up, and six synthetic failure cases. The runtime
results preserve candidate-specific failures; they do not translate an
unsupported capability into a candidate failure. W2's initial HTML contains
only `Loading`; `/w2.js` adds `Widget` at runtime. Scrapy reports JavaScript
rendering as unsupported while retaining its raw initial response. The
composition trial runs Scrapy HTTP first and dispatches to Playwright only when
the required `Widget` is absent.

W3 supplies a bounded root and child page as explicit request inputs. This
matrix measures bounded acquisition, not link-discovery policy. W4 retains
synthetic PDF transport bytes only, not PDF text extraction. W5–W9 are raw
source observations; they do not claim semantic extraction. `file://` is
rejected by the experimental harness before dispatch. The forbidden-destination
redirect is simulated to a second loopback path; no private, metadata, or
external address is contacted.

Timestamped candidate JSON and `latest-candidate-runtime.json` are stored in
`results/candidate-runtime/`; content-addressed raw response bytes are stored
under `results/candidate-runtime/artifacts/`. The original reference result
remains at `results/latest.json`.
