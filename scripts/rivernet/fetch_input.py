"""Pinned input handling for the river network build (T1.2).

``data/rivernet/input_manifest.json`` pins the OSM input by SHA-256. This module
validates the manifest and downloads/verifies a file against it. Standard
library only; ``file://`` URLs work (used by the tests, no network).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import urllib.request
from pathlib import Path
from typing import Any, Sequence

DEFAULT_MANIFEST = Path("data/rivernet/input_manifest.json")
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
SECTIONS = ("pbf", "extract")


class ManifestError(ValueError):
    pass


def sha256_file(path: str | Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def load_manifest(path: str | Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_manifest(data)
    return data


def validate_manifest(data: dict[str, Any]) -> None:
    """Raise ``ManifestError`` unless the manifest is structurally valid.

    A section may be unpinned (``sha256`` null) — that is reported by
    ``is_pinned`` — but a present hash must be 64 lowercase hex characters.
    """
    if data.get("schema") != 1:
        raise ManifestError(f"unsupported manifest schema {data.get('schema')!r}")
    for name in SECTIONS:
        sec = data.get(name)
        if not isinstance(sec, dict):
            raise ManifestError(f"missing section {name!r}")
        sha = sec.get("sha256")
        if sha is not None and not (isinstance(sha, str) and _SHA_RE.match(sha)):
            raise ManifestError(f"{name}.sha256 must be 64 lowercase hex chars or null")
        url = sec.get("url")
        if url is not None and not (isinstance(url, str) and re.match(r"^(https://|file://)", url)):
            raise ManifestError(f"{name}.url must be https:// (or file://) or null")
    filters = data.get("filters")
    if not isinstance(filters, list) or not filters or not all(isinstance(f, str) and f for f in filters):
        raise ManifestError("filters must be a non-empty list of strings")


def is_pinned(data: dict[str, Any], section: str) -> bool:
    sec = data[section]
    return bool(sec.get("url")) and bool(sec.get("sha256"))


def fetch(url: str, dest: str | Path, expected_sha256: str | None, *, allow_unpinned: bool = False) -> str:
    """Download ``url`` to ``dest`` and verify it. Returns the SHA-256.

    Refuses an unpinned download unless ``allow_unpinned``. On a mismatch the
    partial file is removed and ``ManifestError`` is raised.
    """
    if not expected_sha256 and not allow_unpinned:
        raise ManifestError("input is not pinned (sha256 is null); pin it or pass --allow-unpinned")
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    with urllib.request.urlopen(url) as resp, open(tmp, "wb") as out:  # noqa: S310 (https/file only)
        shutil.copyfileobj(resp, out)
    actual = sha256_file(tmp)
    if expected_sha256 and actual != expected_sha256:
        tmp.unlink(missing_ok=True)
        raise ManifestError(f"sha256 mismatch for {url}: expected {expected_sha256}, got {actual}")
    tmp.replace(dest)
    return actual


def cli(argv: Sequence[str]) -> int:
    p = argparse.ArgumentParser(prog="rivernet fetch-input", description="Download a pinned OSM input.")
    p.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    p.add_argument("--section", choices=SECTIONS, default="pbf")
    p.add_argument("--out", required=True)
    p.add_argument("--allow-unpinned", action="store_true")
    ns = p.parse_args(list(argv))
    try:
        manifest = load_manifest(ns.manifest)
        sec = manifest[ns.section]
        if not sec.get("url"):
            raise ManifestError(f"{ns.section}.url is not set in {ns.manifest}")
        sha = fetch(sec["url"], ns.out, sec.get("sha256"), allow_unpinned=ns.allow_unpinned)
    except ManifestError as exc:
        print(f"fetch-input: {exc}", file=sys.stderr)
        return 1
    print(f"fetch-input: {ns.out} sha256={sha}", file=sys.stderr)
    return 0
