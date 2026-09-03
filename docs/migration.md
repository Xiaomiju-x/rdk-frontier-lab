# Migration protocol

## 0. Identify the exact model

Name the full model, variant, checkpoint and source revision. Subgraphs,
untrained cores and first-party substitutes need distinct identities. Review
code/weight/data/dependency terms separately; do not silently replace a blocked model.

## 1. Freeze a host reference

Fix pre/postprocessing, tensor contracts and held-out inputs; calibration must
be disjoint. Record provider identity and determinism. Define numerical and task
gates before quantization, not after inspecting results.

## 2. Export and compile independently

Record actual exporter/opset support. Do not rename an opset or competitor engine
to force compatibility. Bind each target artifact to graph, configuration,
calibration and compiler identities. Schema PASS is not operator or numerical PASS.

## 3. Diagnose before retrying

Replay the same held-out inputs through source, float and quantized stages when
available. Save outputs and find the first divergence. Reproduction before the
board narrows the location but need not identify a unique operator. Use bounded,
justified remediation; retain the original experiment and its failed gates.

## 4. Run the real target

Only eligible independent artifacts enter reviewed file-only recipes. Check
identity, hashes, layout, dtype, alignment and resources before submission.
Verify golden/task outputs and negative inputs, not merely a returned tensor.

## 5. Compare like with like

Use the same source, held-out fixture, contract and timing boundary. Separate
model-call, file-to-file and process latency. Record warmups, samples, percentiles,
throughput definition and resources. Do not compare a BPU inner call against a
CPU full pipeline as though they did equal work.

## 6. Publish honestly

Retain failures, licenses, commands, hashes and clean-exit evidence. Release only
reviewed assets. Without public raw inputs/evidence, label summaries
maintainer-reported; a digest alone does not make them reproducible.
