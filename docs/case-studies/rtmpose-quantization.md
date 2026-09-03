# RTMPose: find the first divergent stage

Evidence level: **maintainer-reported private run**, snapshot 2026-09-03.
Projection and receipt commitments: [`c3-*` observations](../../reports/observations.json).

The original experiment evaluated a 133-keypoint RTMPose model and its unchanged
SimCC decoder. The study below used one original held-out input; it is a
deterministic parity investigation, **not COCO AP or population-level PCK**.

## Same graph, same input, same decoder

| Stage | Exact keypoints out of 133 | Observation |
| --- | --- | --- |
| Source | 133 | Reference |
| Original float | 133 | Preserved |
| Optimized float | 133 | Preserved |
| Calibrated | 2 | First observed failure |
| Quantized BC | 10 | Raw outputs match the earlier S600 board output bit-for-bit |

The three floating stages retained SimCC NRMSE below 2.72e-6. The divergence was
already present in the simulator. A functioning compiler, device runner, aligned
buffer, deterministic output and clean process exit therefore did not establish
model fidelity. The evidence did not isolate one specific internal operator.

## One bounded accuracy-first attempt

An independently compiled 24,420,624-byte Nash-p artifact used a reviewed
max-calibration/int16-requested configuration. Graph, calibration inputs,
held-out input, decoder and original numeric gates stayed fixed.

The quantized BC preserved **4/133 exact points**, PCK@1 px was **0.2782**, maximum
coordinate error **35 px**, maximum score difference **0.11991**, and the two
model-specific SimCC NRMSE values were **0.13040 / 0.14014**. Both PTQ and BC
failed the original gate. The route was stopped before another board run.

## Reusable lesson

1. Treat decoder parity and task accuracy as separate requirements.
2. Compare raw intermediate tensors before guessing a layout or transport bug.
3. Keep original input, graph, thresholds and failed runs immutable.
4. Require a bounded, justified simulator improvement before spending more
   hardware time; do not rename numeric failure as deployment success.

This does not establish that RTMPose is universally incompatible with S600,
nor does it transfer the outcome to a different X5/S100 conversion. Exact public
weights, generated inputs, compiler recipes and raw outputs remain needed for
independent reproduction. The included generic receipt validator cannot replace
the model-specific SimCC and decoded-keypoint gates.
