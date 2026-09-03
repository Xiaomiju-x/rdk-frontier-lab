# Hardware boundaries

| Target | Independent compile target | Artifact |
| --- | --- | --- |
| RDK X5 | `bayes-e` | `.bin` |
| RDK S100 | `nash-e` | `.hbm` |
| RDK S600 | `nash-p` | `.hbm` |

These are the laboratory's target contracts, not a claim that every vendor
example embeds the same march spelling. Record exact sample/runtime metadata
instead of silently relabelling it. Identical extensions do not make HBM files
portable. Compiler, graph, configuration, calibration, layout, dtype, alignment
and runtime identity all matter.

## No hardware execution in the public core

No credentials, server launchers, discovery, automatic installation or all-boards
deploy command are provided. Hosted CI has no private board access. Historical
observations do not certify the newly published code on those devices.

A device recipe needs a project-local environment, explicit identity checks,
resource limits, exclusive locks, timeouts, negative-input tests and independent
cleanup verification. Preserve existing services, models and unrelated workloads.

Use files for inputs and outputs. Do not connect cameras, motors, CAN, serial,
motion commands or robots without a separate reviewed project and on-site controls.

The [Roboto Origin project](https://github.com/Xiaomiju-x/roboto-origin-rdk-x5-s100)
is a separate workline; its offline readiness does not prove real robot control.
