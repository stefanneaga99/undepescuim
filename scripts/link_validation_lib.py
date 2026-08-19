"""Pure URL policy, enumeration, classification and report helpers."""
from __future__ import annotations
import hashlib, ipaddress, json, re, socket
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SCHEMA_VERSION = 1
POLICY_VERSION = 1
USER_AGENT = "UndePescuim-LinkValidator/1.0 (+https://undepescuim.ro/link-validation)"
SECRET_QUERY = re.compile(r"^(token|key|secret|password|auth|signature|session|code|email|phone)$", re.I)
ALLOWED_FIELDS = {"association.siteUrl","association.permitUrl","water.asociatie.siteUrl","water.asociatie.permitUrl","associationLocation.contactUrl","associationLocation.sourceUrl","nationalPermitUrl","guideUrl","guideSourceUrl","provenance.website","provenance.permit_url","provenance.raw_file_url"}
@dataclass(frozen=True)
class LinkTarget:
    association_slug: str | None; field: str; source_path: str; source_kind: str; original_url: str

def sanitize_url(value: str | None) -> str | None:
    if not value: return None
    value = value.strip()
    try:
        p = urlsplit(value)
        if not p.scheme or not p.netloc: return value.split("#",1)[0]
        query = [(k, "REDACTED" if SECRET_QUERY.match(k) else v) for k,v in parse_qsl(p.query, keep_blank_values=True)]
        return urlunsplit((p.scheme.lower(), p.netloc.rsplit("@",1)[-1], p.path, urlencode(query), ""))
    except ValueError: return value.split("#",1)[0]

def _active_exception(item: dict) -> bool:
    if not item.get("approved", True):
        return False
    expires = item.get("expiresAt")
    if not expires:
        return False
    try:
        return date.fromisoformat(str(expires)[:10]) >= date.today()
    except ValueError:
        return False


def _exception_matches(raw: str, exceptions: list[dict]) -> dict | None:
    safe = sanitize_url(raw)
    for item in exceptions:
        if item.get("url") == safe and _active_exception(item):
            return item
    return None

def policy_error(value: str, http_exceptions: list[dict] | None = None, resolver=None) -> str | None:
    exceptions = http_exceptions or []; raw = value.strip()
    if not raw or any(ord(c) < 32 for c in raw): return "malformed_url"
    try: p = urlsplit(raw); host = (p.hostname or "").lower().rstrip("."); port = p.port
    except (ValueError, UnicodeError): return "malformed_url"
    if p.scheme.lower() not in {"http","https"} or not p.netloc: return "forbidden_scheme" if p.scheme else "malformed_url"
    if p.username or p.password: return "credentials_in_url"
    if host == "localhost" or host.endswith(".localhost"): return "private_target"
    try:
        if not ipaddress.ip_address(host).is_global: return "private_target"
    except ValueError: pass
    if p.scheme.lower() == "http" and not _exception_matches(raw, exceptions): return "http_not_approved"
    if p.scheme.lower() == "https" and port not in (None,443) and not any(e.get("url") == sanitize_url(raw) and e.get("allowedPorts") and _active_exception(e) for e in exceptions): return "port_not_allowed"
    if resolver:
        try: answers = resolver(host, port or (443 if p.scheme.lower()=="https" else 80))
        except Exception: return "dns_failure"
        if any(not ipaddress.ip_address(str(a)).is_global for a in answers): return "private_target"
    return None

def enumerate_targets(root: Path) -> list[LinkTarget]:
    out=[]
    def add(slug, field, path, kind, url):
        if url: out.append(LinkTarget(slug,field,path,kind,url))
    assocs=json.loads((root/"public/data/associations.json").read_text())
    for i,r in enumerate(assocs):
        add(r.get("slug"),"association.siteUrl",f"public/data/associations.json[{i}].siteUrl","runtime-association",r.get("siteUrl")); add(r.get("slug"),"association.permitUrl",f"public/data/associations.json[{i}].permitUrl","runtime-association",r.get("permitUrl"))
    waters=json.loads((root/"public/data/waters.json").read_text())
    for i,r in enumerate(waters):
        a=r.get("asociatie") or {}; add(a.get("slug"),"water.asociatie.siteUrl",f"public/data/waters.json[{i}].asociatie.siteUrl","runtime-water",a.get("siteUrl")); add(a.get("slug"),"water.asociatie.permitUrl",f"public/data/waters.json[{i}].asociatie.permitUrl","runtime-water",a.get("permitUrl"))
    loc=root/"data/processed/association_locations.json"
    if loc.exists():
        for i,r in enumerate(json.loads(loc.read_text()).get("locations",[])):
            for j,c in enumerate(r.get("contacts",[])):
                if c.get("kind")=="url": add(r.get("associationSlug"),"associationLocation.contactUrl",f"data/processed/association_locations.json.locations[{i}].contacts[{j}].value","curated-location",c.get("value"))
            for j,s in enumerate(r.get("sources",[])): add(r.get("associationSlug"),"associationLocation.sourceUrl",f"data/processed/association_locations.json.locations[{i}].sources[{j}].url","curated-location",s.get("url"))
    # Explicit constants and provenance adapters (never crawl arbitrary text).
    patterns=[
        ("nationalPermitUrl","src/lib/permit.ts","national-permit",r"NATIONAL_PERMIT_URL\s*=\s*['\"]([^'\"]+)"),
        ("guideUrl","src/content/permis-2026.ts","permit-guide",r"PERMIS_PORTAL_URL\s*=\s*['\"]([^'\"]+)"),
        ("guideUrl","src/content/permis-2026.en.ts","permit-guide-en",r"PERMIS_PORTAL_URL['\"]?\s*:\s*['\"]([^'\"]+)") ,
    ]
    for field,fn,kind,pat in patterns:
        text=(root/fn).read_text() if (root/fn).exists() else ""
        for m in re.finditer(pat,text): add(None,field,f"{fn}:{m.start()}",kind,m.group(1))
    # PERMIS_SOURCES is a rendered, URL-bearing contract in both language files.
    for fn,kind in (("src/content/permis-2026.ts","permit-guide-source"),("src/content/permis-2026.en.ts","permit-guide-source-en")):
        text=(root/fn).read_text() if (root/fn).exists() else ""
        for m in re.finditer(r"url:\s*['\"]([^'\"]+)",text):
            add(None,"guideSourceUrl",f"{fn}:{m.start()}",kind,m.group(1))
    provenance=[
        ("arebaltapeste_associations.jsonl",("website","permit_url")),
        ("locuri_associations.jsonl",("website",)),
        ("sources.jsonl",("raw_file_url",)),
    ]
    for fn,keys in provenance:
        p=root/"data/processed"/fn
        if p.exists():
            for i,line in enumerate(p.read_text().splitlines()):
                try: r=json.loads(line)
                except json.JSONDecodeError: continue
                for key in keys:
                    field={"website":"provenance.website","permit_url":"provenance.permit_url","raw_file_url":"provenance.raw_file_url"}[key]
                    add(r.get("slug"),field,f"data/processed/{fn}[{i}].{key}","provenance",r.get(key))
    return sorted(out,key=lambda t:(t.source_kind,t.association_slug is None,t.association_slug or "",t.field,t.source_path))

def result_for(target: LinkTarget, *, now: str, outcome=None, http_exceptions=None):
    err=policy_error(target.original_url,http_exceptions); o=outcome or {}; status="blocked" if err else o.get("status","ok"); reason=err or o.get("failureReason"); red=o.get("redirect",{"count":0,"chain":[],"crossHost":False,"downgradedToHttp":False})
    return {"associationSlug":target.association_slug,"field":target.field,"sourcePath":target.source_path,"sourceKind":target.source_kind,"originalUrl":sanitize_url(target.original_url),"checkedAt":now,"status":status,"httpStatus":o.get("httpStatus"),"finalUrl":sanitize_url(o.get("finalUrl",target.original_url)) if status in {"ok","redirected"} else None,"failureReason":reason,"confidence":"high" if status=="ok" and not red.get("count") else ("medium" if status=="redirected" else "low"),"redirect":red,"retry":o.get("retry",{"attempts":1,"attemptedAt":[now],"retryAfterSeconds":None,"exhausted":False})}

def repair_record(record):
    if record["status"] in {"ok","unsupported"}: return None
    raw="|".join(str(record.get(k) or "") for k in ("sourceKind","associationSlug","field","sourcePath","originalUrl"))
    return {"schemaVersion":1,"repairKey":hashlib.sha256(raw.encode()).hexdigest(),"associationSlug":record["associationSlug"],"field":record["field"],"sourcePath":record["sourcePath"],"originalUrl":record["originalUrl"],"observedStatus":record["status"],"evidence":{"checkedAt":record["checkedAt"],"failureReason":record["failureReason"],"finalUrl":record["finalUrl"],"redirect":record["redirect"]},"action":"review_and_manually_repair","state":"open"}

def build_report(records, *, mode, generated_at):
    counts={s:sum(r["status"]==s for r in records) for s in sorted({r["status"] for r in records})}
    return {"schemaVersion":1,"generatedAt":generated_at,"mode":mode,"policyVersion":1,"summary":{"total":len(records),"ok":counts.get("ok",0),"failed":len(records)-counts.get("ok",0),"byStatus":counts},"records":records}
