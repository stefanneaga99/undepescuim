import gzip
import json
import subprocess
import sys
from pathlib import Path


FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures/river_segment_audit_cases.json").read_text(encoding="utf-8")
)
ROOT = Path(__file__).resolve().parents[1]
from audit_river_segments import repair_geometries


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


def test_reviewed_alias_resolves_owner_without_hiding_gap(tmp_path):
    root, index = materialize_case(tmp_path, "tarnava_injected_gap")
    records = []
    with gzip.open(index, "rt", encoding="utf-8") as stream:
        records = [json.loads(line) for line in stream if line.strip()]
    relation = next(record for record in records if record["kind"] == "relation")
    relation["name"] = "Tarnava Mare"
    relation["named_aliases"] = ["Tarnava Mare"]
    with index.open("wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as compressed:
            import io
            stream = io.TextIOWrapper(compressed, encoding="utf-8", newline="\n")
            for record in records:
                stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            stream.flush()
    aliases = root / "data/processed/river_name_aliases.json"
    aliases.write_text(json.dumps({"aliases": [{
        "canonical": "Târnava Fixture", "aliases": ["Tarnava Mare"],
        "justification": "OSM alternate name", "source": "osm:9010",
        "expires_on": "2099-01-01"
    }]}, ensure_ascii=False), encoding="utf-8")
    output_json, output_md = root / "report.json", root / "report.md"
    result = subprocess.run([
        sys.executable, str(ROOT / "scripts/audit_river_segments.py"),
        "--osm-index", str(index), "--root", str(root),
        "--aliases", str(aliases), "--out-json", str(output_json),
        "--out-md", str(output_md), "--gate"
    ], cwd=ROOT, capture_output=True, text=True)
    report = json.loads(output_json.read_text())
    assert result.returncode == 1
    assert report["rivers"][0]["owner_slug"] == "tarnava-fixture"
    assert report["rivers"][0]["registry"]["alias_used"] is True
    assert [finding["code"] for finding in report["rivers"][0]["findings"]] == ["missing_segment"]


def test_exception_allows_gate_but_preserves_raw_finding(tmp_path):
    root, index = materialize_case(tmp_path, "tarnava_injected_gap")
    exceptions = root / "data/processed/river_segment_exceptions.json"
    exceptions.write_text(json.dumps({"exceptions": [{
        "id": "review-tarnava-gap", "code": "missing_segment",
        "river_group": "tarnava-fixture", "gate": "allow",
        "justification": "Reviewed source snapshot gap", "source": "osm:9010",
        "expires_on": "2099-01-01"
    }]}, ensure_ascii=False), encoding="utf-8")
    output_json, output_md = root / "report.json", root / "report.md"
    result = subprocess.run([
        sys.executable, str(ROOT / "scripts/audit_river_segments.py"),
        "--osm-index", str(index), "--root", str(root),
        "--exceptions", str(exceptions), "--out-json", str(output_json),
        "--out-md", str(output_md), "--gate"
    ], cwd=ROOT, capture_output=True, text=True)
    report = json.loads(output_json.read_text())
    finding = report["rivers"][0]["findings"][0]
    assert result.returncode == 0
    assert report["gate"] == {"status": "PASS", "blocking_findings": []}
    assert finding["code"] == "missing_segment"
    assert finding["gate_exception"] == {"id": "review-tarnava-gap", "expires_on": "2099-01-01"}
    assert "**missing_segment**" in output_md.read_text()


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


def test_repair_preserves_contract_fields_and_emits_provenance(tmp_path):
    root, index = materialize_case(tmp_path, "valid")
    waters_path = root / "public/data/waters.json"
    before = json.loads(waters_path.read_text())
    before[0]["geometry"] = {"type": "LineString", "coordinates": [[23.49, 46.4], [23.52, 46.4]]}
    waters_path.write_text(json.dumps(before), encoding="utf-8")
    report = {"rivers": [{"river_group": "aries-fixture", "owner_slug": "raul-aries-fixture", "osm": {"relation_ids": [9001]}, "findings": [{"code": "truncated_head"}]}]}
    diff, provenance = root / "repairs.json", root / "provenance.json"
    artifact = repair_geometries(index, root, report, {"aries fixture"}, diff, provenance)
    after = json.loads(waters_path.read_text())
    assert len(artifact["changes"]) == 1
    assert before[0]["id"] == after[0]["id"]
    assert before[0]["asociatie"] == after[0]["asociatie"]
    assert before[0]["riverGroup"] == after[0]["riverGroup"]
    assert before[0]["geometry"] != after[0]["geometry"]
    assert json.loads((root / "public/data/waters.json.audit-backup.json").read_text()) == before
    assert json.loads(diff.read_text())["changes"][0]["provenance"]["osm_relation_id"] == 9001
    assert json.loads(provenance.read_text())["repairs"][0]["osm_way_ids"] == [9101, 9102]


def test_repair_leaves_unapproved_tarnava_blocked(tmp_path):
    root, index = materialize_case(tmp_path, "tarnava_injected_gap")
    report = {"rivers": [{"river_group": "tarnava-fixture", "owner_slug": "tarnava-fixture", "osm": {"relation_ids": [9010]}, "findings": [{"code": "missing_segment"}]}]}
    artifact = repair_geometries(index, root, report, {"cerna", "ialomita", "sieu", "timis"}, root / "repairs.json", root / "provenance.json")
    assert artifact["changes"] == []
    assert json.loads((root / "public/data/waters.json").read_text())[0]["geometry"]["coordinates"] == [[24.0, 46.2], [24.01, 46.2]]


def test_report_schema_contains_gate_grid_and_is_reproducible(tmp_path):
    _, first_result, first, first_md = run_case(tmp_path / "first", "tarnava_injected_gap")
    _, second_result, second, second_md = run_case(tmp_path / "second", "tarnava_injected_gap")
    assert first_result.returncode == second_result.returncode == 1
    assert first["schema_version"] == 1
    assert first["gate"]["status"] == "BLOCKED"
    assert first["cells"] and first["cells"][0]["finding_codes"]["missing_segment"] == 1
    assert "## Coverage grid" in first_md
    assert "**missing_segment**" in first_md
    assert first == second
    assert first_md == second_md


def test_report_keeps_each_overlay_classification(tmp_path):
    root, index = materialize_case(tmp_path, "valid")
    overlay_dir = root / "public/data"
    (overlay_dir / "uncontracted_rivers.json").write_text(json.dumps([
        {"slug": "unc-river", "name": "Pârâu test", "judet": "Alba", "uncontracted": True}
    ], ensure_ascii=False))
    (overlay_dir / "uncontracted_lakes.json").write_text(json.dumps([
        {"slug": "unc-lake", "name": "Lac test", "judet": "Alba", "uncontracted": True}
    ], ensure_ascii=False))
    output_json, output_md = root / "report.json", root / "report.md"
    subprocess.run([sys.executable, str(ROOT / "scripts/audit_river_segments.py"),
                    "--osm-index", str(index), "--root", str(root),
                    "--out-json", str(output_json), "--out-md", str(output_md)],
                   cwd=ROOT, check=True)
    report = json.loads(output_json.read_text())
    assert {x["slug"] for x in report["overlays"]} == {"unc-river", "unc-lake"}
    assert report["cells"][0]["overlay"] == {"rivers": 1, "lakes": 1}
