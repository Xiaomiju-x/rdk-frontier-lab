import unittest
from copy import deepcopy

from rdk_lab.contracts import compare_boards, validate_result
from rdk_lab.demo import run_demo
from rdk_lab.io import ValidationError
from tests.helpers import result_for


class ResultTests(unittest.TestCase):
    def test_each_backend(self):
        for target in ("x5", "s100", "s600"):
            for backend in ("CPU", "BPU", "HYBRID"):
                with self.subTest(target=target, backend=backend):
                    self.assertEqual(
                        validate_result(result_for(target, backend))["decision"], backend + "_PASS"
                    )

    def test_demo_cannot_be_board(self):
        row = run_demo()["receipt"]
        self.assertEqual(validate_result(row)["decision"], "DEMO_PASS")
        row["stages"]["numeric"] = "FAIL"
        self.assertEqual(validate_result(row)["decision"], "DEMO_FAIL")
        row = result_for()
        row["evidence_kind"] = "synthetic_demo"
        with self.assertRaises(ValidationError):
            validate_result(row)

    def test_each_failure_stage_retained(self):
        for stage in ("numeric", "task", "cleanup"):
            row = result_for()
            row["stages"][stage] = "FAIL"
            self.assertEqual(validate_result(row)["decision"], "FAIL")

    def test_pending_not_promoted(self):
        for stage in ("numeric", "task", "cleanup"):
            row = result_for()
            row["stages"][stage] = "NOT_RUN"
            self.assertEqual(validate_result(row)["decision"], "INCOMPLETE")
        for field in ("deterministic", "negative_inputs_rejected"):
            row = result_for()
            row[field] = False
            self.assertEqual(validate_result(row)["decision"], "INCOMPLETE")

    def test_compile_does_not_equal_run(self):
        row = result_for()
        row.update(latencies_ms=[], measurement_scope="not_measured", hardware_observed=False)
        row["stages"].update(execution="NOT_RUN", numeric="NOT_RUN", task="NOT_RUN")
        self.assertEqual(validate_result(row)["decision"], "INCOMPLETE")
        row["stages"]["compile"] = "FAIL"
        self.assertEqual(validate_result(row)["decision"], "FAIL")

    def test_no_success_before_execution(self):
        for field in ("numeric", "task"):
            row = result_for()
            row.update(latencies_ms=[], measurement_scope="not_measured")
            row["stages"].update(execution="NOT_RUN", numeric="NOT_RUN", task="NOT_RUN")
            row["stages"][field] = "PASS"
            with self.assertRaises(ValidationError):
                validate_result(row)

    def test_bad_fields(self):
        changes = {
            "schema_version": [True, 2],
            "run_id": ["", "UPPER", "x/y", None],
            "algorithm_id": ["x y", []],
            "target": ["s100p", [], None],
            "backend": ["CUDA", []],
            "evidence_kind": ["demo", []],
            "march": ["nash-e", None],
            "hardware_observed": [1, False],
            "deterministic": ["true"],
            "negative_inputs_rejected": [None],
            "artifact_suffix": [".bin", []],
            "measurement_scope": ["fast", []],
            "latencies_ms": [[0.0], [-1.0], [True], [float("inf")], None],
        }
        for field, values in changes.items():
            for value in values:
                row = result_for()
                row[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValidationError):
                    validate_result(row)

    def test_bad_digests(self):
        for field in (
            "source_sha256",
            "fixture_sha256",
            "contract_sha256",
            "artifact_sha256",
            "output_sha256",
        ):
            row = result_for()
            row[field] = "not-a-digest"
            with self.assertRaises(ValidationError):
                validate_result(row)

    def test_missing_extra_root(self):
        for value in (None, [], {}, {**result_for(), "extra": 1}):
            with self.assertRaises(ValidationError):
                validate_result(value)

    def test_bad_stages(self):
        for value in (
            None,
            {},
            {**result_for()["stages"], "task": []},
            {**result_for()["stages"], "numeric": "OK"},
        ):
            row = result_for()
            row["stages"] = value
            with self.assertRaises(ValidationError):
                validate_result(row)

    def test_compile_execution_contradiction(self):
        row = result_for()
        row["stages"]["compile"] = "NOT_RUN"
        with self.assertRaises(ValidationError):
            validate_result(row)
        row = result_for()
        row["stages"]["execution"] = "NOT_RUN"
        with self.assertRaises(ValidationError):
            validate_result(row)
        row = result_for()
        row["measurement_scope"] = "not_measured"
        with self.assertRaises(ValidationError):
            validate_result(row)

    def test_host_rules(self):
        row = run_demo()["receipt"]
        row["backend"] = "BPU"
        with self.assertRaises(ValidationError):
            validate_result(row)
        row = result_for(backend="CPU")
        row["artifact_suffix"] = {}
        with self.assertRaises(ValidationError):
            validate_result(row)


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.rows = [result_for(t) for t in ("x5", "s100", "s600")]

    def test_complete_contract(self):
        result = compare_boards(self.rows)
        self.assertEqual(result["status"], "CROSS_BOARD_CONTRACT_PASS")
        self.assertFalse(result["independent_reproduction_certified"])

    def test_missing_target(self):
        self.assertEqual(compare_boards(self.rows[:2])["status"], "INCOMPLETE")

    def test_numeric_failure(self):
        self.rows[1]["stages"]["numeric"] = "FAIL"
        self.assertEqual(compare_boards(self.rows)["status"], "NEGATIVE")

    def test_incomplete_gate_or_timings(self):
        for scenario in ("numeric", "timings"):
            rows = deepcopy(self.rows)
            if scenario == "numeric":
                rows[0]["stages"]["numeric"] = "NOT_RUN"
            else:
                rows[0]["latencies_ms"] = []
            self.assertEqual(compare_boards(rows)["status"], "INCOMPLETE")

    def test_mismatched_provenance(self):
        for key in (
            "source_sha256",
            "fixture_sha256",
            "contract_sha256",
            "algorithm_id",
            "measurement_scope",
        ):
            rows = deepcopy(self.rows)
            rows[0][key] = (
                "f" * 64
                if "sha256" in key
                else ("other-model" if key == "algorithm_id" else "process")
            )
            with self.subTest(key=key), self.assertRaises(ValidationError):
                compare_boards(rows)

    def test_no_binary_reuse(self):
        self.rows[1]["artifact_sha256"] = self.rows[2]["artifact_sha256"]
        with self.assertRaises(ValidationError):
            compare_boards(self.rows)

    def test_duplicates_and_wrong_backend(self):
        for rows in (
            [],
            self.rows * 2,
            [self.rows[0], self.rows[0]],
            [run_demo()["receipt"]],
            [result_for(backend="CPU")],
        ):
            with self.subTest(rows=rows), self.assertRaises(ValidationError):
                compare_boards(rows)
