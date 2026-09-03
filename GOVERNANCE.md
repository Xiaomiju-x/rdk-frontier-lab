# Governance and maintenance

## Ownership

Initial maintainer: [@Xiaomiju-x](https://github.com/Xiaomiju-x).
This is an independently maintained community repository. Vendor employment,
equipment access or upstream links do not make it an official vendor release.

The maintainer reviews scope, licensing, numerical claims and release readiness.
Additional maintainers can be added through a documented PR after sustained,
reviewed contributions; this document does not invent an existing review board.

## Decision process

Small corrections use ordinary PR review. Model identity, evidence semantics,
license boundaries, hardware execution and incompatible API changes require an
issue explaining the trade-off and an explicit maintainer decision in the PR.
Unresolved evidence is labelled incomplete; it is not settled by optimistic wording.

## Release discipline

- The default branch is development; tagged releases are reviewed snapshots.
- CI tests the public tooling, not proprietary runtimes or historical board claims.
- A release includes a changelog, source snapshot, package artifacts, SHA-256
  checksums and verification notes. No PyPI publication is implied.
- Failures and superseded attempts remain in the research history. Never erase
  a failure to make a benchmark table look cleaner.
- Security fixes receive focused review and a new version. No response-time SLA
  is promised by this volunteer-maintained project.

## What long-term maintenance means here

Stable model IDs, explicit versioned schemas, small optional dependencies,
automatically checked documentation, scoped CI, reproducibility instructions and
honest deprecation notices. It does not mean automatic device access, unrestricted
background training or an unlimited commitment of the maintainer's hardware.
