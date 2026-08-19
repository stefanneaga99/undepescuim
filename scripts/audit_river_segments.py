#!/usr/bin/env python3
"""Offline contractual river segment audit; read-only by default."""
from __future__ import annotations
import argparse, gzip, hashlib, json, sys, unicodedata
from collections import Counter
from datetime import date
from pathlib import Path
from river_segment_audit_lib import coverage_fraction, uncovered_runs, terminal_findings, stable_report, duplicate_way_ids, sector_findings, line_length
ROOT=Path(__file__).resolve().parent.parent

def norm(s):
 s=unicodedata.normalize('NFD',s or '').encode('ascii','ignore').decode().lower()
 for x in ('raul','parau','paraul','valea','river','stream'): s=s.replace(x,' ')
 return ' '.join(s.replace('-',' ').split())
def load_jsonl(path):
 op=gzip.open if str(path).endswith('.gz') else open
 with op(path,'rt',encoding='utf-8') as f:
  return [json.loads(x) for x in f if x.strip()]
def geometry_points(w):
 g=w.get('geometry') or {}
 if g.get('type')=='LineString': return [tuple(x) for x in g.get('coordinates',[])]
 if g.get('type')=='MultiLineString': return [tuple(x) for p in g.get('coordinates',[]) for x in p]
 return []
def published_waters(root):
 p=root/'public/data/waters.json'
 if not p.exists(): return []
 return json.loads(p.read_text(encoding='utf8'))

def load_registry(path, key):
 """Load and validate an auditable registry without changing its entries."""
 p=Path(path)
 if not p.exists(): return []
 doc=json.loads(p.read_text(encoding='utf8'))
 entries=doc.get(key, [])
 if not isinstance(entries, list): raise ValueError(f'{p}: {key} must be a list')
 for i, entry in enumerate(entries):
  if not isinstance(entry, dict) or any(not entry.get(k) for k in ('justification','source','expires_on')):
   raise ValueError(f'{p}: {key}[{i}] requires justification, source and expires_on')
  try: date.fromisoformat(str(entry['expires_on']))
  except ValueError as exc: raise ValueError(f'{p}: invalid expires_on at {i}') from exc
 return entries

def registry_aliases(entries):
 aliases={}
 for entry in entries:
  canonical=norm(entry.get('canonical') or entry.get('name') or '')
  values=entry.get('aliases', [])
  if isinstance(values, str): values=[values]
  if canonical: aliases.setdefault(canonical, set()).update(norm(v) for v in values if norm(v))
 return aliases

def alias_match(name, aliases):
 n=norm(name)
 return any(n == alias or n == canonical for canonical, values in aliases.items() for alias in values)

def exception_for(finding, river_group, entries):
 """Exceptions can control only the gate; original findings remain visible."""
 for entry in entries:
  codes=entry.get('codes', entry.get('code', [])); codes=[codes] if isinstance(codes, str) else codes
  groups=entry.get('river_groups', entry.get('river_group', [])); groups=[groups] if isinstance(groups, str) else groups
  if entry.get('gate') in ('allow','suppress_gate') and finding.get('code') in codes and (not groups or river_group in groups):
   if date.fromisoformat(str(entry['expires_on'])) >= date.today(): return entry
 return None
def sources(root):
 rows=[]
 for p in ('data/processed/anpa_waters.jsonl','data/processed/anpa_romsilva_waters.jsonl','data/processed/arebaltapeste_waters.jsonl'):
  q=root/p
  if q.exists():
   rows += [json.loads(x) for x in q.read_text(encoding='utf8').splitlines() if x.strip()]
 return rows
def audit(index, root, alias_path=None, exception_path=None):
 entries=load_jsonl(index); ways={e['osm_id']:e for e in entries if e.get('kind')=='way'}
 waters=published_waters(root); src=sources(root)
 aliases=registry_aliases(load_registry(alias_path or root/'data/processed/river_name_aliases.json','aliases'))
 exceptions=load_registry(exception_path or root/'data/processed/river_segment_exceptions.json','exceptions')
 src_names={norm(r.get('water_name') or r.get('name')) for r in src}
 out=[]; hard=[]
 for rel in [e for e in entries if e.get('kind')=='relation']:
  ids=rel.get('all_way_ids',[]); member=[ways[i] for i in ids if i in ways]
  name=rel.get('name') or (rel.get('named_aliases') or [''])[0]
  names=[name]+list(rel.get('named_aliases') or [])
  candidates=[w for w in waters if any(norm(w.get('name'))==norm(n) for n in names)]
  alias_used=any(alias_match(n, aliases) for n in names)
  if not candidates and not any(norm(n) in src_names or alias_match(n, aliases) for n in names): continue
  owner=candidates[0] if candidates else None; pub=geometry_points(owner) if owner else []
  osm=[tuple(p) for w in member for p in w.get('coordinates',[])]
  findings=[]
  repeated=duplicate_way_ids(ids)
  if repeated: findings.append({'code':'duplicate','way_ids':repeated})
  if len(member)!=len(ids): findings.append({'code':'osm_source_incomplete','missing_way_ids':sorted(set(ids)-set(ways))})
  if not owner: findings.append({'code':'MISSING_CONTRACTED','relation_name':name,'aliases_considered':sorted(set(norm(n) for n in names))})
  elif not pub: findings.append({'code':'missing_segment','reason':'published_geometry_missing','length_m':0})
  runs=uncovered_runs(osm,pub) if pub and osm else []
  for run in runs: findings.append({'code':'missing_segment',**run})
  findings += [{'code':x} for x in terminal_findings(osm,pub)]
  findings += sector_findings(candidates)
  group=(owner.get('riverGroup') or norm(name)) if owner else norm(name)
  for finding in findings:
   ex=exception_for(finding, group, exceptions)
   if ex: finding['gate_exception']={'id':ex.get('id'),'expires_on':ex['expires_on']}
   else: hard.append(finding.get('code','unknown'))
  status='PASS_CONTRACTED' if not findings and owner else ('MISSING_CONTRACTED' if not owner else 'UNRESOLVED_NO_OSM_MATCH')
  out.append({'river_group':group,'owner_slug':owner.get('slug') if owner else None,'source_rows':[r.get('id') for r in src if any(norm(r.get('water_name') or r.get('name'))==norm(n) for n in names)],'osm':{'osm_id':rel['osm_id'],'relation_ids':[rel['osm_id']],'way_ids':ids,'match_status':'confirmed' if owner else 'unresolved'},'topology':{'components':1 if len(member)==len(ids) else 2,'internal_gaps':runs},'coverage':{'osm_to_published':coverage_fraction(osm,pub) if pub else 0.0,'published_to_osm':coverage_fraction(pub,osm) if osm else 0.0},'segments':[{'segment_id':f"{rel['osm_id']}:main",'status':status,'fraction':[0,1],'length_m':round(line_length(osm),3),'evidence':list(osm[::max(1,len(osm)//5)])[:5]}], 'findings':findings,'registry':{'alias_used':alias_used}})
 counts=Counter(r['segments'][0]['status'] for r in out)
 for river in out:
  for finding in river['findings']:
   counts[finding.get('code','unknown')] += 1
 return stable_report({'schema_version':1,'snapshot_sha256':hashlib.sha256(Path(index).read_bytes()).hexdigest(),'thresholds':{'coverage_tol_m':125,'min_report_segment_m':250},'summary':dict(sorted(counts.items())),'rivers':out,'cells':[]}),hard

def markdown(report):
 lines=['# River segment audit','',f"Schema: `{report['schema_version']}`",'', '## Summary','']
 for k,v in report['summary'].items(): lines.append(f'- **{k}**: {v}')
 lines += ['', '## Findings','']
 for r in report['rivers']:
  if r['findings']: lines.append(f"- `{r['river_group']}`: "+', '.join(f['code'] for f in r['findings']))
 return '\n'.join(lines)+'\n'
def main():
 p=argparse.ArgumentParser(); p.add_argument('--osm-index',required=True); p.add_argument('--out-json',required=True); p.add_argument('--out-md',required=True); p.add_argument('--baseline'); p.add_argument('--aliases'); p.add_argument('--exceptions'); p.add_argument('--gate',action='store_true'); a=p.parse_args(); report,hard=audit(Path(a.osm_index),ROOT,a.aliases,a.exceptions)
 Path(a.out_json).write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8'); Path(a.out_md).write_text(markdown(report),encoding='utf8')
 if a.baseline and Path(a.baseline).exists():
  base=json.loads(Path(a.baseline).read_text()); b=base.get('summary',{})
  for k in ('MISSING_CONTRACTED','missing_segment','truncated_head','truncated_mouth','sector_mismatch'):
   if report['summary'].get(k,0)>b.get(k,0): hard.append('baseline_regression:'+k)
 if a.gate and hard:
  print('river segment gate: BLOCKED — '+', '.join(sorted(set(hard))),file=sys.stderr); return 1
 print('river segment gate: PASS' if a.gate else f"audited {len(report['rivers'])} river relations"); return 0
if __name__=='__main__': raise SystemExit(main())
