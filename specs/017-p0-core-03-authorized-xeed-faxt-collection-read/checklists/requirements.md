# P0-CORE-03 Requirements Checklist

- [x] Collection semantics preserve the CORE-02 reference meaning.
- [x] Collection entry point requires `AuthorizedXeed`.
- [x] Reference enumeration is scoped to exactly that Xeed.
- [x] Reference enumeration precedes global FAXT resolution.
- [x] Original global FAXT identity/state is preserved.
- [x] Empty, duplicate, malformed and dangling cases are deterministic and
  fail closed where required.
- [x] No Evidence access, provenance, subject membership, persistence or
  production writer was introduced.
- [ ] All required gates and exact-head remote CI pass.
