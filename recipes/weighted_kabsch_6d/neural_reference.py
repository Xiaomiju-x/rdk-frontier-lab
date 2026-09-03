# SPDX-License-Identifier: MIT
# Copyright (c) 2026 C14 package contributors
"""First-party MIT 6D pose components.

This module is deliberately not NVIDIA FoundationPose.  The only neural
component scores already established RGB-D/mesh correspondences.  A validated
weighted Kabsch solve remains an explicit CPU/GPU geometry partition.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import torch
from torch import nn

N_MATCHES = 128
FEATURE_CHANNELS = 9
OBJECT_SCALE_M = 0.08
CAMERA_CENTER_SCALE_M = 0.20
DEPTH_ERROR_SCALE_M = 0.10


class MatchWeightMicro(nn.Module):
    """Static pointwise confidence scorer: [B, 9, 1, 128] -> [B, 1, 1, 128]."""

    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(FEATURE_CHANNELS, 32, 1),
            nn.ReLU(inplace=False),
            nn.Conv2d(32, 32, 1),
            nn.ReLU(inplace=False),
            nn.Conv2d(32, 16, 1),
            nn.ReLU(inplace=False),
            nn.Conv2d(16, 1, 1),
            nn.Sigmoid(),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.net(features) * features[:, 8:9, :, :]


def build_features_np(
    object_points_m: np.ndarray,
    camera_points_m: np.ndarray,
    color_error: np.ndarray,
    depth_error_m: np.ndarray,
    valid: np.ndarray,
) -> np.ndarray:
    """Create the static neural partition input without hiding pose geometry."""
    object_points_m = np.asarray(object_points_m, dtype=np.float32)
    camera_points_m = np.asarray(camera_points_m, dtype=np.float32)
    color_error = np.asarray(color_error, dtype=np.float32).reshape(-1)
    depth_error_m = np.asarray(depth_error_m, dtype=np.float32).reshape(-1)
    valid = np.asarray(valid, dtype=np.float32).reshape(-1)
    if object_points_m.shape != (N_MATCHES, 3):
        raise ValueError(f"object_points_m must be {(N_MATCHES, 3)}, got {object_points_m.shape}")
    if camera_points_m.shape != (N_MATCHES, 3):
        raise ValueError(f"camera_points_m must be {(N_MATCHES, 3)}, got {camera_points_m.shape}")
    for name, array in {
        "object_points_m": object_points_m,
        "camera_points_m": camera_points_m,
        "color_error": color_error,
        "depth_error_m": depth_error_m,
        "valid": valid,
    }.items():
        if not np.isfinite(array).all():
            raise ValueError(f"{name} contains non-finite values")
    if (
        color_error.shape != (N_MATCHES,)
        or depth_error_m.shape != (N_MATCHES,)
        or valid.shape != (N_MATCHES,)
    ):
        raise ValueError("cue and valid arrays must each have 128 entries")
    valid_bool = valid > 0.5
    if int(valid_bool.sum()) < 6:
        raise ValueError("at least six valid correspondences are required")
    if np.any(color_error < 0.0) or np.any(depth_error_m < 0.0):
        raise ValueError("error cues must be non-negative")
    center = camera_points_m[valid_bool].mean(axis=0, keepdims=True)
    features = np.concatenate(
        [
            object_points_m / OBJECT_SCALE_M,
            (camera_points_m - center) / CAMERA_CENTER_SCALE_M,
            color_error[:, None],
            depth_error_m[:, None] / DEPTH_ERROR_SCALE_M,
            valid[:, None],
        ],
        axis=1,
    ).T[None, :, None, :]
    if features.shape != (1, FEATURE_CHANNELS, 1, N_MATCHES):
        raise AssertionError(features.shape)
    return np.ascontiguousarray(features, dtype=np.float32)


def _validate_geometry(
    object_points: torch.Tensor, camera_points: torch.Tensor, weights: torch.Tensor
) -> None:
    if object_points.ndim != 3 or object_points.shape[-1] != 3:
        raise ValueError("object_points must be [B,N,3]")
    if camera_points.shape != object_points.shape:
        raise ValueError("camera_points must match object_points")
    if weights.ndim != 2 or weights.shape != object_points.shape[:2]:
        raise ValueError("weights must be [B,N]")
    if (
        not torch.isfinite(object_points).all()
        or not torch.isfinite(camera_points).all()
        or not torch.isfinite(weights).all()
    ):
        raise ValueError("geometry contains non-finite values")
    if torch.any(weights < 0):
        raise ValueError("weights must be non-negative")
    if torch.any((weights > 1.0e-4).sum(dim=1) < 6):
        raise ValueError("at least six positively weighted correspondences are required")


def weighted_kabsch(
    object_points: torch.Tensor,
    camera_points: torch.Tensor,
    weights: torch.Tensor,
    *,
    validate: bool = True,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Solve camera_points ~= R @ object_points + t for fixed correspondences."""
    if validate:
        _validate_geometry(object_points, camera_points, weights)
    eps = torch.tensor(1.0e-8, dtype=object_points.dtype, device=object_points.device)
    normalized = weights / torch.clamp(weights.sum(dim=1, keepdim=True), min=eps)
    obj_center = (object_points * normalized[..., None]).sum(dim=1, keepdim=True)
    cam_center = (camera_points * normalized[..., None]).sum(dim=1, keepdim=True)
    obj_zero = object_points - obj_center
    cam_zero = camera_points - cam_center
    covariance = torch.matmul((obj_zero * normalized[..., None]).transpose(1, 2), cam_zero)
    u, singular_values, vh = torch.linalg.svd(covariance, full_matrices=False)
    rotation_pre = torch.matmul(vh.transpose(1, 2), u.transpose(1, 2))
    det = torch.linalg.det(rotation_pre)
    sign = torch.where(det < 0.0, -torch.ones_like(det), torch.ones_like(det))
    diagonal = torch.ones(
        (object_points.shape[0], 3), dtype=object_points.dtype, device=object_points.device
    )
    diagonal[:, 2] = sign
    rotation = torch.matmul(
        torch.matmul(vh.transpose(1, 2), torch.diag_embed(diagonal)), u.transpose(1, 2)
    )
    translation = cam_center[:, 0, :] - torch.matmul(rotation, obj_center[:, 0, :, None])[:, :, 0]
    return rotation, translation, singular_values


class FullPoseExportProbe(nn.Module):
    """Honest source graph export probe; SVD is not replaced or approximated."""

    def __init__(self, scorer: MatchWeightMicro) -> None:
        super().__init__()
        self.scorer = scorer

    def forward(
        self,
        features: torch.Tensor,
        object_points: torch.Tensor,
        camera_points: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        weights = self.scorer(features)[:, 0, 0, :]
        rotation, translation, _ = weighted_kabsch(
            object_points, camera_points, weights, validate=False
        )
        return rotation, translation


@dataclass(frozen=True)
class PoseErrors:
    rotation_deg: float
    translation_mm: float
    add_mm: float


def pose_errors(
    rotation: np.ndarray,
    translation: np.ndarray,
    rotation_gt: np.ndarray,
    translation_gt: np.ndarray,
    mesh_points_m: np.ndarray,
) -> PoseErrors:
    relative = np.asarray(rotation, np.float64) @ np.asarray(rotation_gt, np.float64).T
    cosine = float(np.clip((np.trace(relative) - 1.0) * 0.5, -1.0, 1.0))
    rotation_deg = math.degrees(math.acos(cosine))
    translation_mm = float(
        np.linalg.norm(np.asarray(translation) - np.asarray(translation_gt)) * 1000.0
    )
    pred = np.asarray(mesh_points_m) @ np.asarray(rotation).T + np.asarray(translation)[None, :]
    truth = (
        np.asarray(mesh_points_m) @ np.asarray(rotation_gt).T + np.asarray(translation_gt)[None, :]
    )
    add_mm = float(np.linalg.norm(pred - truth, axis=1).mean() * 1000.0)
    return PoseErrors(rotation_deg=rotation_deg, translation_mm=translation_mm, add_mm=add_mm)
