"""Bounded, offline publication checks on a working tree or exact staged blobs.

This is a conservative aid, not a complete secret detector or license review.
It never prints matching secret text. Git-index mode does not trust .gitignore
or the current worktree contents to describe what will actually be committed.
"""

from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
MAX_FILE = 1024 * 1024
MAX_TOTAL = 8 * 1024 * 1024
MAX_FILES = 500
SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".ruff_cache",
    ".pytest_cache",
    "build",
    "dist",
    "htmlcov",
    "local",
}
ROOT_FILES = {
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    "pyproject.toml",
    "requirements-dev.txt",
    "README.md",
    "README.zh-CN.md",
    "LICENSE",
    "NOTICE",
    "THIRD_PARTY_NOTICES.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    "SUPPORT.md",
    "ROADMAP.md",
    "CHANGELOG.md",
    "CITATION.cff",
    "MANIFEST.in",
}
ROOT_DIRS = {
    ".github",
    "rdk_lab",
    "tools",
    "tests",
    "schemas",
    "docs",
    "examples",
    "recipes",
    "registry",
    "reports",
    "templates",
    "LICENSES",
}
TEXT_SUFFIXES = {".md", ".py", ".json", ".txt", ".toml", ".yaml", ".yml", ".svg", ".cff"}
REQUIRED = ROOT_FILES - {"MANIFEST.in"} | {
    ".github/workflows/ci.yml",
    ".github/CODEOWNERS",
    ".github/dependabot.yml",
    "rdk_lab/py.typed",
    "rdk_lab/data/catalogue.json",
    "docs/results.md",
    "docs/catalogue.md",
    "schemas/result.schema.json",
    "schemas/fixture.schema.json",
    "schemas/catalogue.schema.json",
    "reports/observations.json",
    "reports/source-sbom.spdx.json",
    "LICENSES/CC0-1.0.txt",
    "recipes/weighted_kabsch_6d/LICENSE",
}
PATTERNS = {
    "token-like material": re.compile(
        r"\b(?:sk[-_][A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{24,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16})\b"
    ),
    "private key": re.compile(r"-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----"),
    "SSH key": re.compile(r"ssh-(?:rsa|ed25519)\s+[A-Za-z0-9+/]{30,}"),
    "private IPv4 endpoint": re.compile(
        r"(?<![\w.])(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}|169\.254(?:\.\d{1,3}){2})(?![\w.])"
    ),
    "absolute drive path": re.compile(r"(?i)(?<![a-z0-9])[a-z]:[\\/]"),
    "personal home path": re.compile(r"/(?:home|Users)/[A-Za-z0-9_.-]+/"),
    "URL user credentials": re.compile(r"https?://[^\s/@]+:[^\s/@]+@"),
}
LINKS = re.compile(r"\[[^\]\n]*\]\(([^)\n]+)\)|(?:href|src)=[\"']([^\"']+)[\"']")


class AuditError(ValueError):
    """Publication failed without echoing potentially sensitive contents."""


def approved_path(name: str) -> bool:
    path = PurePosixPath(name)
    if (
        path.is_absolute()
        or any(p in {"", ".", ".."} for p in name.split("/"))
        or "\\" in name
        or ":" in name
    ):
        return False
    if len(path.parts) == 1:
        return name in ROOT_FILES
    if path.parts[0] not in ROOT_DIRS:
        return False
    if any(p.startswith(".env") or p in SKIP_DIRS or p.endswith(".egg-info") for p in path.parts):
        return False
    return path.suffix in TEXT_SUFFIXES or path.name in {
        "LICENSE",
        "NOTICE",
        "CODEOWNERS",
        "py.typed",
    }


def read_worktree(root: Path) -> dict[str, bytes]:
    blobs = {}
    for directory, directories, files in os.walk(root, followlinks=False):
        for name in list(directories):
            path = Path(directory) / name
            if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
                raise AuditError("symlink/junction directory in public tree")
            if name in SKIP_DIRS or name.endswith(".egg-info"):
                directories.remove(name)
        for name in files:
            if (
                name.startswith(".coverage")
                or name in {"coverage.xml", ".DS_Store", "Thumbs.db"}
                or name.endswith((".pyc", ".pyo"))
            ):
                continue
            path = Path(directory) / name
            if path.is_symlink() or not path.is_file():
                raise AuditError("non-regular public file")
            relative = path.relative_to(root).as_posix()
            if path.stat().st_size > MAX_FILE:
                raise AuditError(f"oversized file: {relative}")
            blobs[relative] = path.read_bytes()
            if len(blobs) > MAX_FILES or sum(map(len, blobs.values())) > MAX_TOTAL:
                raise AuditError("publication budget exceeded")
    return blobs


def read_index(root: Path) -> dict[str, bytes]:
    raw = subprocess.run(
        ["git", "ls-files", "--stage", "-z"], cwd=root, check=True, capture_output=True
    ).stdout
    blobs = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        meta, path = record.split(b"\t", 1)
        mode, oid, stage = meta.decode("ascii").split()
        name = path.decode("utf-8")
        if mode not in {"100644", "100755"} or stage != "0":
            raise AuditError(f"non-regular or unresolved index entry: {name}")
        size = int(
            subprocess.run(
                ["git", "cat-file", "-s", oid], cwd=root, check=True, capture_output=True
            ).stdout
        )
        if size > MAX_FILE or len(blobs) >= MAX_FILES:
            raise AuditError("index publication budget exceeded")
        blobs[name] = subprocess.run(
            ["git", "cat-file", "blob", oid], cwd=root, check=True, capture_output=True
        ).stdout
        if sum(map(len, blobs.values())) > MAX_TOTAL:
            raise AuditError("index total size exceeded")
    return blobs


def anchors(text: str) -> set[str]:
    text = re.sub(r"(?ms)^```.*?^```[^\n]*$", "", text)
    seen = {}
    result = set()
    for heading in re.findall(r"(?m)^#{1,6}\s+(.+)$", text):
        slug = re.sub(r"[^\w\s-]", "", re.sub(r"<[^>]*>", "", heading).lower()).replace(" ", "-")
        count = seen.get(slug, 0)
        result.add(slug if count == 0 else f"{slug}-{count}")
        seen[slug] = count + 1
    return result


def check_links(name: str, text: str, blobs: dict[str, bytes]) -> list[str]:
    errors = []
    text = re.sub(r"(?ms)^```.*?^```[^\n]*$", "", text)
    for match in LINKS.finditer(text):
        raw = (match.group(1) or match.group(2)).strip().split(' "', 1)[0].strip("<>")
        link = urlsplit(raw)
        if link.scheme in {"https", "mailto"}:
            continue
        if link.scheme or raw.startswith("//"):
            errors.append(f"{name}: unexpected link scheme")
            continue
        relative = unquote(link.path)
        target = (
            posixpath.normpath(posixpath.join(posixpath.dirname(name), relative))
            if relative
            else name
        )
        if target.startswith(("/", "../")) or "\\" in target:
            errors.append(f"{name}: link leaves public tree")
            continue
        is_directory = target == "." or any(p.startswith(target.rstrip("/") + "/") for p in blobs)
        if target not in blobs and not is_directory:
            errors.append(f"{name}: broken local link to {target}")
        elif link.fragment and target in blobs and target.endswith(".md"):
            if unquote(link.fragment) not in anchors(blobs[target].decode("utf-8")):
                errors.append(f"{name}: missing local anchor in {target}")
    return errors


def check_blobs(blobs: dict[str, bytes], required: bool = True) -> list[str]:
    from rdk_lab.io import ValidationError, decode_json

    errors = []
    if required:
        errors.extend(f"missing required file: {p}" for p in sorted(REQUIRED - blobs.keys()))
    if len(blobs) > MAX_FILES or sum(map(len, blobs.values())) > MAX_TOTAL:
        errors.append("publication budget exceeded")
    seen = set()
    for name, raw in sorted(blobs.items()):
        if not approved_path(name):
            errors.append(f"disallowed path or file type: {name}")
        if name.casefold() in seen:
            errors.append(f"case-ambiguous path: {name}")
        seen.add(name.casefold())
        if len(raw) > MAX_FILE:
            errors.append(f"oversized file: {name}")
        try:
            text = raw.decode("utf-8")
        except UnicodeError:
            errors.append(f"non-UTF8 file: {name}")
            continue
        if "\x00" in text or text.startswith("\ufeff"):
            errors.append(f"NUL or byte-order-mark in text: {name}")
        for category, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                errors.append(f"{name}:{text.count(chr(10), 0, match.start()) + 1}: {category}")
        if name.endswith(".json"):
            try:
                decode_json(text)
            except ValidationError:
                errors.append(f"non-strict JSON: {name}")
        if name.endswith(".md"):
            errors.extend(check_links(name, text, blobs))
        if name.endswith(".svg") and re.search(
            r"<\s*(?:script|foreignObject)|\bon\w+\s*=|(?:href|src)\s*=", text, flags=re.I
        ):
            errors.append(f"active or externally linked SVG: {name}")
    return errors


def check_data(blobs: dict[str, bytes]) -> None:
    from jsonschema import Draft202012Validator, FormatChecker

    from rdk_lab.contracts import validate_result
    from rdk_lab.demo import run_demo
    from rdk_lab.io import decode_json

    def parsed(path):
        return decode_json(blobs[path].decode("utf-8"))

    for schema_path, payload in (
        ("schemas/catalogue.schema.json", parsed("rdk_lab/data/catalogue.json")),
        ("schemas/fixture.schema.json", parsed("examples/fixture/manifest.json")),
        ("schemas/result.schema.json", run_demo()["receipt"]),
    ):
        schema = parsed(schema_path)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(payload)
    validate_result(run_demo()["receipt"])
    catalogue = parsed("rdk_lab/data/catalogue.json")
    ids = {row["id"] for row in catalogue["entries"]}
    if len(ids) != len(catalogue["entries"]):
        raise AuditError("duplicate catalogue IDs")
    if any(not set(item["ids"]).issubset(ids) for item in catalogue["overlaps"]):
        raise AuditError("unknown overlap IDs")
    observations = parsed("reports/observations.json")
    if (
        observations["raw_evidence_bundled"] is not False
        or observations["independently_reproducible_from_public_release"] is not False
    ):
        raise AuditError("historical evidence scope changed; review required")
    if observations["evidence_level"] != "maintainer_reported_private_run":
        raise AuditError("historical observations cannot impersonate public replay")
    for row in observations["observations"]:
        if not re.fullmatch(r"[0-9a-f]{64}", row["original_receipt_sha256"]):
            raise AuditError("invalid original receipt commitment")
        if "FAIL" in row["outcome"] and row.get("numeric_gate_pass") is True:
            raise AuditError("failed observation promoted to numeric PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--git-index",
        action="store_true",
        help="audit staged bytes, including forced ignored paths",
    )
    args = parser.parse_args()
    try:
        blobs = read_index(ROOT) if args.git_index else read_worktree(ROOT)
        errors = check_blobs(blobs)
        if errors:
            for error in errors:
                print(error)
            return 1
        check_data(blobs)
    except (AuditError, OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(f"Publication check rejected input ({type(error).__name__}); no content echoed.")
        return 1
    print(
        json.dumps(
            {
                "status": "PUBLICATION_CHECK_PASS",
                "scope": "git_index" if args.git_index else "worktree",
                "files": len(blobs),
                "bytes": sum(map(len, blobs.values())),
                "manual_review_still_required": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
