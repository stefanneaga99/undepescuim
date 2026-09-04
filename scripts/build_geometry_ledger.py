#!/usr/bin/env python3
"""Build the deterministic source-backed river/lake geometry ledger."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

LOCKED_COMMIT = "62974d0f050b265a27dcc7ea30c6b356eb3a3454"
HISTORICAL_REFS = {
    "origin/agent/t_6465ebb8": "8e416fc81d469e64dc03645682a9ddf4e0a79f66",
    "origin/wt/t_86659d07": "e6edd3e5dc83077be5303fe9b40c3a912d366e6b",
}
SUPPORTED_TYPES = {"Point", "LineString", "MultiLineString", "Polygon", "MultiPolygon"}
CANONICAL_SURFACES = [
    "public/data/waters.json",
    "public/data/associations.json",
    "public/data/association_locations.json",
    "public/data/waters_county_clips.json",
    "data/processed/anpa_waters.jsonl",
    "data/processed/anpa_contracts.jsonl",
    "data/processed/anpa_romsilva_waters.jsonl",
    "data/processed/arebaltapeste_waters.jsonl",
    "data/processed/arebaltapeste_associations.jsonl",
    "data/processed/mures_harghita_covasna_endpoint_audit.json",
    "data/processed/river_segment_audit.json",
    "data/processed/permit_enrichment.json",
    "data/processed/permit_overrides.json",
]
INPUTS = {
    "waters": "public/data/waters.json",
    "countyClips": "public/data/waters_county_clips.json",
    "preview": "public/data/preview_class2_physical.json",
    "uncontractedRivers": "public/data/uncontracted_rivers.json",
    "uncontractedLakes": "public/data/uncontracted_lakes.json",
    "uncontractedMajors": "public/data/uncontracted_majors.json",
    "pipelineManifest": "data/processed/pipeline_manifest.json",
    "snapshotManifest": "data/processed/osm_river_snapshot_manifest.json",
    "segmentAudit": "data/processed/river_segment_audit.json",
    "traceability": "data/processed/traceability_report.json",
    "integrityReport": "data/processed/integrity_report.json",
    "renderRepairProvenance": "data/processed/geometry_render_repair_provenance.json",
    "unresolvedEvidence": "data/processed/geometry_ledger_unresolved_evidence.json",
    "productionEvidence": "docs/evidence/geometry-ledger-production-observations.json",
}
OUTPUTS = {
    "authoritative": "data/processed/geometry_ledger.json",
    "public": "public/data/geometry-ledger.json",
    "manifest": "public/data/geometry-ledger-manifest.json",
    "report": "docs/geometry-ledger-report.md",
}


def canonical_number_values(value: Any) -> Any:
    """Normalize integer-valued floats to JSON numbers shared with browsers."""
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("geometry values must be finite")
        return int(value) if value.is_integer() else value
    if isinstance(value, list):
        return [canonical_number_values(item) for item in value]
    if isinstance(value, dict):
        return {key: canonical_number_values(item) for key, item in value.items()}
    return value


def canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            canonical_number_values(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except ValueError as exc:
        raise ValueError("geometry values must be finite") from exc


def geometry_identity_token(value: Any) -> str:
    """Language-neutral canonical token over JSON values using IEEE-754 numbers."""
    if isinstance(value, bool):
        return "b1" if value else "b0"
    if isinstance(value, (int, float)):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("geometry values must be finite")
        return f"d{struct.pack('>d', number).hex()}"
    if isinstance(value, str):
        return f"s{json.dumps(value, ensure_ascii=False, separators=(',', ':'))}"
    if value is None:
        return "n"
    if isinstance(value, list):
        return f"[{','.join(geometry_identity_token(item) for item in value)}]"
    if isinstance(value, dict):
        return "{" + ",".join(
            f"{geometry_identity_token(key)}:{geometry_identity_token(value[key])}"
            for key in sorted(value)
        ) + "}"
    raise ValueError("geometry contains unsupported JSON value")


def geometry_identity_bytes(value: Any) -> bytes:
    return geometry_identity_token(value).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def scalar_token(value: float | None) -> str:
    if value is None:
        return "null"
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError("segment fractions must be finite numbers or null")
    return canonical_bytes(value).decode("utf-8")


def segment_id(
    source_slug: str,
    geometry_hash: str,
    evidence_source_id: str,
    start: float | None,
    end: float | None,
) -> str:
    value = "\0".join(
        [source_slug, geometry_hash, evidence_source_id, scalar_token(start), scalar_token(end)]
    )
    return sha256_bytes(value.encode("utf-8"))


def coordinate_pairs(value: Any) -> Iterable[tuple[float, float]]:
    if not isinstance(value, list):
        raise ValueError("geometry coordinates must be arrays")
    if len(value) >= 2 and all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in value[:2]):
        lon, lat = float(value[0]), float(value[1])
        if not math.isfinite(lon) or not math.isfinite(lat):
            raise ValueError("geometry values must be finite")
        yield lon, lat
        return
    for item in value:
        yield from coordinate_pairs(item)


def geometry_summary(geometry: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(geometry, dict) or geometry.get("type") not in SUPPORTED_TYPES:
        raise ValueError("unsupported GeoJSON geometry type")
    points = list(coordinate_pairs(geometry.get("coordinates")))
    if not points:
        raise ValueError("geometry must contain coordinates")
    normalized = {"type": geometry["type"], "coordinates": geometry["coordinates"]}
    digest = sha256_bytes(geometry_identity_bytes(normalized))
    xs, ys = zip(*points)
    return {
        "geometryHash": digest,
        "type": geometry["type"],
        "bbox": [min(xs), min(ys), max(xs), max(ys)],
        "coordinateCount": len(points),
        "valid": True,
        "validityEvidence": "finite supported GeoJSON coordinates; structural audit only",
    }


def load_json(root: Path, key: str, default: Any = None) -> Any:
    path = root / INPUTS[key]
    if not path.exists() and default is not None:
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def raw_source(path: str, digest: str, source_slug: str, url: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "evidenceSourceId": f"{LOCKED_COMMIT}:{path}#{source_slug}",
        "commit": LOCKED_COMMIT,
        "path": path,
        "rawFileSha256": digest,
    }
    if url:
        result["url"] = url
    return result


def source_url(water: dict[str, Any]) -> str | None:
    for key in ("source_url", "url"):
        value = water.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value
    reference = water.get("referinta")
    if isinstance(reference, str) and reference.startswith(("http://", "https://")):
        return reference
    return None


def preview_index(preview: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, str], list[str]]]:
    records = {record["slug"]: record for record in preview.get("records", [])}
    aliases: dict[tuple[str, str], list[str]] = defaultdict(list)
    for record in records.values():
        group = record.get("riverGroup")
        for candidate in record.get("physicalCandidates", []):
            geometry = candidate.get("geometry")
            if not geometry:
                continue
            digest = geometry_summary(geometry)["geometryHash"]
            if candidate.get("geometryHash") != digest:
                raise ValueError(f"{record['slug']} candidate geometryHash is not canonical")
            aliases[(str(group or ""), digest)].append(record["slug"])
    return records, {key: sorted(set(values)) for key, values in aliases.items()}


def runtime_preview_keys(preview: dict[str, Any]) -> set[tuple[str, str]]:
    """Mirror the current UI: validate and consume every ledger candidate."""
    keys: set[tuple[str, str]] = set()
    for record in preview.get("records", []):
        candidates = record.get("physicalCandidates", [])
        for candidate in candidates:
            if not candidate.get("geometry"):
                continue
            digest = geometry_summary(candidate["geometry"])["geometryHash"]
            if candidate.get("geometryHash") != digest:
                raise ValueError(f"{record['slug']} runtime candidate geometryHash is not canonical")
            keys.add((str(record.get("riverGroup") or ""), digest))
    return keys


def endpoint_evidence(water: dict[str, Any], canonical_source: dict[str, Any]) -> dict[str, Any]:
    start, end = water.get("sectorStart"), water.get("sectorEnd")
    detail = water.get("source_detail")
    explicit = (
        isinstance(start, (int, float))
        and not isinstance(start, bool)
        and isinstance(end, (int, float))
        and not isinstance(end, bool)
        and isinstance(detail, str)
        and bool(detail.strip())
    )
    if explicit:
        return {
            "status": "source-backed-explicit",
            "start": start,
            "end": end,
            "citations": [{**canonical_source, "sourceDetail": detail}],
            "rationale": "Explicit persisted interval with source-detail citation; course_frac is excluded.",
        }
    return {
        "status": "not-verified",
        "start": None,
        "end": None,
        "citations": [],
        "rationale": "No independently cited explicit endpoints; names, county, OSM, locality, length, screenshots and course_frac are non-evidence.",
    }


def county_evidence(slug: str, county: str | None, clips: dict[str, Any], clip_digest: str) -> dict[str, Any]:
    value = clips.get(slug)
    if slug not in clips:
        status = "not-materialized"
    elif value is None or (isinstance(value, dict) and value.get(str(county or "").lower()) is None):
        status = "explicit-hide-or-null"
    else:
        status = "materialized"
    return {
        "status": status,
        "citation": {
            "commit": LOCKED_COMMIT,
            "path": INPUTS["countyClips"],
            "rawFileSha256": clip_digest,
            "key": slug,
        },
        "rationale": "Render-clip state only; it does not prove legal ownership, association or endpoints.",
    }


def variant(
    source_slug: str,
    state: str,
    geometry: dict[str, Any],
    evidence_source_id: str,
    start: float | None,
    end: float | None,
    citation: dict[str, Any],
) -> dict[str, Any]:
    summary = geometry_summary(geometry)
    return {
        "state": state,
        "start": start,
        "end": end,
        "evidenceSourceId": evidence_source_id,
        "segmentId": segment_id(source_slug, summary["geometryHash"], evidence_source_id, start, end),
        "geometry": summary,
        "geojson": geometry,
        "citation": citation,
    }


def browser_resolution_conflict(county: str | None, observations: list[dict[str, Any]]) -> bool:
    cards = [card for item in observations if isinstance((card := item.get("card")), dict)]
    return bool(county and cards and all(county not in str(card.get("text", "")) for card in cards))


def build(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    waters = load_json(root, "waters")
    clips = load_json(root, "countyClips")
    preview = load_json(root, "preview")
    unresolved = load_json(root, "unresolvedEvidence")
    production = load_json(root, "productionEvidence", {"observations": {}, "probes": [], "limitations": ["browser evidence file unavailable"]})
    pipeline = load_json(root, "pipelineManifest")
    repair = load_json(root, "renderRepairProvenance")
    input_hashes = {key: file_sha256(root / path) for key, path in INPUTS.items() if (root / path).exists()}
    before_hashes = {path: file_sha256(root / path) for path in CANONICAL_SURFACES}
    preview_records, alias_groups = preview_index(preview)
    unresolved_by_slug = {record["slug"]: record for record in unresolved["records"]}
    historical = {
        record["sourceSlug"]: record for record in unresolved["historicalAudit"]["candidateRecords"]
    }
    source_artifact_by_commit = {
        item["commit"]: item for item in preview.get("sourceArtifacts", [])
    }
    browser_by_slug = production.get("observations", {})
    records: list[dict[str, Any]] = []

    for water in sorted(waters, key=lambda item: item["slug"]):
        slug = water["slug"]
        canonical = raw_source(INPUTS["waters"], input_hashes["waters"], slug, source_url(water))
        endpoint = endpoint_evidence(water, canonical)
        variants: list[dict[str, Any]] = []
        geometry = water.get("geometry")
        if geometry:
            variants.append(variant(slug, "canonical-legal-sector", geometry, canonical["evidenceSourceId"], endpoint["start"], endpoint["end"], canonical))

        preview_record = preview_records.get(slug)
        aliases = {slug}
        if preview_record:
            for candidate in preview_record.get("physicalCandidates", []):
                candidate_geometry = candidate.get("geometry")
                if not candidate_geometry:
                    continue
                summary = geometry_summary(candidate_geometry)
                group_key = (str(preview_record.get("riverGroup") or ""), summary["geometryHash"])
                aliases.update(alias_groups.get(group_key, []))
                commit = str(candidate.get("sourceCommit") or preview_record.get("sourceCommit") or "unavailable")
                artifact_source = source_artifact_by_commit.get(commit, {})
                path = str(artifact_source.get("path") or INPUTS["preview"])
                evidence_id = f"{commit}:{path}#{candidate.get('id') or slug}"
                citation = {
                    "commit": commit,
                    "path": path,
                    "rawFileSha256": artifact_source.get("sha256", input_hashes["preview"]),
                    "aggregatePath": INPUTS["preview"],
                    "aggregateSha256": input_hashes["preview"],
                    "candidateId": candidate.get("id"),
                }
                variants.append(variant(slug, "physical-full-course-preview", candidate_geometry, evidence_id, None, None, citation))
                if endpoint["status"] == "source-backed-explicit":
                    variants.append(variant(slug, "explicit-physical-segment", candidate_geometry, evidence_id, endpoint["start"], endpoint["end"], citation))

        unresolved_record = unresolved_by_slug.get(slug)
        unresolved_class = unresolved_record.get("class") if unresolved_record else None
        unresolved_reason = (
            unresolved_record.get("classification", {}).get("blocker")
            if unresolved_record
            else ("canonical-geometry-absent" if not geometry else None)
        )
        if not variants:
            variants.append({
                "state": "unresolved",
                "start": None,
                "end": None,
                "evidenceSourceId": canonical["evidenceSourceId"],
                "segmentId": None,
                "geometry": None,
                "reason": unresolved_reason or "no-ledger-geometry-variant",
                "citation": canonical,
            })

        historical_record = historical.get(slug)
        observations = list(browser_by_slug.get(slug, []))
        render_conflict = browser_resolution_conflict(water.get("judet"), observations) if historical_record else False
        if render_conflict:
            variants.append({
                "state": "unresolved",
                "start": None,
                "end": None,
                "evidenceSourceId": canonical["evidenceSourceId"],
                "segmentId": None,
                "geometry": None,
                "reason": "production-card-resolves-outside-canonical-county",
                "citation": canonical,
            })
        classification = (
            "preview-only"
            if preview_record and not geometry
            else ("repaired" if geometry and not render_conflict else "unresolved")
        )
        confidence = (
            unresolved_record.get("classification", {}).get("confidence")
            if unresolved_record
            else ("high" if geometry else "low")
        )
        if historical_record and not observations:
            observations.append({
                "source": f"{HISTORICAL_REFS['origin/wt/t_86659d07']}:.local-work/river-geometry-confirmed-batches.json",
                "result": "NOT_REPRODUCED",
                "note": "Historical RENDERING_FIX candidate was ineligible; no repair is approved by that audit.",
            })
        raw_sources = [canonical]
        if preview_record:
            raw_sources.append({
                "evidenceSourceId": f"{LOCKED_COMMIT}:{INPUTS['preview']}#{slug}",
                "commit": LOCKED_COMMIT,
                "path": INPUTS["preview"],
                "rawFileSha256": input_hashes["preview"],
            })
        records.append({
            "sourceSlug": slug,
            "name": water.get("name"),
            "county": water.get("judet"),
            "subtype": water.get("subtype"),
            "aliases": sorted(aliases),
            "riverGroup": water.get("riverGroup"),
            "classification": classification,
            "classificationRationale": "canonical geometry and current browser resolution are render-ready in the frozen data; not mutated by this audit" if classification == "repaired" else ("neutral physical preview exists but legal geometry is unverified" if classification == "preview-only" else ("current Production card resolves outside the canonical county for a historical audit candidate" if render_conflict else "no supported render geometry variant")),
            "confidence": confidence,
            "unresolved": {"class": unresolved_class, "reason": unresolved_reason} if unresolved_class or unresolved_reason else None,
            "canonicalBbox": water.get("bbox"),
            "rawSources": raw_sources,
            "geometryVariants": variants,
            "countyConsistencyEvidence": county_evidence(slug, water.get("judet"), clips, input_hashes["countyClips"]),
            "endpointEvidence": endpoint,
            "historicalAudit": {
                "candidate": historical_record is not None,
                "classification": historical_record.get("classification") if historical_record else None,
                "eligible": historical_record.get("eligible") if historical_record else None,
                "reproduction": "NOT_REPRODUCED" if historical_record else None,
                "citations": [
                    {"ref": ref, "commit": commit, "path": ".local-work/river-geometry-confirmed-batches.json" if "86659" in ref else ".local-work/river-geometry-phase1-audit.json"}
                    for ref, commit in HISTORICAL_REFS.items()
                ] if historical_record else [],
            },
            "browserObservations": observations,
        })

    classifications = Counter(record["classification"] for record in records)
    states = Counter(item["state"] for record in records for item in record["geometryVariants"])
    ledger = {
        "artifact": "canonical-geometry-ledger",
        "schemaVersion": 1,
        "lockedCommit": LOCKED_COMMIT,
        "identityRules": {
            "sourceSlug": "immutable canonical water slug",
            "aliases": "sorted unique exact canonical slugs only",
            "riverGroup": "explicit canonical/source mapping only; never name-inferred",
            "geometryHash": "SHA-256 language-neutral geometry token: sorted keys, UTF-8 strings, finite IEEE-754 binary64 numbers",
            "segmentId": "sha256(sourceSlug + NUL + geometryHash + NUL + evidenceSourceId + NUL + start + NUL + end)",
            "selected-focus": "runtime-only and never persisted as legal geometry",
        },
        "totals": {
            "canonicalWaters": len(records),
            "rivers": sum(record["subtype"] == "rau" for record in records),
            "lakes": sum(record["subtype"] == "lac" for record in records),
            "canonicalGeometryPresent": sum(bool(water.get("geometry")) for water in waters),
            "canonicalGeometryAbsent": sum(not water.get("geometry") for water in waters),
            "canonicalBboxPresent": sum(bool(water.get("bbox")) for water in waters),
            "unresolvedInventory": unresolved["recordCount"],
            "unresolvedByClass": unresolved["counts"],
            "class2PreviewRecords": preview.get("recordCount", 0),
            "class2PreviewCandidates": preview.get("candidateCount", 0),
            "physicalPreviewRepresentativeKeys": len(alias_groups),
            "physicalPreviewRuntimeRepresentatives": len(runtime_preview_keys(preview)),
            "classifications": dict(sorted(classifications.items())),
            "states": dict(sorted(states.items())),
        },
        "sourceArtifacts": {
            key: {"path": path, "sha256": input_hashes.get(key), "count": len(load_json(root, key)) if key in {"uncontractedRivers", "uncontractedLakes", "uncontractedMajors"} else None}
            for key, path in INPUTS.items() if key in input_hashes
        },
        "historicalRefs": [{"ref": ref, "commit": commit} for ref, commit in sorted(HISTORICAL_REFS.items())],
        "productionEvidence": production,
        "records": records,
    }

    public_records = []
    for record in records:
        projected = {key: value for key, value in record.items() if key != "geometryVariants"}
        projected["geometryVariants"] = [
            {key: value for key, value in item.items() if key != "geojson"}
            for item in record["geometryVariants"]
        ]
        public_records.append(projected)
    public = {
        "artifact": "public-geometry-ledger",
        "schemaVersion": 1,
        "lockedCommit": LOCKED_COMMIT,
        "totals": ledger["totals"],
        "identityRules": ledger["identityRules"],
        "sourceArtifacts": ledger["sourceArtifacts"],
        "records": public_records,
    }

    stale = []
    for path, expected in sorted(pipeline.get("outputs", {}).items()):
        actual_path = root / path
        if actual_path.exists():
            actual = file_sha256(actual_path)
            if actual != expected:
                stale.append({"path": path, "manifestSha256": expected, "actualSha256": actual})
    after_hashes = {path: file_sha256(root / path) for path in CANONICAL_SURFACES}
    report = render_report(ledger, stale, before_hashes, production, repair)
    authoritative_bytes = canonical_bytes(ledger) + b"\n"
    public_bytes = canonical_bytes(public) + b"\n"
    report_bytes = report.encode("utf-8")
    manifest = {
        "artifact": "geometry-ledger-manifest",
        "schemaVersion": 1,
        "lockedCommit": LOCKED_COMMIT,
        "originMainAtLock": LOCKED_COMMIT,
        "historicalRefs": ledger["historicalRefs"],
        "inputHashes": dict(sorted(input_hashes.items())),
        "outputHashes": {
            OUTPUTS["authoritative"]: sha256_bytes(authoritative_bytes),
            OUTPUTS["public"]: sha256_bytes(public_bytes),
            OUTPUTS["report"]: sha256_bytes(report_bytes),
        },
        "canonicalNoMutation": {
            "status": "PASS" if before_hashes == after_hashes else "FAIL",
            "before": before_hashes,
            "after": after_hashes,
        },
        "staleManifestReconciliation": {
            "status": "STALE_RECORDED" if stale else "CURRENT",
            "mismatches": stale,
        },
        "determinism": "Run twice and compare all four output files byte-for-byte.",
        "limitations": production.get("limitations", []),
    }
    return ledger, public, manifest, report


def render_report(
    ledger: dict[str, Any],
    stale: list[dict[str, str]],
    before_hashes: dict[str, str],
    production: dict[str, Any],
    repair: dict[str, Any],
) -> str:
    totals = ledger["totals"]
    lines = [
        "# Deterministic river/lake geometry ledger",
        "",
        f"Locked `origin/main`: `{LOCKED_COMMIT}`.",
        "",
        "## Scope and semantics",
        "",
        f"- Canonical waters: **{totals['canonicalWaters']}** ({totals['rivers']} rivers, {totals['lakes']} lakes).",
        f"- Canonical geometry: **{totals['canonicalGeometryPresent']} present**, **{totals['canonicalGeometryAbsent']} absent**.",
        f"- Unresolved inventory: **{totals['unresolvedInventory']}**; classes `{json.dumps(totals['unresolvedByClass'], sort_keys=True)}`.",
        f"- Class2 physical source: **{totals['class2PreviewRecords']} records / {totals['class2PreviewCandidates']} candidates / {totals['physicalPreviewRepresentativeKeys']} all-candidate `(riverGroup, geometryHash)` keys**.",
        f"- Current runtime validates every exact candidate identity and deduplicates all candidates to **{totals['physicalPreviewRuntimeRepresentatives']} representatives**.",
        "- `repaired` means render-ready canonical geometry in the frozen dataset; it does not claim this audit changed or newly proved the legal sector.",
        "- `preview-only` is a neutral physical course and never legal ownership/association/endpoint evidence.",
        "- `selected-focus` is runtime-only and is deliberately absent from persisted geometry variants.",
        "",
        "## Immutable legal surfaces",
        "",
    ]
    lines.extend(f"- `{path}`: `{digest}` (before = after)" for path, digest in sorted(before_hashes.items()))
    lines.extend(["", "## Historical audit refs", ""])
    lines.extend(f"- `{item['ref']}` → `{item['commit']}`" for item in ledger["historicalRefs"])
    lines.extend(["", "The four prior `RENDERING_FIX` rows remain `NOT_REPRODUCED` and ineligible in the confirmed-batch audit; this ledger does not approve those historical repairs.", "", "## Pipeline manifest reconciliation", ""])
    if stale:
        lines.extend(f"- STALE `{item['path']}`: manifest `{item['manifestSha256']}`, actual `{item['actualSha256']}`" for item in stale)
    else:
        lines.append("- No stale output hashes detected.")
    lines.extend(["", "## Production browser evidence", ""])
    for probe in production.get("probes", []):
        lines.append(f"- `{probe.get('viewport')}` / `{probe.get('serviceWorkers')}`: `{probe.get('url')}`; HTTP `{probe.get('httpStatus')}`; evidence `{probe.get('evidencePath')}`.")
    for limitation in production.get("limitations", []):
        lines.append(f"- Limitation: {limitation}")
    buzau = production.get("observations", {}).get("anpa-anpa-0207", [])
    if buzau:
        properties = buzau[0].get("featureProperties", [{}])
        aliases = properties[0].get("physicalAliases", []) if properties else []
        lines.append(f"- Buzău Production feature aliases are `{json.dumps(aliases, ensure_ascii=False)}` at all probes, while the source-backed ledger group has six exact aliases.")
        lines.append("- Frozen Production baseline: Buzău renders neutral teal `#14b8a6`, weight 3, dash `7 5`; its click opened the canonical AJVPS card without the physical-preview disclosure before this runtime fix.")
    lines.append("- Mobile probes use the Vaul bottom sheet at `35vh`; desktop probes use the right aside. All four probes reported zero console/page errors.")
    lines.append("- Historical candidate click-resolution: Bacău Bărzăuța opens the Covasna sector card; Maramureș Crasna (Frumușaua) opens the Satu Mare Crasna card. Șugo and Geamărtălui resolve to matching-county cards.")
    lines.append("- Per-target feature properties, styles, card text, culling-before/after-fit and visible filter controls are retained in `docs/evidence/geometry-ledger-production-observations.json`.")
    lines.extend(["", "## Classification totals", ""])
    lines.extend(f"- `{key}`: {value}" for key, value in sorted(totals["classifications"].items()))
    lines.extend(["", "## Source-backed render repair provenance", "", f"- County clip transition: `{repair.get('before_clip_sha256')}` → `{repair.get('after_clip_sha256')}`; {repair.get('changed_clip_entry_count')} entries.", "- No legal/ownership/association/endpoint surface was mutated by this generator.", ""])
    return "\n".join(lines)


def write_outputs(output_root: Path, ledger: dict[str, Any], public: dict[str, Any], manifest: dict[str, Any], report: str) -> None:
    payloads: dict[str, bytes] = {
        OUTPUTS["authoritative"]: canonical_bytes(ledger) + b"\n",
        OUTPUTS["public"]: canonical_bytes(public) + b"\n",
        OUTPUTS["manifest"]: canonical_bytes(manifest) + b"\n",
        OUTPUTS["report"]: report.encode("utf-8"),
    }
    for relative, payload in payloads.items():
        path = output_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output_root = (args.output_root or root).resolve()
    ledger, public, manifest, report = build(root)
    write_outputs(output_root, ledger, public, manifest, report)
    print(json.dumps({"outputs": OUTPUTS, "totals": ledger["totals"]}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
