#!/usr/bin/env python3
"""Offline contractual river segment audit; read-only by default."""
from __future__ import annotations
import argparse, copy, gzip, hashlib, json, sys, unicodedata
from collections import Counter, defaultdict
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
  try:
   expiry = date.fromisoformat(str(entry['expires_on']))
  except ValueError as exc: raise ValueError(f'{p}: invalid expires_on at {i}') from exc
  if expiry < date.today():
   raise ValueError(f'{p}: {key}[{i}] expired on {expiry.isoformat()}')
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

def alias_equivalent(left, right, aliases):
 """Return whether names are equal or members of the same reviewed alias set."""
 l, r = norm(left), norm(right)
 if l == r:
  return True
 return any({l, r} <= ({canonical, *values}) for canonical, values in aliases.items())

def exception_for(finding, river_group, entries, as_of=date(2099, 1, 1)):
 """Exceptions can control only the gate; original findings remain visible."""
 for entry in entries:
  codes=entry.get('codes', entry.get('code', [])); codes=[codes] if isinstance(codes, str) else codes
  groups=entry.get('river_groups', entry.get('river_group', [])); groups=[groups] if isinstance(groups, str) else groups
  if entry.get('gate') in ('allow','suppress_gate') and finding.get('code') in codes and (not groups or river_group in groups):
   if date.fromisoformat(str(entry['expires_on'])) >= as_of: return entry
 return None
def sources(root):
 rows=[]
 for p in ('data/processed/anpa_waters.jsonl','data/processed/anpa_romsilva_waters.jsonl','data/processed/arebaltapeste_waters.jsonl'):
  q=root/p
  if q.exists():
   rows += [json.loads(x) for x in q.read_text(encoding='utf8').splitlines() if x.strip()]
 return rows
def _county(water):
 return ' '.join(str(water.get('judet') or water.get('county') or 'Necunoscut').split()) or 'Necunoscut'

def _overlay_entries(root):
 entries=[]
 for kind, filename in (('river', 'public/data/uncontracted_rivers.json'), ('lake', 'public/data/uncontracted_lakes.json')):
  path=root/filename
  if path.exists():
   values=json.loads(path.read_text(encoding='utf8'))
   if isinstance(values, list): entries.extend({'kind':kind, 'entry':v} for v in values)
 return entries

def coverage_grid(waters, rivers, overlays=()):
 """Return a stable county coverage grid without collapsing findings."""
 by_group={r.get('river_group'): r for r in rivers}
 grid=defaultdict(lambda: {'contracted': 0, 'with_geometry': 0, 'missing_geometry': 0,
                           'finding_count': 0, 'finding_codes': Counter(),
                           'overlay_rivers': 0, 'overlay_lakes': 0})
 for water in waters:
  county=_county(water); row=grid[county]; row['contracted'] += 1
  if water.get('geometry'): row['with_geometry'] += 1
  else: row['missing_geometry'] += 1
  report=by_group.get(water.get('riverGroup'))
  for finding in (report or {}).get('findings', []):
   row['finding_count'] += 1; row['finding_codes'][finding.get('code','unknown')] += 1
 for item in overlays:
  county=_county(item['entry']); row=grid[county]
  row['overlay_rivers' if item['kind']=='river' else 'overlay_lakes'] += 1
 result=[]
 for county in sorted(grid):
  row=grid[county]
  result.append({'county': county, 'contracted': row['contracted'],
   'with_geometry': row['with_geometry'], 'missing_geometry': row['missing_geometry'],
   'finding_count': row['finding_count'], 'finding_codes': dict(sorted(row['finding_codes'].items())),
   'overlay': {'rivers': row['overlay_rivers'], 'lakes': row['overlay_lakes']},
   'coverage_status': 'blocked' if row['finding_count'] else ('covered' if row['missing_geometry']==0 else 'partial')})
 return result

def overlay_classification(overlays):
 """Expose every overlay entry, rather than aggregating away problematic rows."""
 result=[]
 for item in overlays:
  entry=item['entry']; result.append({'kind':item['kind'], 'slug':entry.get('slug'),
   'name':entry.get('name'), 'county':_county(entry),
   'classification': 'uncontracted' if entry.get('uncontracted', True) else 'contracted'})
 return sorted(result, key=lambda x:(x['kind'], str(x['county']), str(x['slug'] or ''), str(x['name'] or '')))

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
  candidates=[w for w in waters if any(alias_equivalent(w.get('name'), n, aliases) for n in names)]
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
 overlays=_overlay_entries(root)
 report=stable_report({'schema_version':1,'snapshot_sha256':hashlib.sha256(Path(index).read_bytes()).hexdigest(),
  'thresholds':{'coverage_tol_m':125,'min_report_segment_m':250}, 'summary':dict(sorted(counts.items())),
  'rivers':out, 'cells':coverage_grid(waters, out, overlays), 'overlays':overlay_classification(overlays)})
 return report,hard

def apply_baseline(report, baseline_path):
 if not baseline_path or not Path(baseline_path).exists(): return []
 baseline=json.loads(Path(baseline_path).read_text(encoding='utf8'))
 if not isinstance(baseline, dict) or not isinstance(baseline.get('summary'), dict):
  raise ValueError(f'{baseline_path}: baseline requires a summary object')
 if baseline.get('schema_version', 1) != report.get('schema_version', 1):
  raise ValueError(f'{baseline_path}: unsupported schema_version')
 keys=('MISSING_CONTRACTED','missing_segment','truncated_head','truncated_mouth','sector_mismatch','duplicate')
 deltas={k: report['summary'].get(k,0)-baseline.get('summary',{}).get(k,0) for k in keys}
 report['baseline']={'snapshot_sha256':baseline.get('snapshot_sha256'), 'summary_deltas':deltas}
 return ['baseline_regression:'+k for k,v in deltas.items() if v > 0]

def set_gate(report, hard):
 blockers=sorted(set(hard))
 report['gate']={'status':'BLOCKED' if blockers else 'PASS', 'blocking_findings':blockers}

def _repairable_geometry(index, river, scope):
 """Return deterministic OSM geometry or None; ambiguity is never guessed."""
 group = norm(river.get('river_group'))
 owner = river.get('owner_slug')
 names = {group}
 osm = river.get('osm') or {}
 entries = load_jsonl(index)
 relations = [e for e in entries if e.get('kind') == 'relation' and e.get('osm_id') in osm.get('relation_ids', [])]
 if len(relations) != 1 or group not in scope:
  return None
 rel = relations[0]
 ways = {e.get('osm_id'): e for e in entries if e.get('kind') == 'way'}
 ids = rel.get('all_way_ids') or []
 if not ids or len(ids) != len(set(ids)) or any(i not in ways for i in ids):
  return None
 coords = [list(p) for i in ids for p in (ways[i].get('coordinates') or [])]
 if len(coords) < 2 or any(len(p) < 2 for p in coords):
  return None
 # Repairs are restricted to geometry-only findings. Contract/sector and
 # ownership findings remain blocking and therefore cannot be auto-repaired.
 codes = {f.get('code') for f in river.get('findings', [])}
 if codes - {'missing_segment', 'truncated_head', 'truncated_mouth'}:
  return None
 return {'type': 'LineString', 'coordinates': coords}, {'osm_relation_id': rel.get('osm_id'), 'osm_way_ids': ids, 'method': 'ordered_complete_relation_ways'}

def repair_geometries(index, root, report, scope, diff_path, provenance_path):
 """Apply only unambiguous OSM-backed geometry repairs, preserving all other fields."""
 waters_path = root / 'public/data/waters.json'
 original = waters_path.read_bytes()
 waters = json.loads(original.decode('utf-8'))
 by_slug = {w.get('slug'): w for w in waters}
 owner_counts = Counter(r.get('owner_slug') for r in report.get('rivers', []) if r.get('owner_slug'))
 changes, skipped = [], []
 for river in report.get('rivers', []):
  if owner_counts.get(river.get('owner_slug'), 0) != 1:
   if norm(river.get('river_group')) in scope:
    skipped.append({'river_group': river.get('river_group'), 'reason': 'multiple_relations_for_owner'})
   continue
  result = _repairable_geometry(index, river, scope)
  if not result:
   if norm(river.get('river_group')) in scope:
    skipped.append({'river_group': river.get('river_group'), 'reason': 'ambiguous_or_incomplete_evidence'})
   continue
  geometry, provenance = result
  water = by_slug.get(river.get('owner_slug'))
  if not water:
   skipped.append({'river_group': river.get('river_group'), 'reason': 'owner_not_found'})
   continue
  before = copy.deepcopy(water.get('geometry'))
  if before == geometry:
   continue
  water['geometry'] = geometry
  changes.append({'river_group': river.get('river_group'), 'owner_slug': water.get('slug'), 'before': before, 'after': geometry, 'provenance': provenance})
 if changes:
  backup = waters_path.with_name('waters.json.audit-backup.json')
  if backup.exists() and backup.read_bytes() != original:
   raise RuntimeError(f'refusing to overwrite non-matching backup: {backup}')
  if not backup.exists(): backup.write_bytes(original)
  waters_path.write_text(json.dumps(waters, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
 artifact = {'schema_version': 1, 'source_snapshot_sha256': hashlib.sha256(Path(index).read_bytes()).hexdigest(), 'changes': changes, 'skipped': skipped}
 Path(diff_path).write_text(json.dumps(artifact, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
 Path(provenance_path).write_text(json.dumps({'schema_version': 1, 'repairs': [{'river_group': c['river_group'], **c['provenance']} for c in changes]}, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
 return artifact

def markdown(report):
 lines=['# River segment audit','',f"Schema: `{report['schema_version']}`",f"Snapshot: `{report.get('snapshot_sha256','')}`",'',
        f"## Gate: **{report.get('gate',{}).get('status','UNKNOWN')}**",'']
 blockers=report.get('gate',{}).get('blocking_findings',[])
 lines.append('- Blocking codes: '+(', '.join(f'`{x}`' for x in blockers) if blockers else 'none'))
 lines += ['', '## Summary','']
 for k,v in report['summary'].items(): lines.append(f'- **{k}**: {v}')
 if report.get('baseline'):
  lines += ['', '## Baseline deltas','']
  for k,v in report['baseline']['summary_deltas'].items(): lines.append(f'- **{k}**: {v:+d}')
 lines += ['', '## Coverage grid','', '| County | Contracted | Geometry | Missing | Findings | Overlay rivers | Overlay lakes | Status |', '|---|---:|---:|---:|---:|---:|---:|---|']
 for c in report.get('cells',[]):
  lines.append(f"| {c['county']} | {c['contracted']} | {c['with_geometry']} | {c['missing_geometry']} | {c['finding_count']} | {c['overlay']['rivers']} | {c['overlay']['lakes']} | {c['coverage_status']} |")
 lines += ['', '## Findings','']
 for r in report['rivers']:
  for finding in r.get('findings',[]):
   details={k:v for k,v in finding.items() if k != 'code'}
   suffix=' — '+json.dumps(details, ensure_ascii=False, sort_keys=True) if details else ''
   lines.append(f"- `{r['river_group']}`: **{finding.get('code','unknown')}**{suffix}")
 lines += ['', '## Overlay classification','']
 for item in report.get('overlays',[]):
  lines.append(f"- `{item['slug']}` — {item['kind']} / {item['classification']} / {item['county']} / {item['name']}")
 return '\n'.join(lines)+'\n'
def main():
 p=argparse.ArgumentParser(); p.add_argument('--osm-index',required=True); p.add_argument('--out-json',required=True); p.add_argument('--out-md',required=True); p.add_argument('--root',type=Path,default=ROOT, help='fixture/project root containing public/data and data/processed'); p.add_argument('--baseline'); p.add_argument('--aliases'); p.add_argument('--exceptions'); p.add_argument('--gate',action='store_true'); p.add_argument('--repair',action='store_true', help='apply only deterministic OSM-backed geometry repairs'); p.add_argument('--repair-diff', default='data/processed/river_segment_repairs.json'); p.add_argument('--repair-provenance', default='data/processed/river_segment_repair_provenance.json'); p.add_argument('--repair-scope', default='cerna,cerna valcea,ialomita,sieu,timis', help='comma-separated normalized river groups eligible for repair'); a=p.parse_args()
 report,hard=audit(Path(a.osm_index),a.root,a.aliases,a.exceptions)
 if a.repair:
  scope={norm(x) for x in a.repair_scope.split(',') if norm(x)}
  diff=Path(a.repair_diff); provenance=Path(a.repair_provenance)
  if not diff.is_absolute(): diff=a.root/diff
  if not provenance.is_absolute(): provenance=a.root/provenance
  repair_geometries(Path(a.osm_index),a.root,report,scope,diff,provenance)
  report,hard=audit(Path(a.osm_index),a.root,a.aliases,a.exceptions)
 hard += apply_baseline(report, a.baseline)
 set_gate(report, hard)
 Path(a.out_json).write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8'); Path(a.out_md).write_text(markdown(report),encoding='utf8')
 if a.gate and hard:
  print('river segment gate: BLOCKED — '+', '.join(sorted(set(hard))),file=sys.stderr); return 1
 print('river segment gate: PASS' if a.gate else f"audited {len(report['rivers'])} river relations"); return 0
if __name__=='__main__': raise SystemExit(main())
