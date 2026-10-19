# Spec 106 — Its website's HTTP security grade (Mozilla HTTP Observatory)

Last free source of the CTO-approved SEO/GEO roadmap (technical trust).

- `pipeline/web_quality/observatory.py`: MDN HTTP Observatory API v2 (free, no key): grade
  (A+..F), score, checks passed of 12, scan time and the public report URL.
- `tools/runtime/security_grade.py`: queued on read, two hosts per tick, 30 days shared per
  host, failed scans retried after 6 h (UNKNOWN, never a grade).
- Finding `WEB_REPRESENTATION` / `SECURITY_HEADERS_GRADE`, OBSERVED, with instrument,
  conditions, sample and uncertainty: HTTPS redirection, HSTS, CSP and other headers as the
  Observatory weighs them; not a penetration test nor a search position. AXENT steps: open the
  report, HSTS + CSP + X-Content-Type-Options + Referrer-Policy, measure again.
- SSL Labs is not used: its free service's terms restrict use and a scan takes minutes.
- On unless `AXIGNAL_SECURITY_GRADE_ENABLED=false`. Cost: $0.

Measured live on the 20 agency clients: 17 graded on the first pass (8 F, 2 D-, 1 D, 3 C-,
1 C, 1 B-, 1 B), 3 refused by the service and retried later.
