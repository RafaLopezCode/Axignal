# Local AO-24A harness

Use only isolated development storage outside the repository. The real-mode
launcher composes unchanged FR-30 and existing AO-01 authorization. It writes
an isolated QA bearer to the specified data directory; never commit or publish it.
Production authentication remains the existing runtime's responsibility.

```powershell
cd D:\AXIGNAL\Axignal
uv run python apps/web/experience/qa/037-customer-zero/run_runtime.py `
  --data-dir D:/AXIGNAL/.ao24a-real-proof `
  --sha 1ae70d0e0a89e9af69ed53d5dbbaf1de8bd86b0b
```

In another terminal:

```powershell
cd D:\AXIGNAL\Axignal\apps\web\experience
$env:AXIGNAL_RUNTIME_ORIGIN = 'http://127.0.0.1:8765'
npm run build
npm run start
```

Open `http://127.0.0.1:3810/admin/customer-zero`. If a staff session is requested,
use the existing isolated token in `D:/AXIGNAL/.ao24a-real-proof/admin-session.key`.
The server verifies it, transports it as an HttpOnly cookie and checks authority
for every read/command. No browser-selected role or identity is accepted.

The validated directory already contains two actual observations. To independently
exercise NO_XEED, use a new isolated directory under D:/AXIGNAL, connect that QA
session and Plant AXIGNAL. Do not erase the validated historical evidence.

Default `real` mode acquires the authorized public source. `--scenario insufficient`,
`failure` or `rejection` provide explicit local-only failure injection for browser
QA; they cannot manufacture a successful projection. Return to `real` afterwards.
