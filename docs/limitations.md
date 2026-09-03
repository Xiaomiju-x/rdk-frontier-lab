# Known limitations

- APIs are alpha. The core implements no vendor runtime, automatic deployment,
  remote execution, signatures or hardware attestation.
- Receipt checks establish consistency, not truth, scientific representativeness
  or independent reproduction. Path checks assume a stable trusted root.
- Geometry requires established correspondences. The neural reference requires
  separately installed Torch and includes no pretrained checkpoint.
- No PyPI publication is included in this release.
- Fixed/synthetic consistency is not labelled-dataset accuracy. Many official
  examples still lack full parity, stress, clean-rebuild or redistribution closure.
- New BPU routes include numerical/task failures despite compilation and execution.
- TTM R3 has no accepted standard ONNX; native S600 CPU deployment is unfinished.
- Some large-model entries are source/subgraph probes or first-party substitutes,
  not the upstream trained model.
- S600 runtime queue-full behaviour was not observed; application concurrency is
  not runtime-overflow coverage.
- No complete independently reproducible public three-board benchmark exists.
- No robot, sensor, actuator, navigation or motion-control readiness is established.

These are tracked boundaries, not grounds to hide results or blame hardware
without evidence. See [results](results.md) and [roadmap](../ROADMAP.md).
