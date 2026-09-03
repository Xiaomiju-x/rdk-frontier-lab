"""Synthetic known-correspondence CPU geometry; no camera, weights or training."""

import json

import numpy as np

from rdk_lab.geometry import weighted_kabsch

points = np.array(
    [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [1, 0, 1], [0, 1, 1], [1, 1, 1]],
    dtype=float,
)
rotation = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]], dtype=float)
translation = np.array([0.25, -0.5, 2.0])
actual_r, actual_t, rms = weighted_kabsch(points, points @ rotation.T + translation, np.ones(8))
assert np.allclose(actual_r, rotation, atol=1e-12)
assert np.allclose(actual_t, translation, atol=1e-12)
print(
    json.dumps(
        {
            "status": "SYNTHETIC_GEOMETRY_PASS",
            "rms": rms,
            "hardware_execution": False,
            "learned_correspondences": False,
        }
    )
)
