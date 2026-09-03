# Results and evidence boundaries

Snapshot: **2026-09-03 16:36, UTC+08:00**. This release does not start fresh board
experiments. New public software tests and historical device observations are
different evidence classes.

The [catalogue](catalogue.md) contains **59 registry entries**: 26 official,
17 frontier and 16 research. These are not 59 distinct models, runnable public
recipes or successful deployments. Known overlaps are recorded in the catalogue.
The only complete runnable algorithm recipe shipped in 0.1.0 is the optional
CPU weighted-Kabsch geometry example; the arithmetic CLI demo is not a model.

## What is independently replayable here?

The CLI, JSON/manifest validators, numerical utilities, schema checks, packaged
metadata and optional geometry recipe have executable tests. Hosted CI checks
software behavior, not RDK hardware. See the actual
[CI runs](https://github.com/Xiaomiju-x/rdk-frontier-lab/actions/workflows/ci.yml).

Device numbers below are **maintainer-reported historical observations**. Their
sanitized projections and original-file digest commitments are in
[observations.json](../reports/observations.json). Full receipts, original
inputs, weights and runtime environments are not bundled, so these numbers
cannot be independently reproduced from this release alone.

## Selected complete-model observations

| Model / target | Boundary | P50 / P90 / P99, ms | Numerical outcome |
| --- | --- | --- | --- |
| SwinIR-S ×2 / S600 CPU | Same-fixture file-to-file, 200 timed calls | 136.607 / 139.110 / 140.109 | Accepted within the bounded fixture |
| SwinIR-S ×2 / S600 default BPU | Same-fixture file-to-file, 200 timed calls | 5.695 / 5.900 / 6.092 | **FAIL**: PSNR drop 5.472–7.294 dB; limit 0.30 dB |
| SigLIP2 complete vision tower / S600 CPU | File → vision → cached-text similarity → NPZ close, 160 timed calls | 58.348 / 58.599 / 59.114 | Accepted on eight fixed synthetic inputs |
| SigLIP2 / S600 default quantized BC | CPU simulator, not a board benchmark | Not reported | **FAIL**: all six original numeric gates |

The SwinIR BPU has a latency benefit on this fixture but is **not an accepted
algorithm deployment**. SigLIP2 includes the complete vision tower, but uses
cached text embeddings rather than executing the full text tower. These CPU
baselines are not public dataset accuracy, retrieval quality or real-world gain.

## Stop-loss results are part of the deliverable

- SwinIR's one accuracy-first candidate compiled, but every image still missed
  the original PSNR-drop limit. No new board deployment followed.
- RTMPose's same-input six-stage study placed the first observed failure at the
  calibrated graph. One accuracy-first candidate still preserved only 4 of 133
  exact keypoints and was stopped before another board run.
- Default SigLIP2 BC failed its simulator gates. Its prepared six-stage diagnostic
  had not been executed at the snapshot.
- EfficientAD, D-FINE and other new BPU routes retain numeric failures in the
  catalogue; finite, deterministic and fast output is not enough for acceptance.
- TTM R3 has a full host CPU baseline, but two ONNX export routes failed and the
  prepared native S600 CPU environment was not installed or accepted yet.

Case studies: [SwinIR](case-studies/swinir-quantization.md) and
[RTMPose](case-studies/rtmpose-quantization.md). They discuss the observed failure
boundary without claiming one proven faulty operator or a universal model limit.

## Platform work and official examples

The S600 mixed loop ran for 1,803.91 seconds, with 273,320 iterations and 819,960
model calls across a synthetic canary, MobileNetV2 and YOLO11n. The recorded peak
temperature was 53.217 °C. This is a bounded infrastructure stability result,
not an all-model stress certification or comparable end-to-end application FPS.

X5/S100 official examples cover several vision, speech and point-cloud lanes.
Read the per-entry notes: official smoke tests, hybrid execution, fixed prompts,
bounded accuracy, unresolved asset provenance and pending target conversions
are intentionally distinct. An official depth model passing does not reverse a
different custom Depth Anything conversion failing.

## No aggregate success percentage

We do not flatten host, export, compilation, simulator, CPU, BPU, task accuracy
and cleanup into one percentage. A future public benchmark needs licensed input
data, exact rebuild instructions, independently obtained target artifacts and
reviewed repeated measurements on every claimed board. That is unfinished work,
not something this repository's name or CI badge establishes.
