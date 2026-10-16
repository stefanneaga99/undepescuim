"""Human override registries (plan T3.2). Pure validation, standard library only.

``data/sectors/course_overrides.json``::

    {"schema": 1, "overrides": [{"slug", "course_id", "reason", "reviewer", "date"}]}

``data/sectors/endpoint_overrides.json``::

    {"schema": 1, "overrides": [{"slug", "end": "from|to",
        "anchor": {"type": "node|way|area|measure", "id"?, "m"?}, "reason", "reviewer", "date"}]}
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ANCHOR_TYPES = ("node", "way", "area", "measure")


def _nonempty(x: Any) -> bool:
    return isinstance(x, str) and bool(x.strip())


def _common(doc: Any) -> tuple[list[str], list[Any]]:
    if not isinstance(doc, dict):
        return ["document must be an object"], []
    errs = []
    if doc.get("schema") != SCHEMA_VERSION:
        errs.append(f"schema must be {SCHEMA_VERSION}")
    items = doc.get("overrides")
    if not isinstance(items, list):
        errs.append("overrides must be a list")
        items = []
    extra = set(doc) - {"schema", "overrides"}
    if extra:
        errs.append(f"unknown top-level keys: {sorted(extra)}")
    return errs, items


def _entry_common(i: int, o: Any, allowed: set[str]) -> list[str]:
    if not isinstance(o, dict):
        return [f"[{i}] must be an object"]
    errs = []
    for k in ("slug", "reason", "reviewer"):
        if not _nonempty(o.get(k)):
            errs.append(f"[{i}] {k} must be a non-empty string")
    if not (isinstance(o.get("date"), str) and DATE_RE.match(o["date"])):
        errs.append(f"[{i}] date must be YYYY-MM-DD")
    extra = set(o) - allowed
    if extra:
        errs.append(f"[{i}] unknown keys: {sorted(extra)}")
    return errs


def validate_course_overrides(doc: Any) -> list[str]:
    errs, items = _common(doc)
    seen: set[str] = set()
    for i, o in enumerate(items):
        errs += _entry_common(i, o, {"slug", "course_id", "reason", "reviewer", "date"})
        if isinstance(o, dict):
            if not _nonempty(o.get("course_id")):
                errs.append(f"[{i}] course_id must be a non-empty string")
            s = o.get("slug")
            if s in seen:
                errs.append(f"[{i}] duplicate slug {s!r}")
            seen.add(s)
    return errs


def validate_endpoint_overrides(doc: Any) -> list[str]:
    errs, items = _common(doc)
    seen: set[tuple[Any, Any]] = set()
    for i, o in enumerate(items):
        errs += _entry_common(i, o, {"slug", "end", "anchor", "reason", "reviewer", "date"})
        if not isinstance(o, dict):
            continue
        if o.get("end") not in ("from", "to"):
            errs.append(f"[{i}] end must be 'from' or 'to'")
        key = (o.get("slug"), o.get("end"))
        if key in seen:
            errs.append(f"[{i}] duplicate {key!r}")
        seen.add(key)
        a = o.get("anchor")
        if not isinstance(a, dict):
            errs.append(f"[{i}] anchor must be an object")
            continue
        t = a.get("type")
        if t not in ANCHOR_TYPES:
            errs.append(f"[{i}] anchor.type must be one of {ANCHOR_TYPES}")
        if set(a) - {"type", "id", "m"}:
            errs.append(f"[{i}] anchor has unknown keys")
        if t == "measure":
            m = a.get("m")
            if isinstance(m, bool) or not isinstance(m, (int, float)) or m < 0:
                errs.append(f"[{i}] anchor.m must be a number >= 0")
        elif t in ("node", "way", "area"):
            if isinstance(a.get("id"), bool) or not isinstance(a.get("id"), (int, str)):
                errs.append(f"[{i}] anchor.id required for {t}")
    return errs


def load_course_overrides(path: str | Path) -> dict[str, dict[str, Any]]:
    """slug -> override. Missing file means no overrides; invalid file raises."""
    p = Path(path)
    if not p.exists():
        return {}
    doc = json.loads(p.read_text(encoding="utf-8"))
    errs = validate_course_overrides(doc)
    if errs:
        raise ValueError(f"{p}: " + "; ".join(errs))
    return {o["slug"]: o for o in doc["overrides"]}


def load_endpoint_overrides(path: str | Path) -> dict[tuple[str, str], dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return {}
    doc = json.loads(p.read_text(encoding="utf-8"))
    errs = validate_endpoint_overrides(doc)
    if errs:
        raise ValueError(f"{p}: " + "; ".join(errs))
    return {(o["slug"], o["end"]): o for o in doc["overrides"]}
