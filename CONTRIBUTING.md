# Contributing

Thank you for helping make edge-AI results easier to reproduce. Clear negative
results, documentation fixes and small tested recipes are as useful as new models.

## First contribution

1. Read the [publication boundary](docs/publication.md) and [code of conduct](CODE_OF_CONDUCT.md).
2. Open a focused issue explaining the target, evidence and proposed scope.
3. Work on a branch. Keep one algorithm, behaviour change or documentation fix per PR.
4. Run the checks below and describe exactly what you tested and did not test.

```bash
python -m venv .venv
# Activate this environment using your shell's normal activation command.
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m ruff format --check .
python -m coverage run -m unittest discover -s tests -v
python -m coverage report
python tools/render_catalogue.py --check
python tools/check_publication.py
python -m build
```

The test suite and CI are offline with respect to devices and models. Dependency
installation is a separate network operation. No contributor is required to own
a board or provide a cloud account to improve the public core.

## Algorithm contributions

Use [the model template](templates/model-entry.md). Provide:

- Exact model/variant identity and immutable upstream source revision.
- Separate code, checkpoint, dataset and dependency terms. Do not upload assets
  merely because a related sample repository has a permissive license.
- Calibration and held-out definitions, with no overlap and no post-result seed selection.
- A frozen task contract before quantization or benchmarking. New contracts must
  have new identities; retain failed attempts rather than retroactively relaxing gates.
- Distinct host, CPU, BPU and hybrid results. Record compiled target, input/output
  layout, dtype, alignment, provider evidence and timing boundary.
- A repeatable command, negative-input tests, cleanup evidence and known limits.

Descriptions must distinguish full trained models, untrained source probes,
subgraphs, classical substitutes and micro models. Never relabel one as another.
Do not count renamed variants or cross-referenced catalogue rows as new models.

## Public evidence

The core receipt validator checks consistency, not honesty or hardware attestation.
A green validation result does not replace reviewer inspection and independent
reproduction. The initial catalogue is a **maintainer-reported snapshot**; turning
an entry into a reproducible public recipe requires additional review.

Exclude credentials, local identities, private endpoints, raw internal logs,
identifiable images/audio, personal paths, restricted weights and binary caches.
New public files must be text or reviewed static assets and pass the allowlist audit.

## Tests and compatibility

- Support Python 3.10–3.14 for the core and Linux/Windows for tested interfaces.
- Keep the core dependency-free; heavy frameworks belong in optional recipes.
- Add a regression for every fixed validation bug, especially false PASS paths.
- Keep coverage at or above the configured 90% branch-aware threshold.
- Change schemas deliberately and document migrations in [API stability](docs/api.md).
- Update generated documentation from its source, not by hand-editing a generated table.

Commits should explain why a change is needed. Contributions are licensed under
the applicable file license; do not contribute code you cannot legally share.
There is no CLA or corporate endorsement implied by contributing.
