#!/usr/bin/env python3
"""Validate the provenance-backed association locations artifact."""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, NoReturn

ROOT = Path(__file__).resolve().parent.parent
ARTIFACT = ROOT / "data/processed/association_locations.json"
ASSOCIATIONS = ROOT / "public/data/associations.json"
TYPES = {"headquarters", "registered_office", "branch", "office", "club_contact_point", "permit_pickup_point", "partner_location"}
STATUSES = {"verified", "ambiguous", "stale", "unverified"}
FRESHNESS = {"current", "needs_confirmation", "historical"}
CONFIDENCE = {"high", "medium", "low"}
SOURCE_TYPES = {"association_first_party", "official_registry", "official_regulator", "dated_association_notice", "named_partner_page", "secondary_corroboration"}
PHONE_RE = re.compile(r"^\+?[\d\s()./-]{6,}$")


def fail(message: str) -> NoReturn:
    print(f"FAIL: association locations — {message}")
    raise SystemExit(1)


def iso_date(value: Any, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        fail(f"{field} must be ISO date: {value!r}")


def validate(path: Path = ARTIFACT) -> dict:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
        assocs = json.loads(ASSOCIATIONS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(str(exc))
    if doc.get("schemaVersion") != 1 or not isinstance(doc.get("locations"), list):
        fail("schemaVersion 1 and locations array are required")
    known_ids = {a.get("id") for a in assocs}
    known_slugs = {a.get("slug") for a in assocs}
    ids: set[str] = set()
    for i, row in enumerate(doc["locations"]):
        prefix = f"locations[{i}]"
        required = ("id", "associationId", "associationSlug", "type", "address", "locality", "county", "country", "sources", "status", "confidence", "freshness", "checkedAt", "public", "review")
        missing = [key for key in required if not row.get(key)]
        if missing: fail(f"{prefix} missing {', '.join(missing)}")
        if row["id"] in ids: fail(f"duplicate id {row['id']}")
        ids.add(row["id"])
        if row["associationId"] not in known_ids: fail(f"{prefix} unknown associationId")
        if row["associationSlug"] not in known_slugs: fail(f"{prefix} unknown associationSlug")
        if row["type"] not in TYPES or row["status"] not in STATUSES or row["freshness"] not in FRESHNESS or row["confidence"] not in CONFIDENCE:
            fail(f"{prefix} has an invalid enum")
        if row["country"] != "RO" or not isinstance(row["public"], bool): fail(f"{prefix} country/public invalid")
        iso_date(row["checkedAt"], f"{prefix}.checkedAt")
        review = row["review"]
        if review.get("status") != "approved" or not row["public"]: fail(f"{prefix} is not approved for public projection")
        if review.get("approvedAt"): iso_date(review["approvedAt"], f"{prefix}.review.approvedAt")
        for source in row["sources"]:
            if not isinstance(source, dict) or not re.match(r"^https?://", source.get("url", "")) or source.get("sourceType") not in SOURCE_TYPES:
                fail(f"{prefix} has invalid source provenance")
            iso_date(source.get("retrievedAt"), f"{prefix}.source.retrievedAt")
            if source.get("publishedAt"): iso_date(source["publishedAt"], f"{prefix}.source.publishedAt")
        for contact in row.get("contacts", []):
            if contact.get("kind") == "phone" and not PHONE_RE.match(contact.get("value", "")): fail(f"{prefix} invalid phone")
        if row["type"] == "permit_pickup_point" and not any(word in row.get("label", "").lower() for word in ("permit", "permis")):
            fail(f"{prefix} permit pickup is not explicitly labeled")
    return doc


if __name__ == "__main__":
    result = validate()
    print(f"PASS: association locations — schema v{result['schemaVersion']}, {len(result['locations'])} records")
