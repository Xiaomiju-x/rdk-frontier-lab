import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rdk_lab import __version__
from rdk_lab.catalog import load_catalog, select_entries
from rdk_lab.cli import main
from rdk_lab.demo import run_demo
from rdk_lab.io import ValidationError, write_new_json
from tests.helpers import result_for


class CatalogTests(unittest.TestCase):
    def test_snapshot(self):
        doc = load_catalog()
        self.assertEqual(doc["counting_unit"], "registry_entry_not_unique_model_or_success_count")
        self.assertGreater(len(doc["entries"]), 40)
        self.assertEqual(len(doc["entries"]), len({r["id"] for r in doc["entries"]}))
        self.assertTrue(all(not r["bundled_full_upstream_model"] for r in doc["entries"]))

    def test_filters(self):
        self.assertTrue(all("s600" in r["intended_targets"] for r in select_entries("s600")))
        self.assertTrue(all(r["group"] == "official" for r in select_entries(group="official")))
        for kwargs in ({"target": "invalid"}, {"group": "invalid"}):
            with self.assertRaises(ValidationError):
                select_entries(**kwargs)

    def test_corrupt_catalog(self):
        for doc in (
            {},
            {"schema_version": 1, "entries": None},
            {"schema_version": 1, "entries": [{"id": "x"}, {"id": "x"}]},
        ):
            with (
                patch("rdk_lab.catalog.decode_json", return_value=doc),
                self.assertRaises(ValidationError),
            ):
                load_catalog()


class CliTests(unittest.TestCase):
    def invoke(self, *argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(list(argv))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_doctor(self):
        code, out, err = self.invoke("doctor")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["version"], __version__)
        self.assertFalse(json.loads(out)["automatic_downloads"])
        self.assertEqual(err, "")

    def test_catalog_modes(self):
        code, out, _ = self.invoke("catalog", "--group", "frontier", "--json")
        self.assertEqual(code, 0)
        self.assertGreater(json.loads(out)["entry_count"], 0)
        code, out, _ = self.invoke("catalog", "--target", "x5")
        self.assertEqual(code, 0)
        self.assertIn("not a deployment count", out)

    def test_demo_deterministic(self):
        a, b = run_demo(), run_demo()
        self.assertEqual(a, b)
        self.assertEqual(a["review"]["decision"], "DEMO_PASS")
        code, out, _ = self.invoke("demo")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), a)

    def test_demo_failure_visible(self):
        with patch(
            "rdk_lab.demo.compare_vectors",
            return_value={"max_abs": 99.0, "relative_l2": 99.0, "cosine": 0.0},
        ):
            self.assertEqual(run_demo()["review"]["decision"], "DEMO_FAIL")
            self.assertEqual(self.invoke("demo")[0], 1)

    def test_write_evaluate_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            file = str(Path(directory) / "demo.json")
            self.assertEqual(self.invoke("demo", "--output", file)[0], 0)
            self.assertEqual(self.invoke("evaluate", file)[0], 0)
            self.assertEqual(self.invoke("demo", "--output", file)[0], 1)
            self.assertEqual(self.invoke("evaluate", str(Path(directory) / "missing.json"))[0], 1)

    def test_evaluate_failure_and_incomplete(self):
        with tempfile.TemporaryDirectory() as directory:
            for stage, expected in (("FAIL", 1), ("NOT_RUN", 2)):
                path = Path(directory) / f"{stage}.json"
                row = result_for()
                row["stages"]["numeric"] = stage
                write_new_json(path, row)
                self.assertEqual(self.invoke("evaluate", str(path))[0], expected)

    def test_compare(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for target in ("x5", "s100", "s600"):
                path = Path(directory) / f"{target}.json"
                write_new_json(path, result_for(target))
                paths.append(str(path))
            self.assertEqual(self.invoke("compare", *paths)[0], 0)
            self.assertEqual(self.invoke("compare", *paths[:2])[0], 2)

    def test_fixture_verify(self):
        self.assertEqual(
            self.invoke(
                "verify",
                str(Path(__file__).resolve().parents[1] / "examples/fixture/manifest.json"),
            )[0],
            0,
        )

    def test_bad_arguments(self):
        with self.assertRaises(SystemExit) as raised:
            self.invoke("--version")
        self.assertEqual(raised.exception.code, 0)
        with self.assertRaises(SystemExit) as raised:
            self.invoke("unknown-command")
        self.assertEqual(raised.exception.code, 2)
