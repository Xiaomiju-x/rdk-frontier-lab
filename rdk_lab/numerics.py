"""Small standard-library metrics with explicit zero and non-finite semantics."""

from __future__ import annotations

import math
from collections.abc import Sequence

from .io import require


def finite_number(value: object) -> bool:
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def vector(values: Sequence[float]) -> list[float]:
    require(
        isinstance(values, (list, tuple)) and len(values) > 0, "nonempty numeric vector required"
    )
    require(
        all(finite_number(x) for x in values),
        "all vector values must be finite numbers, not booleans",
    )
    return [float(x) for x in values]


def percentile(values: Sequence[float], q: float) -> float:
    """Linear interpolation at (n-1)*q (not nearest-rank)."""
    ordered = sorted(vector(values))
    require(finite_number(q) and 0 <= q <= 1, "quantile must be within [0,1]")
    position = (len(ordered) - 1) * q
    lo, hi = math.floor(position), math.ceil(position)
    weight = position - lo
    return ordered[lo] * (1 - weight) + ordered[hi] * weight


def summarize_latencies(values: Sequence[float]) -> dict[str, float | int]:
    samples = vector(values)
    require(all(x > 0 for x in samples), "timed latencies must be strictly positive")
    mean = math.fsum(x / len(samples) for x in samples)
    require(mean > 0 and finite_number(1000 / mean), "throughput overflow")
    return {
        "count": len(samples),
        "p50_ms": percentile(samples, 0.5),
        "p90_ms": percentile(samples, 0.9),
        "p99_ms": percentile(samples, 0.99),
        "mean_ms": mean,
        "tasks_per_second": 1000 / mean,
    }


def compare_vectors(actual: Sequence[float], golden: Sequence[float]) -> dict[str, float]:
    left, right = vector(actual), vector(golden)
    require(len(left) == len(right), "vector length mismatch")
    # Scaling avoids squared-norm overflow. A zero reference gets no arbitrary epsilon.
    scale = max(max(abs(x) for x in left), max(abs(x) for x in right))
    if scale == 0:
        return {"max_abs": 0.0, "relative_l2": 0.0, "cosine": 1.0}
    a, b = [x / scale for x in left], [x / scale for x in right]
    norm_a, norm_b = math.hypot(*a), math.hypot(*b)
    require(norm_b > 0, "relative error is undefined for a nonzero output against zero golden")
    difference = [x - y for x, y in zip(a, b, strict=True)]
    cosine = (
        0.0
        if norm_a == 0
        else math.fsum((x / norm_a) * (y / norm_b) for x, y in zip(a, b, strict=True))
    )
    metrics = {
        "max_abs": max(abs(x) for x in difference) * scale,
        "relative_l2": math.hypot(*difference) / norm_b,
        "cosine": max(-1.0, min(1.0, cosine)),
    }
    require(all(finite_number(v) for v in metrics.values()), "metric overflow")
    return metrics
