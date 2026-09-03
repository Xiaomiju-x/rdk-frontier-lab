# SwinIR-S ×2: fast execution is not faithful restoration

Evidence level: **maintainer-reported private run**, snapshot 2026-09-03.
Numeric projections and original receipt commitments:
[`c17-*` observations](../../reports/observations.json).

## Contract before results

The bounded experiment used a fixed source graph, twelve calibration inputs,
four held-out image inputs and two seam inputs. The frozen image-quality gate
allowed at most **0.30 dB PSNR loss** relative to the source result. Evaluations
used floating outputs before uint8 conversion; post-processing clipping did not
explain the failure. This is not a published super-resolution dataset benchmark.

## Observed sequence

| Stage | Observation | Interpretation |
| --- | --- | --- |
| S600 CPU reference | E2E P50 136.607 ms; original bounded gates accepted | A reference for this fixture, not all image distributions |
| Default independent Nash-p compile | HBM generated | Compiler acceptance only |
| Real S600 BPU | E2E P50 5.695 ms; PSNR loss 5.472–7.294 dB | Execution succeeds; algorithm numeric gate fails |
| Six-stage same-input simulation | Source and two floating stages pass; first failure at calibrated; BC output bit-exact with prior board output | Failure already reproduced before device dispatch |
| One max-calibration/int16-requested candidate | New 118,193,000-byte HBM; PTQ/BC still fail original gate | Stop this candidate before any new board run |

Default and CPU timings both include file read, validation, inference, uint8
output and closed file sink, with 200 timed calls each. Their latency benefit
must not be presented without the quality failure.

## The unsuccessful precision-first candidate

| Held-out image | PTQ PSNR loss, dB | BC PSNR loss, dB | Frozen limit |
| --- | --- | --- | --- |
| 0 | 0.4358 | 0.4404 | 0.3000 |
| 1 | 0.6792 | 0.6870 | 0.3000 |
| 2 | 0.6125 | 0.6211 | 0.3000 |
| 3 | 0.6816 | 0.6884 | 0.3000 |

The candidate improved these numbers substantially, but **all four still fail**.
Its graph, original inputs and thresholds were unchanged. No replacement seed,
easier held-out set, relaxed threshold or second tuning search was used to turn
this specific failed contract into a passing result.

## What the diagnosis does and does not establish

The final output was already INT16, golden values were within its range, and a
separate mathematical output-quantization check passed. Internal mixed INT8/INT16
was observed. Together with the stage replay, this argues against treating the
problem as only final-output clipping or a board transport error. It **does not
uniquely identify an internal operator** or prove that all requested INT16 nodes
were lowered in that precision.

The generalizable method is to preserve the failed artifact, replay identical
inputs across source/float/calibrated/PTQ/BC stages, and move the next expensive
device test behind a frozen simulator gate. This method can be reused even when
the original model cannot yet be redistributed as a complete public recipe.

## Still missing for public reproduction

Rights-cleared model acquisition, compiler recipe and runtime version capsule,
the exact generated inputs and raw stage outputs, plus independent public
replication. Digest commitments alone do not supply those materials. Do not
quote this case study as a hardware defect, a vendor comparison or a proof that
SwinIR can never work on an RDK target.
