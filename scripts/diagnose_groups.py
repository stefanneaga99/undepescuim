#!/usr/bin/env python3
"""Diagnose multi-contract groups for issues: missing/duplicate fracs, geometry anomalies."""
import json
from collections import defaultdict

waters = json.load(open('public/data/waters.json', encoding='utf-8'))
groups = defaultdict(list)
for w in waters:
    g = w.get('riverGroup') or ''
    if g:
        groups[g].append(w)
multi = {k: v for k, v in sorted(groups.items()) if len(v) >= 2}

print('=== Groups with missing frac / duplicate fracs / multiple geometries ===')
for g, members in multi.items():
    fracs = [m.get('course_frac') for m in members]
    has_geom = [bool(m.get('geometry')) for m in members]
    ngeom = sum(has_geom)
    nfrac = sum(1 for f in fracs if isinstance(f, (int, float)))
    frac_set = sorted(set(round(f, 4) for f in fracs if isinstance(f, (int, float))))
    nfracval = len([f for f in fracs if isinstance(f, (int, float))])
    issue = []
    if nfrac < len(members):
        issue.append(f'{len(members) - nfrac} missing frac')
    if len(frac_set) < nfracval:
        issue.append('DUPLICATE fracs: ' + str(frac_set))
    if ngeom > 1:
        issue.append(f'{ngeom} members WITH geometry')
    if issue:
        print(f'  {g:16} n={len(members):2} geom={ngeom} ' + ' '.join(issue))
        for m in members:
            print(f'      {m["slug"]:18} {m.get("name", "")[:38]:40} [{m.get("judet", ""):12}] frac={m.get("course_frac")} geom={bool(m.get("geometry"))}')
