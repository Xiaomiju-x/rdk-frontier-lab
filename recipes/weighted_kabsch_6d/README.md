# Weighted Kabsch 6D · first-party recipe

This is **not NVIDIA FoundationPose**. It solves a rigid transform from known,
weighted 3D correspondences. Correspondence estimation, object detection,
segmentation, camera calibration and robust outlier discovery are out of scope.

## Runnable geometry

```bash
python -m pip install ".[geometry]"
python examples/geometry_demo.py
```

The demo uses eight analytic points, a known 90-degree rotation and translation.
It executes only NumPy on the local CPU. Install is optional; the core `rdk_lab`
CLI does not import NumPy.

```python
from rdk_lab.geometry import weighted_kabsch

rotation, translation, rms = weighted_kabsch(object_points, camera_points, weights)
# camera_points ≈ object_points @ rotation.T + translation
```

Inputs use one consistent length unit. The solver requires six positive weights
and rank-two or better geometry, rejects non-finite/negative weights and returns
a proper rotation. It is not a RANSAC estimator. Do not interpret a low residual
with oracle correspondences as real RGB-D pose accuracy.

## Neural reference, not pretrained inference

[`neural_reference.py`](neural_reference.py) preserves the first-party PyTorch
`MatchWeightMicro` scorer and the original geometry partition. It is provided as
reviewable source; PyTorch, checkpoints, training inputs and ONNX outputs are not
bundled or installed automatically. Its full export probe intentionally retains
the SVD operator rather than replacing it with a falsely equivalent graph.

The public NumPy port has stricter degeneracy checks. Its tests are new **host
tests**, not a repetition of the historical X5/S100 CPU measurements.

License: [MIT](LICENSE). Neither this grant nor the top-level Apache license
extends to NVIDIA models, datasets or proprietary dependencies.
