"""Command-line entry points. No command initiates remote or hardware execution."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

from . import __version__
from .catalog import load_catalog, select_entries
from .contracts import TARGETS, compare_boards, validate_result
from .demo import run_demo
from .io import ValidationError, load_json, verify_manifest, write_new_json


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="rdk-lab",
        description="Offline-first RDK evidence tools; never starts device or network work.",
    )
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="show local tool capabilities; no device probe")
    catalogue = commands.add_parser(
        "catalog", help="list reported observations; target is intended scope, not a PASS filter"
    )
    catalogue.add_argument("--target", choices=["host", *TARGETS])
    catalogue.add_argument("--group", choices=["official", "frontier", "research"])
    catalogue.add_argument("--json", action="store_true")
    demo = commands.add_parser(
        "demo", help="run a six-number CPU arithmetic replay, not a model benchmark"
    )
    demo.add_argument("--output", type=Path, help="optional new receipt file; never overwrites")
    verify = commands.add_parser("verify", help="verify a local fixture allowlist and its hashes")
    verify.add_argument("manifest", type=Path)
    evaluate = commands.add_parser(
        "evaluate", help="check receipt consistency; does not certify its truth"
    )
    evaluate.add_argument("receipt", type=Path)
    comparison = commands.add_parser(
        "compare", help="compare 1..3 same-contract independent board receipts"
    )
    comparison.add_argument("receipts", type=Path, nargs="+")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        code = 0
        if args.command == "doctor":
            result = {
                "version": __version__,
                "python": platform.python_version(),
                "mode": "offline",
                "automatic_downloads": False,
                "hardware_execution": False,
                "vendor_runtimes_bundled": False,
                "targets": TARGETS,
            }
        elif args.command == "catalog":
            entries = select_entries(args.target, args.group)
            if not args.json:
                print(
                    f"Snapshot {load_catalog()['as_of']}; {len(entries)} registry entries, not a deployment count."
                )
                for row in entries:
                    print(f"{row['id']:>3}  {row['name']}\n     {row['observed_status']}")
                return 0
            result = {
                "as_of": load_catalog()["as_of"],
                "entry_count": len(entries),
                "is_deployed_model_count": False,
                "entries": entries,
            }
        elif args.command == "demo":
            result = run_demo()
            if args.output:
                write_new_json(args.output, result["receipt"])
            code = 0 if result["review"]["decision"] == "DEMO_PASS" else 1
        elif args.command == "verify":
            result = verify_manifest(args.manifest)
        elif args.command == "evaluate":
            result = validate_result(load_json(args.receipt))
            code = (
                2
                if result["decision"] == "INCOMPLETE"
                else (1 if result["decision"] in {"FAIL", "DEMO_FAIL"} else 0)
            )
        else:
            result = compare_boards([load_json(p) for p in args.receipts])
            code = {"CROSS_BOARD_CONTRACT_PASS": 0, "NEGATIVE": 1, "INCOMPLETE": 2}[
                result["status"]
            ]
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False))
        return code
    except (ValidationError, OSError) as error:
        print(
            json.dumps({"status": "REJECTED", "error": str(error)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
