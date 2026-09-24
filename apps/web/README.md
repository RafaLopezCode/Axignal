# AXIGNAL Web Application (Boundary Placeholder)

`apps/web/` is the web application boundary. No product features are implemented
during the governance bootstrap.

## Rules

- The web app is a **presentation and query layer**. It reads from AXIGLAND
  projections and may issue XIGNAL (observation) requests.
- The web app MUST NOT write canonical state directly. Canonical writes happen
  only through the domain layer after evidence admission.
- No `Edit company profile` capability may exist (MASTER §23, §32).
- Infrastructure (schedulers, providers, budgets, JEV, batches) must stay
  invisible to normal users (MASTER §26, §46.40).
- UX semantics precede visual spectacle (MASTER §25, §46.39).
