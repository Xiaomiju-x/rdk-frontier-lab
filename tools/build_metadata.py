"""Generate schemas and a deterministic SPDX inventory of shipped source.

This is a source inventory, not a claim about a contributor's installed software
or the upstream model assets mentioned in the historical catalogue.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BASE = "https://github.com/Xiaomiju-x/rdk-frontier-lab/raw/main/schemas/"
CREATED = "2026-09-03T09:30:04Z"


def object_schema(properties: dict, **extra) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(properties),
        "properties": properties,
        **extra,
    }


def schemas() -> dict[str, dict]:
    from rdk_lab.contracts import STATES, TARGETS

    digest = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    name = {"type": "string", "pattern": "^[a-z0-9][a-z0-9_.-]{0,95}$"}
    version = {"type": "integer", "const": 1}
    fixture = object_schema(
        {
            "schema_version": version,
            "fixture_id": {"type": "string", "minLength": 1, "pattern": "\\S"},
            "files": {
                "type": "array",
                "minItems": 1,
                "maxItems": 10000,
                "items": object_schema(
                    {
                        "path": {"type": "string", "minLength": 1},
                        "size_bytes": {"type": "integer", "minimum": 0},
                        "sha256": digest,
                    }
                ),
            },
        }
    )
    result = object_schema(
        {
            "schema_version": version,
            "run_id": name,
            "algorithm_id": name,
            "target": {"enum": ["host", *TARGETS]},
            "march": {"enum": ["host", *(v[0] for v in TARGETS.values())]},
            "backend": {"enum": ["CPU", "BPU", "HYBRID"]},
            "evidence_kind": {"enum": ["synthetic_demo", "machine_observation"]},
            "source_sha256": digest,
            "fixture_sha256": digest,
            "contract_sha256": digest,
            "artifact_sha256": digest,
            "artifact_suffix": {"enum": [".bin", ".hbm", ".onnx", ".json", ".py"]},
            "stages": object_schema(
                {
                    k: {"enum": sorted(STATES)}
                    for k in ("compile", "execution", "numeric", "task", "cleanup")
                }
            ),
            "hardware_observed": {"type": "boolean"},
            "deterministic": {"type": "boolean"},
            "negative_inputs_rejected": {"type": "boolean"},
            "measurement_scope": {
                "enum": ["model_call", "file_to_file", "process", "not_measured"]
            },
            "latencies_ms": {
                "type": "array",
                "maxItems": 100000,
                "items": {"type": "number", "exclusiveMinimum": 0},
            },
            "output_sha256": digest,
        }
    )
    catalogue = object_schema(
        {
            "schema_version": version,
            "as_of": {"type": "string", "format": "date-time"},
            "counting_unit": {"const": "registry_entry_not_unique_model_or_success_count"},
            "publication_scope": {"type": "string", "minLength": 1},
            "entries": {
                "type": "array",
                "minItems": 1,
                "items": object_schema(
                    {
                        "id": {"type": "string", "pattern": "^[OCF][0-9]+$"},
                        "name": {"type": "string", "minLength": 1},
                        "group": {"enum": ["official", "frontier", "research"]},
                        "direction": {"type": "string", "minLength": 1},
                        "intended_targets": {
                            "type": "array",
                            "minItems": 1,
                            "uniqueItems": True,
                            "items": {"enum": ["host", *TARGETS]},
                        },
                        "observed_status": {"type": "string", "minLength": 1},
                        "scope_note": {"type": "string", "minLength": 1},
                        "evidence_level": {"const": "maintainer_reported_private_run"},
                        "bundled_full_upstream_model": {"const": False},
                    }
                ),
            },
            "overlaps": {
                "type": "array",
                "items": object_schema(
                    {
                        "ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 2,
                            "uniqueItems": True,
                        },
                        "reason": {"type": "string", "minLength": 1},
                    }
                ),
            },
        }
    )
    return {
        filename: {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": BASE + filename,
            "$comment": "Generated. Python also enforces semantic, path and finite-number gates.",
            **body,
        }
        for filename, body in (
            ("fixture.schema.json", fixture),
            ("result.schema.json", result),
            ("catalogue.schema.json", catalogue),
        )
    }


def source_sbom() -> dict:
    from rdk_lab import __version__

    paths = sorted(
        [p for p in (ROOT / "rdk_lab").rglob("*") if p.is_file() and "__pycache__" not in p.parts]
        + [
            ROOT / "recipes/weighted_kabsch_6d/neural_reference.py",
            ROOT / "examples/geometry_demo.py",
        ]
    )
    files = []
    for index, path in enumerate(paths):
        relative = path.relative_to(ROOT).as_posix()
        data = path.read_bytes()
        license_id = "Apache-2.0"
        if relative in {"rdk_lab/geometry.py", "recipes/weighted_kabsch_6d/neural_reference.py"}:
            license_id = "MIT"
        elif relative == "rdk_lab/data/demo_fixture.json":
            license_id = "CC0-1.0"
        files.append(
            {
                "SPDXID": f"SPDXRef-File-{index:03d}",
                "fileName": "./" + relative,
                "checksums": [
                    {"algorithm": "SHA256", "checksumValue": hashlib.sha256(data).hexdigest()},
                    {"algorithm": "SHA1", "checksumValue": hashlib.sha1(data).hexdigest()},
                ],
                "licenseConcluded": license_id,
                "licenseInfoInFiles": [license_id],
                "copyrightText": "2026 Xiaomiju-x",
            }
        )
    sha1s = sorted(f["checksums"][1]["checksumValue"] for f in files)
    verification = hashlib.sha1("".join(sha1s).encode()).hexdigest()
    identity = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"rdk-frontier-lab-{__version__}-public-source",
        "documentNamespace": f"https://github.com/Xiaomiju-x/rdk-frontier-lab/spdx/{identity}",
        "creationInfo": {
            "created": CREATED,
            "creators": ["Tool: rdk-frontier-lab-build-metadata-0.1.0", "Person: Xiaomiju-x"],
            "comment": "Deterministic release-source inventory. No downloaded dependencies, models, vendor binaries or installed environment are represented. Timestamp is the initial metadata-generation epoch for this release.",
        },
        "packages": [
            {
                "name": "rdk-frontier-lab",
                "SPDXID": "SPDXRef-Package",
                "versionInfo": __version__,
                "downloadLocation": "https://github.com/Xiaomiju-x/rdk-frontier-lab",
                "filesAnalyzed": True,
                "packageVerificationCode": {"packageVerificationCodeValue": verification},
                "licenseConcluded": "Apache-2.0 AND MIT AND CC0-1.0",
                "licenseDeclared": "Apache-2.0 AND MIT AND CC0-1.0",
                "licenseInfoFromFiles": ["Apache-2.0", "MIT", "CC0-1.0"],
                "copyrightText": "2026 Xiaomiju-x",
                "comment": "Core runtime dependency set is empty. Optional NumPy and the source-only neural reference's PyTorch are not bundled; inspect their own distribution metadata when installing them.",
            }
        ],
        "files": files,
        "relationships": [
            {
                "spdxElementId": "SPDXRef-DOCUMENT",
                "relationshipType": "DESCRIBES",
                "relatedSpdxElement": "SPDXRef-Package",
            },
            *[
                {
                    "spdxElementId": "SPDXRef-Package",
                    "relationshipType": "CONTAINS",
                    "relatedSpdxElement": f["SPDXID"],
                }
                for f in files
            ],
        ],
    }


def generated() -> dict[Path, str]:
    values = {ROOT / "schemas" / name: body for name, body in schemas().items()}
    values[ROOT / "reports/source-sbom.spdx.json"] = source_sbom()
    return {
        path: json.dumps(body, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
        for path, body in values.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale = []
    for path, text in generated().items():
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != text:
                stale.append(path.relative_to(ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
    if stale:
        print("Generated metadata is stale: " + ", ".join(stale))
        return 1
    print("Schemas and source SPDX inventory: " + ("PASS" if args.check else "written"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
