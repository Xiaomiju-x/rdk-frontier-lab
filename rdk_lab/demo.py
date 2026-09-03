"""First-party six-number arithmetic replay, explicitly not a neural benchmark."""

from __future__ import annotations

from importlib.resources import files
from typing import Any

from .contracts import validate_result
from .io import canonical_sha256, decode_json
from .numerics import compare_vectors


def run_demo() -> dict[str, Any]:
    fixture = decode_json(
        files("rdk_lab").joinpath("data/demo_fixture.json").read_text(encoding="utf-8")
    )
    source = {"operation": "max(0, 0.5*x + 0.125)", "implementation": "python-scalar-reference-v1"}
    contract = {"max_abs": 1e-12, "relative_l2": 1e-12, "minimum_cosine": 0.999999999999}
    output = [max(0.0, 0.5 * x + 0.125) for x in fixture["input"]]
    metrics = compare_vectors(output, fixture["golden"])
    passed = (
        metrics["max_abs"] <= contract["max_abs"]
        and metrics["relative_l2"] <= contract["relative_l2"]
        and metrics["cosine"] >= contract["minimum_cosine"]
    )
    negative = False
    try:
        compare_vectors([float("nan")], [1.0])
    except ValueError:
        negative = True
    receipt = {
        "schema_version": 1,
        "run_id": "offline-demo-v1",
        "algorithm_id": "scalar-relu-reference",
        "target": "host",
        "march": "host",
        "backend": "CPU",
        "evidence_kind": "synthetic_demo",
        "source_sha256": canonical_sha256(source),
        "fixture_sha256": canonical_sha256(fixture),
        "contract_sha256": canonical_sha256(contract),
        "artifact_sha256": canonical_sha256(source),
        "artifact_suffix": ".json",
        "stages": {
            "compile": "NOT_RUN",
            "execution": "PASS",
            "numeric": "PASS" if passed else "FAIL",
            "task": "PASS" if passed else "FAIL",
            "cleanup": "PASS",
        },
        "hardware_observed": False,
        "deterministic": output == [max(0.0, 0.5 * x + 0.125) for x in fixture["input"]],
        "negative_inputs_rejected": negative,
        "measurement_scope": "not_measured",
        "latencies_ms": [],
        "output_sha256": canonical_sha256(output),
    }
    return {
        "review": validate_result(receipt),
        "receipt": receipt,
        "numeric": metrics,
        "output": output,
        "scope": "six-number arithmetic demo; no learned model, board, GPU, network or timing claim",
    }
