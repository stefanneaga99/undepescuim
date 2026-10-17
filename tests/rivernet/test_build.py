import gzip
import json
import re
from pathlib import Path

from rivernet import __main__ as cli
from rivernet import build as bd

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests" / "fixtures" / "rivernet"


def waters_file(tmp_path, names):
    p = tmp_path / "waters.json"
    p.write_text(json.dumps([{"name": n, "subtype": s} for n, s in names]), encoding="utf-8")
    return p


def read_jsonl(path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def test_candidate_keys_come_from_river_waters_only():
    keys = bd.river_candidate_keys(
        [{"name": "Râul Barcău", "subtype": "rau"}, {"name": "Lacul Barcău", "subtype": "lac"},
         {"name": "Valea Iadului", "subtype": "rau"}]
    )
    assert "barcau" in keys and "valea iadului" in keys and "iadului" in keys
    assert "lacul barcau" not in keys


def test_build_writes_qa_all_courses_and_the_candidate_subset(tmp_path):
    waters = waters_file(tmp_path, [("Râul Barcău", "rau"), ("Lacul X", "lac")])
    out = tmp_path / "out"
    summary = bd.build(FIX / "barcau.jsonl.gz", out, waters)
    assert summary["courses_total"] == 1 and summary["courses_candidates"] == 1
    assert summary["commit_courses"] is True
    assert json.loads((out / "qa.json").read_text(encoding="utf-8"))["courses_total"] == 1
    assert [r["name_key"] for r in read_jsonl(out / "courses.jsonl.gz")] == ["barcau"]
    assert len(read_jsonl(out / "courses_all.jsonl.gz")) == 1
    assert json.loads((out / "build_summary.json").read_text(encoding="utf-8"))["courses_total"] == 1


def test_subset_excludes_courses_nobody_asks_for(tmp_path):
    waters = waters_file(tmp_path, [("Râul Jiu", "rau")])
    out = tmp_path / "out"
    summary = bd.build(FIX / "barcau.jsonl.gz", out, waters)
    assert summary["courses_total"] == 1 and summary["courses_candidates"] == 0
    assert read_jsonl(out / "courses.jsonl.gz") == []


def test_oversize_subset_is_not_kept(tmp_path):
    out = tmp_path / "out"
    summary = bd.build(FIX / "barcau.jsonl.gz", out, None, max_commit_mb=0.0001)
    assert summary["commit_courses"] is False
    assert not (out / "courses.jsonl.gz").exists()
    assert (out / "courses_all.jsonl.gz").exists()
    assert summary["candidate_filter"] == "none"


def test_outputs_are_byte_deterministic(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    bd.build(FIX / "bistrita.jsonl.gz", a, None)
    bd.build(FIX / "bistrita.jsonl.gz", b, None)
    for name in ("courses.jsonl.gz", "courses_all.jsonl.gz", "qa.json", "build_summary.json"):
        assert (a / name).read_bytes() == (b / name).read_bytes()


def test_cli_plumbing(tmp_path):
    waters = waters_file(tmp_path, [("Râul Barcău", "rau")])
    out = tmp_path / "o"
    rc = cli.main(["build", "--extract", str(FIX / "barcau.jsonl.gz"), "--out-dir", str(out),
                   "--waters", str(waters)])
    assert rc == 0 and (out / "qa.json").exists()
    rc = cli.main(["build", "--extract", str(FIX / "barcau.jsonl.gz"), "--out-dir", str(tmp_path / "o2"),
                   "--waters", ""])
    assert rc == 0


def test_workflow_contract():
    wf = (ROOT / ".github" / "workflows" / "rivernet-build.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in wf
    assert not re.search(r"^\s*(push|pull_request|schedule):", wf, re.M)
    assert "python -m rivernet fetch-input" in wf and "python -m rivernet build" in wf
    assert "gh pr create" in wf
    # only data directories are ever staged
    adds = re.findall(r"git add ([^\n]+)", wf)
    assert adds == ["data/rivernet data/sectors"]


def test_big_intermediates_are_gitignored():
    assert "/data/rivernet/courses_all.jsonl.gz" in (ROOT / ".gitignore").read_text(encoding="utf-8")


def test_is_candidate_uses_aliases_and_article_variants():
    from rivernet.build import is_candidate

    assert is_candidate({"name_key": "olt", "aliases": []}, {"olt"})
    assert is_candidate({"name_key": "gurghiul", "aliases": []}, {"gurghiu"})
    assert is_candidate({"name_key": "maros", "aliases": ["Mureș"]}, {"mures"})
    assert not is_candidate({"name_key": "olt", "aliases": []}, {"jiu"})


def test_course_index_covers_all_and_includes_alias_keys(tmp_path):
    from rivernet.build import course_index, write_course_index

    recs = [{"course_id": "rel:1", "name_key": "olt", "aliases": ["Aluta"]},
            {"course_id": "name:x:n2", "name_key": "x", "aliases": []}]
    assert course_index(recs) == {"rel:1": ["olt", "aluta"], "name:x:n2": ["x"]}
    write_course_index(tmp_path / "i.json", recs)
    assert json.loads((tmp_path / "i.json").read_text(encoding="utf-8"))["rel:1"] == ["olt", "aluta"]


def test_candidate_filter_accepts_stem_matches():
    river_candidate_keys, is_candidate = bd.river_candidate_keys, bd.is_candidate
    keys = river_candidate_keys([{"subtype": "rau", "name": "Valea Pojorâtei"}, {"subtype": "lac", "name": "Lacul Z"}])
    assert "stem:pojorat" in keys and not any("lacul" in k or k == "stem:z" for k in keys)
    assert is_candidate({"name_key": "pojorata", "name": "Pojorâta", "aliases": []}, keys)
    assert is_candidate({"name_key": "x", "name": "X", "aliases": ["Pojorâta"]}, keys)
    assert not is_candidate({"name_key": "putna", "name": "Putna", "aliases": []}, keys)
