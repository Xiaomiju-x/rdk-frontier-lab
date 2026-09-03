"""Publication regressions use synthetic inputs, never actual credentials/devices."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as SchemaError

from rdk_lab.contracts import validate_result
from rdk_lab.demo import run_demo
from tools.build_metadata import ROOT, generated, schemas, source_sbom
from tools.check_distribution import member_safe
from tools.check_publication import (
    AuditError,
    anchors,
    approved_path,
    check_blobs,
    check_data,
    check_links,
    read_index,
    read_worktree,
)


class PublicationTests(unittest.TestCase):
    def test_public_tree_and_data(self):
        blobs = read_worktree(ROOT)
        self.assertEqual(check_blobs(blobs), [])
        check_data(blobs)

    def test_generated_metadata_matches(self):
        for path, text in generated().items():
            self.assertEqual(path.read_text(encoding="utf-8"), text, path.name)

    def test_no_fake_demo_compile_success(self):
        row = run_demo()["receipt"]
        row["stages"]["compile"] = "FAIL"
        self.assertEqual(validate_result(row)["decision"], "DEMO_FAIL")

    def test_path_policy(self):
        for name in (
            ".env",
            "rdk_lab/value.bin",
            "models/model.onnx",
            "../README.md",
            "/README.md",
            "rdk_lab/.venv/test.py",
            "rdk_lab/../bad.py",
            "rdk_lab/.env.example",
            "rdk_lab/a\\b.py",
            "rdk_lab/a:b.py",
        ):
            with self.subTest(name=name):
                self.assertFalse(approved_path(name))
        self.assertTrue(approved_path("recipes/weighted_kabsch_6d/LICENSE"))

    def test_sensitive_inputs_not_echoed(self):
        samples = [
            "sk" + "-" + "X" * 32,
            "ghp" + "_" + "Y" * 40,
            ".".join(("192", "168", "20", "30")),
            ".".join(("10", "20", "30", "40")),
            ".".join(("172", "19", "20", "30")),
            "Z" + ":/personal/file",
            "/".join(("", "home", "example_person", "data")),
            "-----BEGIN " + "PRIVATE KEY-----",
            "https://" + "example:example@domain.invalid",
        ]
        for sample in samples:
            with self.subTest(kind=len(sample)):
                errors = check_blobs({"README.md": sample.encode()}, required=False)
                self.assertTrue(errors)
                self.assertTrue(all(sample not in error for error in errors))

    def test_bad_bytes_case_and_json(self):
        samples = [
            {"README.md": b"\xff"},
            {"README.md": b"a\x00b"},
            {"README.md": b"\xef\xbb\xbfhello"},
            {"README.md": b"a", "Readme.md": b"b"},
            {"reports/bad.json": b'{"x": 1, "x": 2}'},
            {"reports/bad.json": b'{"x": 1e999}'},
            {"docs/assets/bad.svg": b"<svg><script>alert(1)</script></svg>"},
            {"docs/assets/bad.svg": b'<svg onload="bad()"/>'},
            {"README.md": b"x" * (1024 * 1024 + 1)},
        ]
        for sample in samples:
            self.assertTrue(check_blobs(sample, required=False))
        self.assertTrue(check_blobs({}, required=True))

    def test_link_resolution(self):
        blobs = {"README.md": b"# Hello\n", "docs/page.md": b"# Details\n## Again\n## Again\n"}
        self.assertEqual(
            check_links(
                "README.md",
                "[page](docs/page.md#again-1) [docs](docs/) [url](https://example.org)",
                blobs,
            ),
            [],
        )
        for link in (
            "missing.md",
            "../escape.md",
            "docs/page.md#absent",
            "javascript:alert",
            "//example.org",
        ):
            self.assertTrue(check_links("README.md", f"[link]({link})", blobs))
        self.assertEqual(anchors("# A\n# A\n```text\n# Not a heading\n```\n"), {"a", "a-1"})

    def test_runtime_assets_not_shipped_in_archives(self):
        for name in (
            "/file.py",
            "../file.py",
            "pkg/model.bin",
            "pkg/key.pem",
            "pkg/.env",
            "pkg/__pycache__/x.pyc",
            "pkg/a\\b.py",
        ):
            self.assertFalse(member_safe(name))
        self.assertTrue(member_safe("rdk_lab/geometry.py"))

    def test_schemas_and_unknown_fields(self):
        generated_schemas = schemas()
        for schema in generated_schemas.values():
            Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(generated_schemas["result.schema.json"])
        row = run_demo()["receipt"]
        validator.validate(row)
        row["unreviewed"] = True
        with self.assertRaises(SchemaError):
            validator.validate(row)

    def test_sbom_checksum_and_license_scope(self):
        sbom = source_sbom()
        self.assertEqual(sbom, source_sbom())
        for file in sbom["files"]:
            path = ROOT / file["fileName"]
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(), file["checksums"][0]["checksumValue"]
            )
            self.assertFalse(path.name.endswith((".bin", ".hbm", ".whl")))
        self.assertEqual(sbom["packages"][0]["licenseDeclared"], "Apache-2.0 AND MIT AND CC0-1.0")

    def test_observation_promotion_rejected(self):
        blobs = read_worktree(ROOT)
        original = json.loads(blobs["reports/observations.json"])
        for key in ("raw_evidence_bundled", "independently_reproducible_from_public_release"):
            doc = {**original, key: True}
            blobs["reports/observations.json"] = json.dumps(doc).encode()
            with self.assertRaises(AuditError):
                check_data(blobs)


@unittest.skipUnless(shutil.which("git"), "Git is required to test actual staged-blob inspection")
class IndexTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="rdk-index-test-")
        self.root = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)
        self.git("init", "--quiet")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def test_scan_staged_not_worktree_bytes(self):
        marker = "sk" + "-" + "Z" * 32
        path = self.root / "README.md"
        path.write_text(marker, encoding="utf-8")
        self.git("add", "README.md")
        path.write_text("Reviewed public content", encoding="utf-8")
        indexed = read_index(self.root)
        self.assertEqual(indexed["README.md"].decode(), marker)
        self.assertTrue(check_blobs(indexed, required=False))
        self.assertEqual(check_blobs(read_worktree(self.root), required=False), [])

    def test_forced_ignored_file_still_checked(self):
        (self.root / ".gitignore").write_text("*.log\n", encoding="utf-8")
        (self.root / "private.log").write_text("Do not publish", encoding="utf-8")
        self.git("add", "-f", "private.log")
        self.assertIn("private.log", read_index(self.root))
        self.assertTrue(check_blobs(read_index(self.root), required=False))
