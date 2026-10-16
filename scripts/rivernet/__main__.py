"""Command-line entry point: ``PYTHONPATH=scripts python -m rivernet <command>``.

Each subcommand is a stub that exits with status 2 until the task that
implements it lands (see docs/plans/river-geometry-v2.md). Later tasks replace
the stub by registering a real handler in ``HANDLERS``.
"""

from __future__ import annotations

import argparse
import sys
from typing import Callable, Sequence

# command -> task that implements it
PLANNED: dict[str, str] = {
    "extract": "T1.1",
    "fetch-input": "T1.2",
    "build": "T2.4",
    "parse": "T3.1",
    "match": "T3.2",
    "resolve": "T3.4",
    "report": "T3.5",
    "review-page": "T3.5",
    "publish": "T4.2",
}

# command -> callable(list_of_remaining_args) -> exit status
HANDLERS: dict[str, Callable[[list[str]], int]] = {}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m rivernet",
        description="OSM river network, linear referencing and sector resolution "
        "(river geometry v2).",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    for name, task in PLANNED.items():
        # add_help=False: a command's own flags (including -h) are passed through
        sub.add_parser(name, help=f"task {task}", add_help=False)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    ns, rest = parser.parse_known_args(argv)
    if ns.command is None:
        parser.print_help()
        return 0
    handler = HANDLERS.get(ns.command)
    if handler is None:
        print(
            f"rivernet {ns.command}: not implemented yet (task {PLANNED[ns.command]})",
            file=sys.stderr,
        )
        return 2
    return handler(list(rest))


if __name__ == "__main__":
    sys.exit(main())
