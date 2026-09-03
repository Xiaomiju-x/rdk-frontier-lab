"""Receipt validation and three-board comparison, separate from execution.

This is a consistency gate, not remote attestation. A contributor can fabricate
JSON; reviewers must still inspect provenance and independently reproduce it.
"""

from __future__ import annotations

import re
from typing import Any

from .io import digest_valid, require
from .numerics import finite_number, summarize_latencies

TARGETS = {"x5": ("bayes-e", ".bin"), "s100": ("nash-e", ".hbm"), "s600": ("nash-p", ".hbm")}
STATES = {"PASS", "FAIL", "NOT_RUN", "BLOCKED"}
_ID = re.compile(r"[a-z0-9][a-z0-9_.-]{0,95}\Z")


def validate_result(result: Any) -> dict[str, Any]:
    require(isinstance(result, dict), "result must be an object")
    keys = {
        "schema_version",
        "run_id",
        "algorithm_id",
        "target",
        "march",
        "backend",
        "evidence_kind",
        "source_sha256",
        "fixture_sha256",
        "contract_sha256",
        "artifact_sha256",
        "artifact_suffix",
        "stages",
        "hardware_observed",
        "deterministic",
        "negative_inputs_rejected",
        "measurement_scope",
        "latencies_ms",
        "output_sha256",
    }
    require(set(result) == keys, "missing or unexpected result fields")
    require(
        type(result["schema_version"]) is int and result["schema_version"] == 1,
        "unsupported result schema",
    )
    for key in ("run_id", "algorithm_id"):
        require(
            isinstance(result[key], str) and _ID.fullmatch(result[key]) is not None,
            f"invalid {key}",
        )
    require(
        isinstance(result["target"], str) and result["target"] in {"host", *TARGETS},
        "unsupported target",
    )
    require(
        isinstance(result["backend"], str) and result["backend"] in {"CPU", "BPU", "HYBRID"},
        "unsupported backend",
    )
    require(
        isinstance(result["evidence_kind"], str)
        and result["evidence_kind"] in {"synthetic_demo", "machine_observation"},
        "unknown evidence kind",
    )
    for key in ("hardware_observed", "deterministic", "negative_inputs_rejected"):
        require(type(result[key]) is bool, f"{key} must be boolean")
    for key in (
        "source_sha256",
        "fixture_sha256",
        "contract_sha256",
        "artifact_sha256",
        "output_sha256",
    ):
        require(digest_valid(result[key]), f"invalid {key}")
    target, backend = result["target"], result["backend"]
    if target == "host":
        require(backend == "CPU" and result["march"] == "host", "host receipt cannot claim a BPU")
    else:
        require(result["march"] == TARGETS[target][0], "target/march mismatch")
    if backend in {"BPU", "HYBRID"}:
        require(result["artifact_suffix"] == TARGETS[target][1], "wrong target artifact suffix")
    else:
        require(
            isinstance(result["artifact_suffix"], str)
            and result["artifact_suffix"] in {".onnx", ".json", ".py"},
            "unsupported CPU artifact type",
        )
    stages = result["stages"]
    require(
        isinstance(stages, dict)
        and set(stages) == {"compile", "execution", "numeric", "task", "cleanup"},
        "invalid stage fields",
    )
    require(all(isinstance(v, str) and v in STATES for v in stages.values()), "unknown stage state")
    require(
        isinstance(result["measurement_scope"], str)
        and result["measurement_scope"]
        in {"model_call", "file_to_file", "process", "not_measured"},
        "unknown measurement boundary",
    )
    samples = result["latencies_ms"]
    require(
        isinstance(samples, list) and len(samples) <= 100000, "latencies must be a bounded list"
    )
    require(
        all(finite_number(x) and x > 0 for x in samples),
        "latencies must be positive finite numbers",
    )
    if stages["execution"] != "PASS":
        require(
            not samples and result["measurement_scope"] == "not_measured",
            "failed/unrun execution cannot publish successful timing",
        )
        require(
            stages["numeric"] != "PASS" and stages["task"] != "PASS",
            "unrun execution cannot pass numeric/task gates",
        )
    if samples:
        require(
            result["measurement_scope"] != "not_measured", "measured samples require a boundary"
        )
    if result["evidence_kind"] == "synthetic_demo":
        require(
            target == "host" and backend == "CPU" and not result["hardware_observed"],
            "demo cannot impersonate a board",
        )
    if target != "host" and stages["execution"] == "PASS":
        require(
            result["hardware_observed"] and result["evidence_kind"] == "machine_observation",
            "board execution requires recorded hardware observation",
        )
    if backend in {"BPU", "HYBRID"} and stages["execution"] == "PASS":
        require(stages["compile"] == "PASS", "BPU execution requires independent compile PASS")
    all_required = all(stages[k] == "PASS" for k in ("execution", "numeric", "task", "cleanup"))
    all_required = all_required and result["deterministic"] and result["negative_inputs_rejected"]
    all_required = all_required and not any(value == "FAIL" for value in stages.values())
    if result["evidence_kind"] == "synthetic_demo":
        decision = "DEMO_PASS" if all_required else "DEMO_FAIL"
    elif any(stages[k] == "FAIL" for k in stages):
        decision = "FAIL"
    elif not all_required:
        decision = "INCOMPLETE"
    else:
        decision = f"{backend}_PASS"
    return {
        "decision": decision,
        "target": target,
        "backend": backend,
        "metrics": summarize_latencies(samples) if samples else None,
        "public_benchmark_certified": False,
    }


def compare_boards(results: list[dict[str, Any]]) -> dict[str, Any]:
    require(isinstance(results, list) and 0 < len(results) <= 3, "provide one to three results")
    reviews = [validate_result(row) for row in results]
    seen: set[str] = set()
    for row in results:
        require(
            row["target"] in TARGETS and row["target"] not in seen, "duplicate or non-board target"
        )
        seen.add(row["target"])
        require(row["backend"] == "BPU", "cross-board profile requires BPU-only evidence")
    for key in (
        "algorithm_id",
        "source_sha256",
        "fixture_sha256",
        "contract_sha256",
        "measurement_scope",
    ):
        require(len({row[key] for row in results}) == 1, f"non-comparable {key}")
    require(
        len({row["artifact_sha256"] for row in results}) == len(results),
        "cross-board binary reuse forbidden",
    )
    if any(r["decision"] == "FAIL" for r in reviews):
        status = "NEGATIVE"
    elif seen != set(TARGETS) or any(
        r["decision"] != "BPU_PASS" or r["metrics"] is None for r in reviews
    ):
        status = "INCOMPLETE"
    else:
        status = "CROSS_BOARD_CONTRACT_PASS"
    return {"status": status, "boards": reviews, "independent_reproduction_certified": False}
