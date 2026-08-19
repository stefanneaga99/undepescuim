#!/usr/bin/env python3
"""Safe deterministic fixture validator and explicitly opt-in live checker."""
from __future__ import annotations
import argparse, json, socket, sys, time
from urllib.parse import urljoin, urlsplit
from datetime import datetime, timezone
from pathlib import Path
import requests
from link_validation_lib import USER_AGENT, LinkTarget, build_report, enumerate_targets, policy_error, repair_record, result_for, sanitize_url
ROOT=Path(__file__).resolve().parent.parent
RETRYABLE={408,425,429,500,502,503,504}
_HTML_TYPES = ("text/html", "application/xhtml+xml")
_PARKED_MARKERS = ("domain is for sale", "buy this domain", "domain parking", "parked free", "coming soon")
_HOST_LAST_REQUEST = {}

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
def resolve(host, port):
    return {x[4][0] for x in socket.getaddrinfo(host,port,type=socket.SOCK_STREAM)}
def pace(host):
    wait = 1.0 - (time.monotonic() - _HOST_LAST_REQUEST.get(host, 0.0))
    if wait > 0: time.sleep(wait)
    _HOST_LAST_REQUEST[host] = time.monotonic()
def content_reason(response, field):
    content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
    if field.endswith("permitUrl") or field in {"nationalPermitUrl", "guideUrl"}:
        allowed = _HTML_TYPES + ("application/pdf",)
    else:
        allowed = _HTML_TYPES
    if content_type and content_type not in allowed:
        return "wrong_content_type"
    sample = getattr(response, "_validator_sample", b"")
    if any(marker in sample.decode("utf-8", "ignore").lower() for marker in _PARKED_MARKERS):
        return "parked_domain"
    return None
def live_one(target, exceptions):
    checked=[]; started=now(); err=policy_error(target.original_url,exceptions,resolver=resolve)
    if err: return result_for(target,now=started,outcome={"failureReason":err},http_exceptions=exceptions)
    url=target.original_url; chain=[]; retry_after=None; last=None
    for attempt in range(3):
        checked.append(now())
        if attempt:
            delay = retry_after if retry_after else (1,3)[attempt-1]
            time.sleep(min(delay,60))
        try:
            pace(urlsplit(url).hostname or "")
            r=requests.head(url,allow_redirects=False,timeout=(3,7),headers={"User-Agent":USER_AGENT,"Accept":"text/html,application/xhtml+xml;q=0.9,*/*;q=0.1"},verify=True)
            if r.status_code in {405,403,501}:
                r.close(); pace(urlsplit(url).hostname or ""); r=requests.get(url,allow_redirects=False,stream=True,timeout=(3,7),headers={"User-Agent":USER_AGENT,"Accept":"text/html,application/xhtml+xml;q=0.9,*/*;q=0.1"},verify=True)
                r._validator_sample = next(r.iter_content(65536), b"")
            if 300<=r.status_code<400 and r.headers.get("Location"):
                if len(chain) >= 5:
                    r.close()
                    return result_for(target,now=started,outcome={"status":"blocked","failureReason":"redirect_limit","httpStatus":r.status_code,"redirect":{"count":len(chain),"chain":chain,"crossHost":False,"downgradedToHttp":False}},http_exceptions=exceptions)
                nxt=urljoin(url,r.headers["Location"])
                hoperr=policy_error(nxt,exceptions,resolver=resolve)
                if hoperr: return result_for(target,now=started,outcome={"status":"blocked","failureReason":"unsafe_redirect","httpStatus":r.status_code,"redirect":{"count":len(chain)+1,"chain":chain+[ {"url":sanitize_url(url),"status":r.status_code}],"crossHost":False,"downgradedToHttp":False}},http_exceptions=exceptions)
                if any(x["url"]==sanitize_url(nxt) for x in chain): return result_for(target,now=started,outcome={"status":"blocked","failureReason":"redirect_loop","httpStatus":r.status_code},http_exceptions=exceptions)
                chain.append({"url":sanitize_url(url),"status":r.status_code}); url=nxt; continue
            if r.status_code in RETRYABLE:
                retry_after=min(int(r.headers.get("Retry-After","0")) if r.headers.get("Retry-After","").isdigit() else 0,60); last=r
                if attempt<2: continue
                status="transient_error"; reason="http_%s"%r.status_code
            elif 400<=r.status_code<500: status="client_error"; reason="http_%s"%r.status_code
            elif 200<=r.status_code<300:
                reason = content_reason(r, target.field)
                status = "client_error" if reason else ("redirected" if chain else "ok")
            else: status="server_error"; reason="http_%s"%r.status_code
            r.close()
            return result_for(target,now=started,outcome={"status":status,"httpStatus":r.status_code,"finalUrl":url,"failureReason":reason,"redirect":{"count":len(chain),"chain":chain,"crossHost":False,"downgradedToHttp":False},"retry":{"attempts":attempt+1,"attemptedAt":checked,"retryAfterSeconds":retry_after,"exhausted":attempt==2}},http_exceptions=exceptions)
        except (requests.RequestException, OSError, TimeoutError):
            last=None
            if attempt==2: return result_for(target,now=started,outcome={"status":"transient_error","failureReason":"network_error","redirect":{"count":len(chain),"chain":chain,"crossHost":False,"downgradedToHttp":False},"retry":{"attempts":3,"attemptedAt":checked,"retryAfterSeconds":None,"exhausted":True}},http_exceptions=exceptions)
    return result_for(target,now=started,outcome={"status":"transient_error","failureReason":"network_error"},http_exceptions=exceptions)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--mode",choices=("fixtures","live"),default="fixtures"); ap.add_argument("--report",default="data/processed/link_validation_report.json"); ap.add_argument("--repairs",default="data/processed/link_validation_repairs.jsonl"); ap.add_argument("--limit",type=int,default=0); ap.add_argument("--only-source"); ap.add_argument("--fail-on",choices=("critical","none"),default="critical"); args=ap.parse_args()
    stamp=now(); exc_path=ROOT/"data/processed/link_validation_http_exceptions.json"; exceptions=json.loads(exc_path.read_text()) if exc_path.exists() else []
    if args.mode=="fixtures":
        fixture=json.loads((ROOT/"tests/fixtures/link_validation/targets.json").read_text()); pairs=[(LinkTarget(i.get("associationSlug"),i["field"],i["sourcePath"],i["sourceKind"],i["url"]),i.get("outcome")) for i in fixture]
        if not fixture: pairs=[(t,None) for t in enumerate_targets(ROOT)]
        records=[result_for(t,now=stamp,outcome=o,http_exceptions=exceptions) for t,o in pairs]
    else:
        targets=enumerate_targets(ROOT); pairs=[(t,None) for t in targets]; records=[live_one(t,exceptions) for t,_ in pairs]
    if args.only_source: records=[r for r in records if r["sourceKind"]==args.only_source]
    if args.limit: records=records[:args.limit]
    records.sort(key=lambda r:(r["sourceKind"],r["associationSlug"] is None,r["associationSlug"] or "",r["field"],r["sourcePath"]))
    report=build_report(records,mode=args.mode,generated_at=stamp); rp=Path(args.report); rp.parent.mkdir(parents=True,exist_ok=True); tmp=rp.with_suffix(rp.suffix+".tmp"); tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n"); tmp.replace(rp)
    repairs=[repair_record(r) for r in records]; repairs=[r for r in repairs if r]; pp=Path(args.repairs); pp.parent.mkdir(parents=True,exist_ok=True); pp.write_text("".join(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n" for r in repairs))
    print(json.dumps(report["summary"],sort_keys=True)); return 1 if args.fail_on=="critical" and any(r["status"] in {"blocked","client_error","server_error"} for r in records) else 0
if __name__=="__main__": sys.exit(main())
