# P0-HFX-01 Tasks

- [x] Verify exact canonical base, clean worktree at reentry, and Manifest V1
  digest; refresh `origin` and confirm no base drift.
- [x] Reconcile GO/NO-GO against MASTER, Constitution, ADRs, CORE-05, and HFX
  integration matrix.
- [x] Add the minimum immutable Subscriber Projection, preserve UNKNOWN, and
  keep XeedId / OrganizationId / FaxtId identity planes distinct.
- [x] Add deterministic contract tests for authorization identity, global
  object identity, membership-only semantics, equal raw ID separation, and
  fail-closed behavior.
- [x] Add the loopback-only test/dev contract server and clearly disclosed
  synthetic data.
- [x] Implement the Golden Master-derived browser presentation and truthful
  empty/unknown/error states without changing its source inputs.
- [x] Verify selection, focus history, camera, depth, Bottom Context, AXENT
  active context, responsive behavior, and reduced motion in a real browser.
- [x] Update the HFX integration matrix only for authorities demonstrated by
  the projection; keep unsupported semantic graph edges UNKNOWN.
- [x] Verify the manifest, deterministic build, canonical Python gates,
  Graphify, JavaScript syntax, browser E2E, changed-path secret pattern scan,
  and scope.
- [x] Complete the A01–A35 adversarial self-audit.
- [ ] Commit, push, open/reuse exactly one PR against `main`, and verify
  exact-head remote CI, including Gitleaks.
- [x] Keep any PR unmerged, hand off required human visual acceptance, and do
  not start HFX-02.
