#!/usr/bin/env python3
"""rebuild_data FULL_STEPS entry: `rivernet publish --mode write` (plan T4.2),
then `rivernet evidence` for public/data/sector-evidence.json (plan T4.3).

Switches every eligible river water in public/data/waters.json to its pre-cut
sector geometry (D7-D9) from the committed data/sectors/sectors.jsonl and
data/rivernet/courses.jsonl.gz. Runs from the repo (or scratch-copy) root.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from rivernet.evidence import cli as evidence_cli  # noqa: E402
from rivernet.publish import cli  # noqa: E402


def main() -> int:
    rc = cli([
        "--mode", "write",
        "--waters", str(ROOT / "public/data/waters.json"),
        "--sectors", str(ROOT / "data/sectors/sectors.jsonl"),
        "--courses", str(ROOT / "data/rivernet/courses.jsonl.gz"),
        "--out-dir", str(ROOT / "data/sectors"),
    ])
    if rc:
        return rc
    return evidence_cli([
        "--waters", str(ROOT / "public/data/waters.json"),
        "--sectors", str(ROOT / "data/sectors/sectors.jsonl"),
        "--manifest", str(ROOT / "data/rivernet/input_manifest.json"),
        "--out", str(ROOT / "public/data/sector-evidence.json"),
    ])


if __name__ == "__main__":
    sys.exit(main())
