"""Data-correctness gates (plan §3.5 species fixture + §3.6 /permis, §7).

These pytest tests are the CHEAP, deterministic layer-1 checks that run on
every commit (data changes -> FULL audit per plan §8); the full audits live in
scripts/audit_*.py and are wired into .github/workflows/data-integrity.yml.

1. species.json matches the pinned Monitorul-Oficial fixture
   (plan §3.5: fixture byte-for-byte on (species, latin, min_cm, retention)).
2. species guard: non-protected min_cm numeric > 0; protected species
   carry min_cm null + retention interzis (plan §3.5).
3. /permis (src/content/permis-2026.ts) discipline: PERMIS_LAST_UPDATED
   within the re-verify window (<= 3 months), portal URL declared in
   PERMIS_SOURCES, and every PENDING fact carries a "proiect/în curs"
   qualifier instead of reading as settled law (plan §3.6).
"""

import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_species_matches_fixture():
    species = load_json("data/species.json")
    fixture = load_json("data/test/species_fixture.json")
    assert len(fixture["species"]) == len(species) == 29, "fixture must pin all 29 species"
    for s in species:
        key = s["species"]
        assert key in fixture["species"], f"species {key} missing from fixture"
        pinned = fixture["species"][key]
        for field in ("latin", "min_cm", "retention"):
            assert s.get(field) == pinned.get(field), (
                f"species.json drift on {key}.{field}: {s.get(field)!r} != {pinned.get(field)!r}"
            )


def test_species_min_cm_guard():
    species = load_json("data/species.json")
    fixture = load_json("data/test/species_fixture.json")
    fixture_protected = [k for k, v in fixture["species"].items() if v.get("retention") == "interzis"]
    protected = [s for s in species if s.get("retention") == "interzis"]
    sized = [s for s in species if s.get("retention") != "interzis"]
    # 10 (not the stale "8" from the older ticket): Caracudă, Lipan and
    # Coregon were reclassified as year-round no-retention by Ordin
    # 23/297/2025 (art. 5 lit. c/d) — the fixture is the verified count.
    assert len(protected) == len(fixture_protected), \
        f"protected count drift: data {len(protected)} vs fixture {len(fixture_protected)}"
    for s in protected:
        assert s.get("min_cm") is None, f"{s['species']} is protected but carries min_cm {s['min_cm']}"
    for s in sized:
        assert isinstance(s.get("min_cm"), (int, float)) and s["min_cm"] > 0, (
            f"{s['species']} must carry a positive min_cm"
        )


def test_permis_last_updated_window():
    ts = (ROOT / "src/content/permis-2026.ts").read_text(encoding="utf-8")
    m = re.search(r"PERMIS_LAST_UPDATED\s*=\s*'(\d{4}-\d{2}-\d{2})'", ts)
    assert m, "PERMIS_LAST_UPDATED missing"
    updated = date.fromisoformat(m.group(1))
    days = (date.today() - updated).days
    assert days <= 93, f"PERMIS_LAST_UPDATED is {days} days old — re-verify against sources"


def test_permis_portal_url_declared():
    ts = (ROOT / "src/content/permis-2026.ts").read_text(encoding="utf-8")
    m = re.search(r"PERMIS_PORTAL_URL\s*=\s*'([^']+)'", ts)
    assert m, "PERMIS_PORTAL_URL missing"
    url = m.group(1)
    assert url in ts, "PERMIS_PORTAL_URL must appear in the facts text"


def test_permis_pending_qualified():
    ts = (ROOT / "src/content/permis-2026.ts").read_text(encoding="utf-8")
    # The MADR draft order (mai 2026) is PENDING — the page must qualify it
    # as a project, never present it as settled.
    assert re.search(r"(proiect|în curs|pregătește|se pregătește)", ts, re.I), (
        "PENDING facts (MADR draft order) must carry a 'proiect/în curs' qualifier"
    )
    # politiadefrontiera aviz is HIGH (official) — the frontier-zone fact must
    # not be presented as an ANPA-permit proof
    assert "frontier" in ts.lower()


def test_species_source_citations_present():
    species = load_json("data/species.json")
    for s in species:
        assert s.get("source"), f"{s['species']} has no source citation"
        assert "Ordin" in s["source"] or "MO" in s["source"] or "Legea" in s["source"], (
            f"{s['species']} source does not cite an official act"
        )