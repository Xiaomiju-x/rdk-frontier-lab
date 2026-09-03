import unittest

import numpy as np

from rdk_lab.geometry import weighted_kabsch
from rdk_lab.io import ValidationError


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.points = np.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [0, 1, 0],
                [0, 0, 1],
                [1, 1, 0],
                [1, 0, 1],
                [0, 1, 1],
                [1, 1, 1],
            ],
            dtype=float,
        )
        self.rotation = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]], dtype=float)
        self.translation = np.array([0.2, -0.5, 3.0])
        self.target = self.points @ self.rotation.T + self.translation

    def test_known_transform(self):
        rotation, translation, residual = weighted_kabsch(self.points, self.target, np.ones(8))
        np.testing.assert_allclose(rotation, self.rotation, atol=1e-12)
        np.testing.assert_allclose(translation, self.translation, atol=1e-12)
        self.assertLess(residual, 1e-12)
        self.assertAlmostEqual(np.linalg.det(rotation), 1.0)

    def test_weight_scale_invariant(self):
        a = weighted_kabsch(self.points, self.target, np.arange(1.0, 9.0))
        b = weighted_kabsch(self.points, self.target, np.arange(1.0, 9.0) * 1e200)
        for x, y in zip(a, b, strict=True):
            np.testing.assert_allclose(x, y, atol=1e-12)

    def test_zero_weight_outlier(self):
        target = self.target.copy()
        target[0] += 100
        weights = np.ones(8)
        weights[0] = 0
        rotation, translation, rms = weighted_kabsch(self.points, target, weights)
        np.testing.assert_allclose(rotation, self.rotation, atol=1e-12)
        np.testing.assert_allclose(translation, self.translation, atol=1e-12)
        self.assertLess(rms, 1e-12)

    def test_reflection_not_rotation(self):
        reflected = self.points.copy()
        reflected[:, 0] *= -1
        rotation, _, residual = weighted_kabsch(self.points, reflected, np.ones(8))
        self.assertAlmostEqual(np.linalg.det(rotation), 1.0)
        self.assertGreater(residual, 0.1)

    def test_reject_shapes(self):
        for source, target, weights in (
            ([], [], []),
            (self.points, self.target[:3], np.ones(8)),
            (self.points, self.target, np.ones((8, 1))),
        ):
            with self.assertRaises(ValidationError):
                weighted_kabsch(source, target, weights)

    def test_reject_weights(self):
        for weights in (np.zeros(8), -np.ones(8), np.array([1] * 5 + [0] * 3), np.full(8, np.nan)):
            with self.assertRaises(ValidationError):
                weighted_kabsch(self.points, self.target, weights)

    def test_nonfinite_input(self):
        bad = self.points.copy()
        bad[0, 0] = float("inf")
        with self.assertRaises(ValidationError):
            weighted_kabsch(bad, self.target, np.ones(8))

    def test_degenerate(self):
        for points in (np.ones((8, 3)), np.arange(24.0).reshape(8, 3)):
            with self.assertRaises(ValidationError):
                weighted_kabsch(points, points, np.ones(8))
