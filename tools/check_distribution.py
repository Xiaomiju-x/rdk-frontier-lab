"""Inspect newly built wheel and sdist without loading or extracting their code."""

from __future__ import annotations

import argparse
import email.parser
import hashlib
import json
import sys
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
LIMIT = 16 * 1024 * 1024


def member_safe(name: str) -> bool:
    path = PurePosixPath(name)
    return (
        not path.is_absolute()
        and "\\" not in name
        and ":" not in name
        and all(
            part not in {"", ".", "..", ".venv", ".git", "__pycache__"} for part in name.split("/")
        )
        and not any(part.startswith(".env") for part in path.parts)
        and path.suffix
        not in {
            ".bin",
            ".hbm",
            ".onnx",
            ".pt",
            ".pth",
            ".safetensors",
            ".pem",
            ".key",
            ".pyc",
            ".log",
        }
    )


def inspect_wheel(path: Path) -> dict:
    from rdk_lab import __version__

    expected_info = f"rdk_frontier_lab-{__version__}.dist-info/"
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if len(names) != len(set(names)) or sum(entry.file_size for entry in entries) > LIMIT:
            raise ValueError("wheel duplicate entries or size budget")
        if any(
            not member_safe(name) or not name.startswith(("rdk_lab/", expected_info))
            for name in names
        ):
            raise ValueError("unexpected wheel member")
        required = {
            "rdk_lab/cli.py",
            "rdk_lab/geometry.py",
            "rdk_lab/py.typed",
            "rdk_lab/data/catalogue.json",
            "rdk_lab/data/demo_fixture.json",
            expected_info + "entry_points.txt",
            expected_info + "licenses/LICENSE",
            expected_info + "licenses/NOTICE",
            expected_info + "licenses/LICENSES/CC0-1.0.txt",
            expected_info + "licenses/recipes/weighted_kabsch_6d/LICENSE",
        }
        if not required.issubset(names):
            raise ValueError("wheel lacks runtime data, CLI or license grants")
        metadata = email.parser.Parser().parsestr(
            archive.read(expected_info + "METADATA").decode("utf-8")
        )
        if metadata["Name"] != "rdk-frontier-lab" or metadata["Version"] != __version__:
            raise ValueError("wheel identity mismatch")
        dependencies = metadata.get_all("Requires-Dist", [])
        if (
            any(
                not value.startswith("numpy<3,>=1.24;") or 'extra == "geometry"' not in value
                for value in dependencies
            )
            or len(dependencies) != 1
        ):
            raise ValueError("unexpected runtime dependencies")
        catalogue = json.loads(archive.read("rdk_lab/data/catalogue.json"))
        if catalogue != json.loads(
            (ROOT / "rdk_lab/data/catalogue.json").read_text(encoding="utf-8")
        ):
            raise ValueError("wheel catalogue differs from reviewed source")
    return {
        "file": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
        "members": len(names),
    }


def inspect_sdist(path: Path) -> dict:
    from rdk_lab import __version__

    prefix = f"rdk_frontier_lab-{__version__}/"
    with tarfile.open(path, "r:gz") as archive:
        entries = archive.getmembers()
        files = [entry for entry in entries if entry.isfile()]
        names = [entry.name for entry in files]
        if len(names) != len(set(names)) or sum(entry.size for entry in entries) > LIMIT:
            raise ValueError("sdist duplicate entries or size budget")
        if any(not (entry.isfile() or entry.isdir()) for entry in entries):
            raise ValueError("sdist links or special files forbidden")
        if any(not member_safe(name) or not name.startswith(prefix) for name in names):
            raise ValueError("unexpected sdist member")
        required = {
            prefix + name
            for name in (
                "pyproject.toml",
                "rdk_lab/cli.py",
                "LICENSE",
                "NOTICE",
                "LICENSES/CC0-1.0.txt",
                "recipes/weighted_kabsch_6d/LICENSE",
                "tests/test_contracts.py",
                "docs/results.md",
                "reports/observations.json",
            )
        }
        if not required.issubset(names):
            raise ValueError("sdist lacks source, tests, documentation or license grants")
    return {
        "file": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
        "members": len(files),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    wheels = sorted(args.dist.glob("*.whl"))
    sdists = sorted(args.dist.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        print("Expected exactly one current wheel and one sdist; use a fresh build directory.")
        return 1
    try:
        rows = [inspect_wheel(wheels[0]), inspect_sdist(sdists[0])]
    except (ValueError, OSError, KeyError, tarfile.TarError, zipfile.BadZipFile) as error:
        print(f"Distribution rejected ({type(error).__name__}).")
        return 1
    print(
        json.dumps(
            {"status": "DISTRIBUTION_CONTENT_PASS", "artifacts": rows}, sort_keys=True, indent=2
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
