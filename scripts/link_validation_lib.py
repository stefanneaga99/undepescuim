"""Pure, offline URL policy and report helpers for link validation."""
from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SCHEMA_VERSION = 1
POLICY_VERSION = 1
SECRET_QUERY = re.compile(r"^(token|key|secret|password|auth|signature|session|code|email|phone)$", re.I)
ALLOWED_FIELDS = {
    "association.siteUrl", "association.permitUrl", "water.asociatie.siteUrl",
    "water.asociatie.permitUrl", "associationLocation.contactUrl",
    "associationLocation.sourceUrl", "nationalPermitUrl", "guideUrl",
    "guideSourceUrl", "provenance.website", "provenance.permit_url", "provenance.raw_file_url",
}

@dataclass(frozen=True)
class LinkTarget:
    association_slug: str | None
    field: str
    source_path: str
    source_kind: str
    original_url: str


def sanitize_url(value: str | None) -> str | None:
    if not value:
        return None
    try:
        p = urlsplit(value.strip())
        if not p.scheme or not p.netloc:
            return value.strip().split("#", 1)[0]
        query = [(k, "REDACTED" if SECRET_QUERY.match(k) else v) for k, v in parse_qsl(p.query, keep_blank_values=True)]
        return urlunsplit((p.scheme.lower(), p.netloc.rsplit("@", 1)[-1], p.path, urlencode(query), ""))
    except ValueError:
        return value.strip().split("#", 1)[0]


def policy_error(value: str, http_exceptions: list[dict] | None = None) -> str | None:
    raw = value.strip()
    if not raw or any(ord(c) < 32 for c in raw): return "malformed_url"
    try: p = urlsplit(raw)
    except ValueError: return "malformed_url"
    if p.scheme.lower() not in {"http", "https"} or not p.netloc: return "forbidden_scheme" if p.scheme else "malformed_url"
    if p.username or p.password: return "credentials_in_url"
    host = (p.hostname or "").lower().rstrip(".")
    if host == "localhost" or host.endswith(".localhost"): return "private_target"
    try:
        if ipaddress.ip_address(host).is_global is False: return "private_target"
    except ValueError:
        pass
    port = p.port
    if p.scheme.lower() == "https" and port not in (None, 443):
        if not any(e.get("url") == sanitize_url(raw) and e.get("allowedPorts") for e in (http_exceptions or [])): return "port_not_allowed"
    if p.scheme.lower() == "http":
        if not any(e.get("url") == sanitize_url(raw) and e.get("approved", True) for e in (http_exceptions or [])): return "http_not_approved"
    return None


def enumerate_targets(root: Path) -> list[LinkTarget]:
    targets: list[LinkTarget] = []
    assocs = json.loads((root / "public/data/associations.json").read_text(encoding="utf-8"))
    for i, row in enumerate(assocs):
        for key, field in (("siteUrl", "association.siteUrl"), ("permitUrl", "association.permitUrl")):
            if row.get(key): targets.append(LinkTarget(row.get("slug"), field, f"public/data/associations.json[{i}].{key}", "runtime-association", row[key]))
    waters = json.loads((root / "public/data/waters.json").read_text(encoding="utf-8"))
    for i, row in enumerate(waters):
        assoc = row.get("asociatie") or {}
        for key, field in (("siteUrl", "water.asociatie.siteUrl"), ("permitUrl", "water.asociatie.permitUrl")):
            if assoc.get(key): targets.append(LinkTarget(assoc.get("slug"), field, f"public/data/waters.json[{i}].asociatie.{key}", "runtime-water", assoc[key]))
    loc = root / "data/processed/association_locations.json"
    if loc.exists():
        for i, row in enumerate(json.loads(loc.read_text(encoding="utf-8")).get("locations", [])):
            slug = row.get("associationSlug")
            for j, contact in enumerate(row.get("contacts", [])):
                if contact.get("kind") == "url" and contact.get("value"): targets.append(LinkTarget(slug, "associationLocation.contactUrl", f"data/processed/association_locations.json.locations[{i}].contacts[{j}].value", "curated-location", contact["value"]))
            for j, source in enumerate(row.get("sources", [])):
                if source.get("url"): targets.append(LinkTarget(slug, "associationLocation.sourceUrl", f"data/processed/association_locations.json.locations[{i}].sources[{j}].url", "curated-location", source["url"]))
    return sorted(targets, key=lambda t: (t.source_kind, t.association_slug is None, t.association_slug or "", t.field, t.source_path))


def result_for(target: LinkTarget, *, now: str, outcome: dict | None = None, http_exceptions: list[dict] | None = None) -> dict:
    err = policy_error(target.original_url, http_exceptions)
    outcome = outcome or {}
    status = outcome.get("status", "ok") if not err else "blocked"
    reason = err or outcome.get("failureReason")
    final = sanitize_url(outcome.get("finalUrl", target.original_url)) if status in {"ok", "redirected"} else None
    redirect = outcome.get("redirect", {"count": 0, "chain": [], "crossHost": False, "downgradedToHttp": False})
    return {"associationSlug": target.association_slug, "field": target.field, "sourcePath": target.source_path, "sourceKind": target.source_kind, "originalUrl": sanitize_url(target.original_url), "checkedAt": now, "status": status, "httpStatus": outcome.get("httpStatus"), "finalUrl": final, "failureReason": reason, "confidence": "high" if status == "ok" and not redirect.get("count") else ("medium" if status == "redirected" else "low"), "redirect": redirect, "retry": outcome.get("retry", {"attempts": 1, "attemptedAt": [now], "retryAfterSeconds": None, "exhausted": False})}


def repair_record(record: dict) -> dict | None:
    if record["status"] in {"ok", "unsupported"}: return None
    key = "|".join(str(record.get(k) or "") for k in ("sourceKind", "associationSlug", "field", "sourcePath", "originalUrl"))
    return {"schemaVersion": 1, "repairKey": hashlib.sha256(key.encode()).hexdigest(), "associationSlug": record["associationSlug"], "field": record["field"], "sourcePath": record["sourcePath"], "originalUrl": record["originalUrl"], "observedStatus": record["status"], "evidence": {"checkedAt": record["checkedAt"], "failureReason": record["failureReason"], "finalUrl": record["finalUrl"], "redirect": record["redirect"]}, "action": "review_and_manually_repair", "state": "open"}


def build_report(records: list[dict], *, mode: str, generated_at: str) -> dict:
    counts = {s: sum(r["status"] == s for r in records) for s in sorted({r["status"] for r in records})}
    return {"schemaVersion": SCHEMA_VERSION, "generatedAt": generated_at, "mode": mode, "policyVersion": POLICY_VERSION, "summary": {"total": len(records), "ok": counts.get("ok", 0), "failed": len(records) - counts.get("ok", 0), "byStatus": counts}, "records": records}
