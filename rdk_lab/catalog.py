"""Read the versioned public snapshot without consulting the private laboratory."""

from __future__ import annotations

from importlib.resources import files
from typing import Any

from .io import decode_json, require


def load_catalog() -> dict[str, Any]:
    doc = decode_json(files("rdk_lab").joinpath("data/catalogue.json").read_text(encoding="utf-8"))
    require(isinstance(doc, dict) and doc.get("schema_version") == 1, "invalid catalogue")
    rows = doc.get("entries")
    require(isinstance(rows, list), "catalogue entries missing")
    ids = [row["id"] for row in rows]
    require(len(ids) == len(set(ids)), "duplicate catalogue entry IDs")
    return doc


def select_entries(target: str | None = None, group: str | None = None) -> list[dict[str, Any]]:
    require(target in {None, "host", "x5", "s100", "s600"}, "unsupported target filter")
    require(group in {None, "official", "frontier", "research"}, "unsupported group filter")
    return [
        row
        for row in load_catalog()["entries"]
        if (target is None or target in row["intended_targets"])
        and (group is None or group == row["group"])
    ]
