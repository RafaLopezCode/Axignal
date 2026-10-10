# AXIGNAL Admin — root-only ten-minute step-up (issue #184)

Status: CODE INTEGRATION CANDIDATE; production factor NOT enrolled or enabled.

The existing operator SSH connection and normal PRIMARY Admin session remain
unchanged. Sensitive Staff writes require a separate independently verified TOTP
factor and an ephemeral STEP_UP bearer. This is not a public login service.

## Explicit operator ceremony (only after deployment authorization)

Verify the active AXIGNAL deployment SHA, services and persistent data directory
before running any command. Use only the AXIGNAL root-only operator shell.

1. Enroll once with python -m tools.runtime.admin_session enroll-step-up
   using --principal-id, --factor-file and --provisioning-file arguments.
   Factor and provisioning paths must be outside Git and release paths.
   The CLI creates both exclusively mode 0600 and prints no factor or URI.
   Read the provisioning file only within the protected operator terminal,
   scan it on an independent authenticator device, then securely remove that
   temporary provisioning file. Never store a screenshot or copy in documentation.
2. Keep the original PRIMARY session and its token file. For a privileged task,
   invoke python -m tools.runtime.admin_session step-up with --data-dir,
   --primary-token-file, --factor-file and --output-file. An authenticator code
   is requested interactively without shell echo. The CLI rejects non-TTY usage.
   It writes a distinct opaque bearer to a new root-only 0600 file, never stdout.
3. In the Admin Accounts panel reached through the existing authorized loopback
   SSH tunnel, paste the temporary bearer into its step-up control. It is
   exchanged at same origin, checked against the live PRIMARY principal, and
   retained only in a separate HttpOnly cookie scoped to Staff API endpoints.
   It expires in no more than ten minutes; PRIMARY reads continue uninterrupted.
4. Revoke a temporary credential via the existing admin_session revoke CLI with
   --data-dir and --token-file. Revoking PRIMARY also blocks Staff operations
   because each write revalidates both credentials against the same principal.

## Invariants

- Do not activate AXIGNAL_STAFF_CAPACITY_ENABLED during issuer installation.
- Never pass OTP via command arguments, environmental variables, browser forms,
  HTTP requests, Git, logs, screenshots or long-lived prompts.
- Never expose a public Admin login, new port or modified SSH/PAM policy.
- No checkout or billing mutations are authorized by Staff operations.
- Verify a real tenant in the protected production runtime only after separate
  approval, including successful and denied flows, session expiry, revocation,
  tenant isolation, billing preservation and audit attribution.
