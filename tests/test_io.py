import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rdk_lab.io import (
    ValidationError,
    canonical_bytes,
    canonical_sha256,
    decode_json,
    digest_valid,
    load_json,
    safe_file,
    sha256_file,
    verify_manifest,
    write_new_json,
)


class JsonTests(unittest.TestCase):
    def test_roundtrip(self):
        value = {"b": [1, True, None], "a": "中文"}
        self.assertEqual(decode_json(canonical_bytes(value).decode()), value)
        self.assertEqual(
            canonical_sha256(value), hashlib.sha256(canonical_bytes(value)).hexdigest()
        )

    def test_reject_bad_json(self):
        for value in (
            '{"x":1,"x":2}',
            '{"a":{"b":1,"b":2}}',
            "NaN",
            "Infinity",
            "-Infinity",
            "1e999",
            "[1e999]",
            "{",
            "\ufeff{}",
        ):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                decode_json(value)

    def test_digest_validation(self):
        self.assertTrue(digest_valid("a" * 64))
        for value in (None, True, "A" * 64, "a" * 63, "g" * 64, [], 7):
            self.assertFalse(digest_valid(value))

    def test_file_bounds(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "sample.json"
            with self.assertRaises(ValidationError):
                load_json(file)
            file.write_bytes(b"{}")
            self.assertEqual(load_json(file), {})
            with self.assertRaises(ValidationError):
                load_json(file, max_bytes=1)
            file.write_bytes(b"\xff")
            with self.assertRaises(ValidationError):
                load_json(file)

    def test_write_once(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "nested/result.json"
            write_new_json(file, {"ok": True})
            before = file.read_bytes()
            with self.assertRaises(ValidationError):
                write_new_json(file, {"ok": False})
            self.assertEqual(file.read_bytes(), before)
            self.assertEqual(list(file.parent.glob("*.partial")), [])

    def test_atomic_publish_failure_removes_own_temp(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "result.json"
            with (
                patch("rdk_lab.io.os.link", side_effect=OSError("test filesystem failure")),
                self.assertRaises(OSError),
            ):
                write_new_json(file, {"ok": True})
            self.assertEqual(list(Path(directory).iterdir()), [])


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "value.txt").write_text("first-party synthetic data\n", encoding="utf-8")
        file = self.root / "value.txt"
        self.doc = {
            "schema_version": 1,
            "fixture_id": "test-fixture",
            "files": [
                {
                    "path": "value.txt",
                    "size_bytes": file.stat().st_size,
                    "sha256": sha256_file(file),
                }
            ],
        }
        self.manifest = self.root / "manifest.json"

    def run_doc(self, doc=None):
        self.manifest.write_text(json.dumps(self.doc if doc is None else doc), encoding="utf-8")
        return verify_manifest(self.manifest)

    def test_good_manifest(self):
        result = self.run_doc()
        self.assertEqual(result["status"], "INTEGRITY_PASS")
        self.assertEqual(result["file_count"], 1)
        self.assertFalse(result["hardware_execution"])

    def test_unsafe_paths(self):
        paths = (
            "",
            "/etc/passwd",
            "../value.txt",
            "a/../value.txt",
            "./value.txt",
            "a//b",
            "Z" + ":/value.txt",
            "a\\b",
            "a\x00b",
            "value.txt ",
            "value.txt.",
            True,
            None,
        )
        for path in paths:
            with self.subTest(path=path), self.assertRaises(ValidationError):
                safe_file(self.root, path)

    def test_nonexistent_or_directory(self):
        for path in ("missing", "directory"):
            if path == "directory":
                (self.root / path).mkdir()
            with self.assertRaises(ValidationError):
                safe_file(self.root, path)
        with self.assertRaises(ValidationError):
            safe_file(self.root / "missing", "value.txt")

    def test_content_tamper(self):
        self.run_doc()
        (self.root / "value.txt").write_bytes(b"x" * self.doc["files"][0]["size_bytes"])
        with self.assertRaisesRegex(ValidationError, "SHA-256 mismatch"):
            self.run_doc()

    def test_invalid_entry(self):
        for field, value in (
            ("size_bytes", True),
            ("size_bytes", -1),
            ("size_bytes", 999),
            ("sha256", "a"),
            ("path", "../value.txt"),
        ):
            from copy import deepcopy

            doc = deepcopy(self.doc)
            doc["files"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValidationError):
                self.run_doc(doc)

    def test_duplicate_and_wrong_root(self):
        self.doc["files"].append(self.doc["files"][0].copy())
        with self.assertRaises(ValidationError):
            self.run_doc()
        for doc in (
            [],
            {},
            {"schema_version": 1, "fixture_id": "a", "files": []},
            {"schema_version": True, "fixture_id": "a", "files": []},
        ):
            with self.subTest(doc=doc), self.assertRaises(ValidationError):
                self.run_doc(doc)

    def test_bad_fields(self):
        from copy import deepcopy

        for change in (
            {"fixture_id": " "},
            {"files": [1]},
            {"files": [{"path": "value.txt"}]},
            {"extra": True},
        ):
            doc = deepcopy(self.doc)
            doc.update(change)
            with self.subTest(change=change), self.assertRaises(ValidationError):
                self.run_doc(doc)

    def test_symlink_file_and_parent(self):
        try:
            os.symlink(self.root / "value.txt", self.root / "link.txt")
            (self.root / "real").mkdir()
            (self.root / "real/f.txt").write_text("x")
            os.symlink(self.root / "real", self.root / "linkdir", target_is_directory=True)
        except OSError:
            self.skipTest("symlink creation not available to this Windows account")
        for path in ("link.txt", "linkdir/f.txt"):
            with self.subTest(path=path), self.assertRaises(ValidationError):
                safe_file(self.root, path)
        with self.assertRaises(ValidationError):
            safe_file(self.root / "linkdir", "f.txt")
