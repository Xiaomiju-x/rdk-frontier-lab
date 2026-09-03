# SPDX-License-Identifier: MIT
# Copyright (c) 2026 C14 package contributors
"""NumPy-only public port of the first-party weighted Kabsch geometry partition.

Not NVIDIA FoundationPose. Requires established point correspondences and
user-supplied confidence weights; supplies no detector or learned matcher.
"""

from __future__ import annotations

import numpy as np

from .io import require


def weighted_kabsch(object_points, camera_points, weights):
    """Solve camera ~= object @ rotation.T + translation in the same length unit.

    Inputs: two finite (N,3) arrays and a finite, nonnegative (N,) weight vector.
    At least six positive weights and rank >= 2 are required. Returns a proper
    rotation (det +1), translation, and weighted RMS residual. No RANSAC or
    outlier-rejection claim is made.
    """
    source = np.asarray(object_points, dtype=np.float64)
    target = np.asarray(camera_points, dtype=np.float64)
    weight = np.asarray(weights, dtype=np.float64)
    require(source.ndim == 2 and source.shape[1] == 3, "object points must have shape (N,3)")
    require(
        target.shape == source.shape and weight.shape == (len(source),), "geometry shape mismatch"
    )
    require(all(np.isfinite(x).all() for x in (source, target, weight)), "geometry must be finite")
    require(
        bool((weight >= 0).all()) and int((weight > 0).sum()) >= 6, "six positive weights required"
    )
    weight = weight / weight.max()
    weight = weight / weight.sum()
    a, b = (source * weight[:, None]).sum(0), (target * weight[:, None]).sum(0)
    covariance = ((source - a) * weight[:, None]).T @ (target - b)
    require(bool(np.isfinite(covariance).all()), "geometry covariance overflow")
    u, singular, vh = np.linalg.svd(covariance)
    require(
        singular[0] > 0 and singular[1] > singular[0] * 1e-12, "degenerate correspondence geometry"
    )
    correction = np.diag([1.0, 1.0, 1.0 if np.linalg.det(vh.T @ u.T) >= 0 else -1.0])
    rotation = vh.T @ correction @ u.T
    translation = b - rotation @ a
    residual = target - (source @ rotation.T + translation)
    rms = float(np.sqrt((weight * (residual * residual).sum(1)).sum()))
    require(
        bool(np.isfinite(rotation).all() and np.isfinite(translation).all() and np.isfinite(rms)),
        "non-finite pose result",
    )
    return rotation, translation, rms
