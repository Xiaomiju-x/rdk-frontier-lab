# Release checklist

1. Update package version, changelog and citation metadata consistently.
2. Freeze the snapshot date; verify each changed claim against its source.
3. Regenerate catalogue, schemas and deterministic source SBOM.
4. Run lint, format, tests, coverage, schema, link and publication checks.
5. Build and inspect wheel/sdist; install the wheel in a clean environment outside
   the checkout, then run doctor/catalog/demo.
6. Stage only the public mirror, audit actual index blobs and review the diff.
7. Push reviewed source and require hosted CI to pass; no device credentials in CI.
8. Tag the accepted commit, publish release notes and checksummed artifacts,
   and read back the public repository and release page.
9. Preserve limitations. A package release is not a BPU certification.

0.1.0 is a prerelease because tools and recipe coverage are alpha. Future work
should replace maintainer-only observations with rights-cleared reproducible evidence.
