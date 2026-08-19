#!/usr/bin/env python3
"""Compatibility entry point for the retired URL audit.

Reachability is no longer run by this command. Use link_validation.py with
--mode live from the reviewed scheduled job; fixture mode is the CI gate.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from link_validation import main

if __name__ == "__main__":
    # Preserve a safe, deterministic default for old developer invocations.
    if "--mode" not in sys.argv:
        sys.argv[1:1] = ["--mode", "fixtures"]
    raise SystemExit(main())
