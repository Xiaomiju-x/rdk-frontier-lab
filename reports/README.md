# Public observations

- [Selected measurements](observations.json): nine explicitly scoped projections
  from historical private receipts. They are **maintainer-reported**, not public
  raw evidence or an independent replication.
- [Source SPDX inventory](source-sbom.spdx.json): deterministic checksums and
  license declarations for the portable package and identified recipe source.
  It is not an inventory of installed NumPy/PyTorch or vendor/model dependencies.

Each observation carries a SHA-256 commitment to its original receipt. Without
that withheld file, readers cannot independently verify the projection. The
commitment is not a signature, timestamp authority or hardware attestation.
Raw private paths, endpoints, logs, weights and input media are not included.

See [results and interpretation](../docs/results.md) and the
[reproducibility levels](../docs/reproducibility.md).
