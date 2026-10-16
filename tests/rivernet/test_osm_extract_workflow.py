"""Static contract checks for the osm-extract workflow (no YAML dependency)."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WF = (ROOT / ".github" / "workflows" / "osm-extract.yml").read_text(encoding="utf-8")
MANIFEST = json.loads((ROOT / "data" / "rivernet" / "input_manifest.json").read_text(encoding="utf-8"))


def test_workflow_is_manual_only():
    assert "workflow_dispatch:" in WF
    assert not re.search(r"^\s*(push|pull_request|schedule):", WF, re.M)


def test_workflow_never_commits_to_the_repository():
    assert not re.search(r"git (add|commit|push)", WF)
    assert re.search(r"^permissions:\n  contents: read", WF, re.M)


def test_workflow_uses_the_pinned_manifest_and_the_cli():
    assert "data/rivernet/input_manifest.json" in WF
    assert "python -m rivernet fetch-input" in WF
    assert "python -m rivernet extract" in WF
    assert "osmium tags-filter" in WF and "osmium export" in WF


def test_every_manifest_filter_is_an_osmium_expression():
    for expr in MANIFEST["filters"]:
        assert re.match(r"^[nwr]+/[a-z_:]+(=[^\s]+)?$", expr), expr


def test_referenced_objects_are_not_stripped():
    # -R / --omit-referenced would drop the nodes the ways need for coordinates
    assert "-R" not in re.findall(r"osmium tags-filter[^\n]*", WF)[0].split()
