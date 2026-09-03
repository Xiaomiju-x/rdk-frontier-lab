from copy import deepcopy

from rdk_lab.contracts import TARGETS
from rdk_lab.demo import run_demo
from rdk_lab.io import canonical_sha256


def result_for(target="s600", backend="BPU"):
    row = deepcopy(run_demo()["receipt"])
    row.update(
        target=target,
        march=TARGETS[target][0],
        backend=backend,
        evidence_kind="machine_observation",
        hardware_observed=True,
        artifact_suffix=TARGETS[target][1] if backend != "CPU" else ".onnx",
        artifact_sha256=canonical_sha256({"test_target": target}),
        latencies_ms=[1.0, 2.0, 3.0],
        measurement_scope="file_to_file",
    )
    row["stages"]["compile"] = "PASS"
    return row
