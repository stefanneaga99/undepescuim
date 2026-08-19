import gzip
import json
import subprocess
import sys
from pathlib import Path


FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures/river_segment_audit_cases.json").read_text(encoding="utf-8")
)
ROOT = Path(__file__).resolve().parents[1]


def materialize_case(tmp_path, case):
    root = tmp_path / case
    (root / "public/data").mkdir(parents=True)
    (root / "data/processed").mkdir(parents=True)
    spec = FIXTURE["cases"][case]
    contract = spec["contract"]
    (root / "public/data/waters.json").write_text(
        json.dumps([contract], ensure_ascii=False), encoding="utf-8"
    )
    (root / "data/processed/anpa_waters.jsonl").write_text(
        json.dumps(
            {
                "id": contract["id"],
                "water_name": contract["water_name"],
                "association": spec["association"]["name"],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    index = root / "osm-index.jsonl.gz"
    records = [spec["relation"], *spec["ways"]]
    with index.open("wb") as raw:
      with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as compressed:
        stream = compressed
        import io
        stream = io.TextIOWrapper(compressed, encoding="utf-8", newline="\n")
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()
    return root, index


def run_case(tmp_path, case):
    root, index = materialize_case(tmp_path, case)
    output_json, output_md = root / "report.json", root / "report.md"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/audit_river_segments.py"),
            "--osm-index",
            str(index),
            "--root",
            str(root),
            "--out-json",
            str(output_json),
            "--out-md",
            str(output_md),
            "--gate",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return FIXTURE["cases"][case], result, json.loads(output_json.read_text()), output_md.read_text()


def test_valid_fixture_passes_and_reports_no_findings(tmp_path):
    spec, result, report, markdown = run_case(tmp_path, "valid")
    assert result.returncode == 0, result.stderr
    assert report["summary"]["PASS_CONTRACTED"] == 1
    assert report["rivers"][0]["findings"] == []
    assert spec["contract"]["asociatie"]["name"] == spec["association"]["name"]
    assert all(text in markdown for text in spec["expected"]["markdown_must_contain"])


def test_tarnava_fixture_gap_blocks_gate_and_remains_explicit(tmp_path):
    spec, result, report, markdown = run_case(tmp_path, "tarnava_injected_gap")
    assert result.returncode == 1
    assert "missing_segment" in result.stderr
    river = report["rivers"][0]
    assert river["river_group"] == "tarnava-fixture"
    assert [finding["code"] for finding in river["findings"]] == spec["expected"]["finding_codes"]
    assert report["summary"]["missing_segment"] == 1
    assert river["owner_slug"] == "tarnava-fixture"
    assert river["registry"]["alias_used"] is False
    assert all(text in markdown for text in spec["expected"]["markdown_must_contain"])
