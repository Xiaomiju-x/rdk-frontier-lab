import math
import unittest

from rdk_lab.io import ValidationError
from rdk_lab.numerics import compare_vectors, finite_number, percentile, summarize_latencies, vector


class NumericTests(unittest.TestCase):
    def test_finite_type(self):
        for value in (False, None, "1", float("nan"), float("inf"), 10**1000):
            self.assertFalse(finite_number(value))
        self.assertTrue(finite_number(0))

    def test_vector_invalid(self):
        for value in ([], [True], [float("nan")], "12", ["1"], None):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                vector(value)

    def test_percentile_definition(self):
        self.assertEqual(percentile([4.0, 1.0, 2.0, 3.0], 0.5), 2.5)
        self.assertAlmostEqual(percentile([1.0, 2.0, 3.0, 4.0], 0.9), 3.7)
        self.assertEqual(percentile([4.0], 0.99), 4.0)
        self.assertEqual(percentile([1.0, 4.0], 0), 1.0)
        self.assertEqual(percentile([1.0, 4.0], 1), 4.0)

    def test_invalid_quantile(self):
        for q in (-0.1, 1.1, True, float("nan")):
            with self.assertRaises(ValidationError):
                percentile([1.0, 2.0], q)

    def test_latency(self):
        result = summarize_latencies([1.0, 2.0, 3.0])
        self.assertEqual(result["count"], 3)
        self.assertEqual(result["mean_ms"], 2.0)
        self.assertEqual(result["tasks_per_second"], 500.0)
        for values in ([0.0], [-1.0], [1e-320]):
            with self.assertRaises(ValidationError):
                summarize_latencies(values)

    def test_exact_vectors(self):
        for value in ([0.0, 0.0], [1.0, -2.0, 3.0], [1e300, 1e300]):
            result = compare_vectors(value, value)
            self.assertAlmostEqual(result["cosine"], 1.0)
            self.assertEqual(result["relative_l2"], 0.0)
            self.assertEqual(result["max_abs"], 0.0)

    def test_changed_vectors(self):
        result = compare_vectors([2.0, 4.0], [1.0, 2.0])
        self.assertAlmostEqual(result["relative_l2"], 1.0)
        self.assertAlmostEqual(result["cosine"], 1.0)
        self.assertEqual(result["max_abs"], 2.0)
        self.assertEqual(compare_vectors([-1.0], [1.0])["cosine"], -1.0)
        self.assertEqual(compare_vectors([0.0], [1.0])["cosine"], 0.0)

    def test_undefined_or_overflow(self):
        for a, b in (([1.0], [0.0]), ([1.0], [1.0, 2.0]), ([1e308], [-1e308])):
            with self.subTest(a=a, b=b), self.assertRaises(ValidationError):
                compare_vectors(a, b)
        self.assertTrue(math.isfinite(compare_vectors([1e-300], [2e-300])["relative_l2"]))
