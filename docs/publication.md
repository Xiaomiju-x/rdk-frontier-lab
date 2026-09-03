# Public release boundary

This is a curated projection, not a recursive copy of an internal workspace.
Never publish an internal repository or its unreviewed history.

## Included

Reviewed first-party source, small synthetic fixtures, original SVG, schemas,
source references, asset notes, sanitized observations, tests and documentation.
Historical observations and newly tested public code remain separate.

## Excluded

Credentials, private keys, authentication files, private endpoints, personal
paths/hostnames, raw internal logs, company-only material, identifiable media,
source caches, environments, downloaded wheels, ONNX, BIN/HBM, checkpoints and
restricted datasets. Exceptions require asset-specific review and a documented
policy change. A top-level code license cannot override upstream terms.

## Audit

```bash
python tools/check_publication.py
python tools/render_catalogue.py --check
python tools/build_metadata.py --check
```

After staging, use `python tools/check_publication.py --git-index` to scan actual
index blobs, including otherwise ignored paths. Check file types/sizes, UTF-8,
suspicious credentials/endpoints, private paths, JSON, local links and required docs.

Patterns cannot detect every secret or license problem. Review the exact diff
and asset scope before publishing even when automated checks are green.
