import hashlib
import json
from pathlib import Path

import pytest

from rivernet import fetch_input as fi
from rivernet import __main__ as cli

ROOT = Path(__file__).resolve().parents[2]
REAL_MANIFEST = ROOT / "data" / "rivernet" / "input_manifest.json"


def _manifest(sha=None, url=None):
    return {
        "schema": 1,
        "pbf": {"url": url, "sha256": sha},
        "extract": {"url": None, "sha256": None},
        "filters": ["nwr/waterway"],
    }


def test_committed_manifest_is_valid():
    data = fi.load_manifest(REAL_MANIFEST)
    assert data["pbf"]["url"].startswith("https://")
    assert "nwr/waterway" in data["filters"]


def test_validate_rejects_bad_manifests():
    bad = _manifest()
    bad["schema"] = 2
    with pytest.raises(fi.ManifestError):
        fi.validate_manifest(bad)
    with pytest.raises(fi.ManifestError):
        fi.validate_manifest(_manifest(sha="ABC"))
    with pytest.raises(fi.ManifestError):
        fi.validate_manifest(_manifest(url="http://insecure.example/x.pbf"))
    no_extract = _manifest()
    del no_extract["extract"]
    with pytest.raises(fi.ManifestError):
        fi.validate_manifest(no_extract)
    no_filters = _manifest()
    no_filters["filters"] = []
    with pytest.raises(fi.ManifestError):
        fi.validate_manifest(no_filters)


def test_is_pinned():
    assert not fi.is_pinned(_manifest(), "pbf")
    assert fi.is_pinned(_manifest(sha="a" * 64, url="https://x/y"), "pbf")


def test_fetch_verifies_hash(tmp_path):
    src = tmp_path / "src.bin"
    src.write_bytes(b"hello osm")
    good = hashlib.sha256(b"hello osm").hexdigest()
    dest = tmp_path / "out" / "d.bin"
    assert fi.fetch(src.as_uri(), dest, good) == good
    assert dest.read_bytes() == b"hello osm"


def test_fetch_mismatch_removes_partial_file(tmp_path):
    src = tmp_path / "src.bin"
    src.write_bytes(b"hello osm")
    dest = tmp_path / "d.bin"
    with pytest.raises(fi.ManifestError):
        fi.fetch(src.as_uri(), dest, "0" * 64)
    assert not dest.exists()
    assert not (tmp_path / "d.bin.part").exists()


def test_fetch_refuses_unpinned_unless_allowed(tmp_path):
    src = tmp_path / "src.bin"
    src.write_bytes(b"x")
    with pytest.raises(fi.ManifestError):
        fi.fetch(src.as_uri(), tmp_path / "d.bin", None)
    assert fi.fetch(src.as_uri(), tmp_path / "d.bin", None, allow_unpinned=True)


def test_cli_fetch_input_end_to_end(tmp_path):
    src = tmp_path / "src.bin"
    src.write_bytes(b"data")
    sha = hashlib.sha256(b"data").hexdigest()
    manifest = tmp_path / "m.json"
    manifest.write_text(json.dumps(_manifest(sha=sha, url=src.as_uri())), encoding="utf-8")
    out = tmp_path / "o.bin"
    assert cli.main(["fetch-input", "--manifest", str(manifest), "--out", str(out)]) == 0
    assert out.read_bytes() == b"data"


def test_cli_fetch_input_fails_cleanly(tmp_path):
    manifest = tmp_path / "m.json"
    manifest.write_text(json.dumps(_manifest()), encoding="utf-8")
    out = tmp_path / "o.bin"
    # url not set
    assert cli.main(["fetch-input", "--manifest", str(manifest), "--out", str(out)]) == 1
    # unpinned
    src = tmp_path / "s.bin"
    src.write_bytes(b"x")
    manifest.write_text(json.dumps(_manifest(url=src.as_uri())), encoding="utf-8")
    assert cli.main(["fetch-input", "--manifest", str(manifest), "--out", str(out)]) == 1
    assert cli.main(["fetch-input", "--manifest", str(manifest), "--out", str(out), "--allow-unpinned"]) == 0
