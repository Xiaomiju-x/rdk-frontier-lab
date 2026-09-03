"""Strict JSON and local manifest integrity; no network or process execution."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


class ValidationError(ValueError):
    """Input failed an explicit contract; no result is promoted."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def digest_valid(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _nonfinite(value: str) -> None:
    raise ValidationError(f"non-finite JSON literal: {value}")


def decode_json(text: str) -> Any:
    try:
        result = json.loads(text, object_pairs_hook=_pairs, parse_constant=_nonfinite)
        # 1e999 is valid JSON syntax but is not a finite Python float.
        json.dumps(result, allow_nan=False)
        return result
    except (json.JSONDecodeError, UnicodeError, OverflowError, ValueError, RecursionError) as error:
        raise ValidationError(f"invalid strict JSON: {error}") from error


def load_json(path: Path, max_bytes: int = 4 * 1024 * 1024) -> Any:
    require(path.is_file() and not path.is_symlink(), "JSON must be a regular non-symlink file")
    require(path.stat().st_size <= max_bytes, "JSON exceeds the configured size limit")
    try:
        return decode_json(path.read_text(encoding="utf-8"))
    except UnicodeError as error:
        raise ValidationError("JSON must be UTF-8") from error


def sha256_file(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def write_new_json(path: Path, value: Any) -> None:
    """Publish a complete file without replacing an existing result.

    A same-directory hard link publishes the fully flushed temporary file. The
    operation refuses an existing destination even if it appears concurrently.
    On filesystems without hard links, it fails rather than silently overwrites.
    """
    encoded = canonical_bytes(value)
    require(not path.exists() and not path.is_symlink(), "output already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".rdk-result-", suffix=".partial", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def safe_file(root: Path, relative: object) -> Path:
    """Reject traversal, drive names, ambiguous spelling, and every symlink hop."""
    require(isinstance(relative, str) and bool(relative), "path must be a nonempty string")
    require(not any(c in relative for c in "\\:\x00"), "path must be POSIX-relative")
    parts = relative.split("/")
    require(
        all(p not in {"", ".", ".."} and not p.endswith((" ", ".")) for p in parts),
        "noncanonical path",
    )
    require(not PurePosixPath(relative).is_absolute(), "absolute path forbidden")
    require(root.is_dir() and not root.is_symlink(), "root must be a real directory")
    result = root
    for part in parts:
        result = result / part
        require(not result.is_symlink(), "symlink traversal forbidden")
        if hasattr(result, "is_junction"):
            require(not result.is_junction(), "junction traversal forbidden")
    require(result.resolve().is_relative_to(root.resolve()), "path escapes root")
    require(result.is_file(), "manifest file is absent or not regular")
    return result


def verify_manifest(path: Path) -> dict[str, Any]:
    """Verify a declared allowlist; this does not authorize loading its content."""
    doc = load_json(path)
    require(isinstance(doc, dict), "manifest must be an object")
    require(set(doc) == {"schema_version", "fixture_id", "files"}, "unexpected manifest fields")
    require(type(doc["schema_version"]) is int and doc["schema_version"] == 1, "unsupported schema")
    require(
        isinstance(doc["fixture_id"], str) and bool(doc["fixture_id"].strip()),
        "fixture_id required",
    )
    files = doc["files"]
    require(
        isinstance(files, list) and 0 < len(files) <= 10000, "files must contain 1..10000 entries"
    )
    seen: set[str] = set()
    size = 0
    for entry in files:
        require(
            isinstance(entry, dict) and set(entry) == {"path", "size_bytes", "sha256"},
            "invalid file entry",
        )
        file = safe_file(path.parent, entry["path"])
        folded = entry["path"].casefold()
        require(folded not in seen, "duplicate or case-ambiguous path")
        seen.add(folded)
        require(type(entry["size_bytes"]) is int and entry["size_bytes"] >= 0, "invalid byte size")
        require(digest_valid(entry["sha256"]), "invalid SHA-256")
        require(file.stat().st_size == entry["size_bytes"], "file size mismatch")
        require(sha256_file(file) == entry["sha256"], "file SHA-256 mismatch")
        size += entry["size_bytes"]
    return {
        "status": "INTEGRITY_PASS",
        "fixture_id": doc["fixture_id"],
        "file_count": len(files),
        "total_bytes": size,
        "manifest_sha256": sha256_file(path),
        "hardware_execution": False,
    }
