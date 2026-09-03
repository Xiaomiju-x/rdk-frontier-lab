# Architecture

The public repository is separate from the private experimental workspace.
Publication engineering does not start or resume laboratory jobs.

| Layer | Public responsibility | Not included |
| --- | --- | --- |
| Portable core | JSON contracts, hashes, numerics, catalogue and offline examples | SSH, GPU jobs, vendor runtime loading |
| Reviewed recipe | First-party source, explicit optional dependencies and synthetic tests | Automatic permission to use third-party weights |
| Historical observations | Dated projections, original-file commitments and limitations | Raw private telemetry or independent-reproduction claims |

The core works from a checkout and wheel. Catalogue data is packaged in the wheel,
so the installed CLI does not depend on the working directory or private paths.

## Integrity is not truth

Manifests establish byte/hash agreement; validators reject contradictory states.
Neither proves who ran a job or whether a fixture is representative. Source
provenance and independent reproduction are required for stronger claims.

## Implementation lineage

The public contracts incorporate lessons from the laboratory's V2-C and
three-target tools, but are a separately tested portable implementation. They
do not inherit historical hardware PASS from a shared interface concept.

The geometry port comes from a first-party MIT component; its scorer reference
is identified separately. No upstream model source tree or vendor binary is copied.

## Dependencies

The core uses only the standard library. Only `rdk_lab.geometry` imports optional
NumPy. PyTorch is referenced by the separate neural source recipe, never imported
by the CLI. Pinned developer/build dependencies are not runtime dependencies.
