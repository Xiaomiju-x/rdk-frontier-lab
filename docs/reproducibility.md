# Reproducibility levels

| Level | From this release? | Meaning |
| --- | --- | --- |
| Tooling tests | Yes | Public interfaces and regression behaviour on CPU |
| Scalar demo | Yes | Six known values; no neural/hardware claim |
| First-party geometry | Yes, with NumPy | Known correspondences, not a learned matcher |
| Catalogue/source metadata | Inspectable | Dated observations and recorded revisions |
| Historical board summaries | Not fully | Private raw evidence and model assets withheld |
| Complete three-board benchmark | No | Numerical, dataset and reproduction gates remain open |

Use a clean tag, record its commit and run [the contributor checks](../CONTRIBUTING.md).
Hosted tests cover Linux/Windows/Python interfaces, not proprietary board runtimes.

Original-file digests in `registry/snapshot_provenance.json` and selected reports
are provenance commitments. Withheld originals cannot be independently verified
from this release alone.

## Package rebuilding

Install pinned developer requirements; run `python -m build --no-isolation`, then
`python tools/check_distribution.py dist`. The wheel includes public catalogue
data/licenses, not raw experiments or heavy models. Determinism checks use the
same source and `SOURCE_DATE_EPOCH`; they are not cross-platform certification.
