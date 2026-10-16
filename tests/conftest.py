"""Test-suite hooks.

On GitHub Actions, surface pytest failures as workflow annotations
(``::error file=...::``) so they show up on the PR checks page and via the
check-runs API without opening the raw logs. No effect outside Actions.
"""

import os

_MAX_ANNOTATIONS = 10  # GitHub shows at most 10 error annotations per step
_MAX_LINES = 14


def _escape(message: str) -> str:
    """Escape a workflow-command message (data part)."""
    return message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    reports = list(terminalreporter.stats.get("failed", [])) + list(terminalreporter.stats.get("error", []))
    for report in reports[:_MAX_ANNOTATIONS]:
        path, lineno, _ = report.location
        tail = "\n".join(report.longreprtext.strip().splitlines()[-_MAX_LINES:])
        title = f"pytest {report.nodeid}".replace(",", " ").replace(":", " ")
        terminalreporter.write_line(
            f"::error file={path},line={(lineno or 0) + 1},title={title}::{_escape(tail)}"
        )
