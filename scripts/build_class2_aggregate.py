#!/usr/bin/env python3
"""Build the deterministic, Preview-only Class2 physical geometry aggregate."""
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = Path('/home/stefan/undepescuim-local-work/.local-work/class2-branch-audit.json')
OUT = ROOT / 'public/data/preview_class2_physical.json'
BRANCHES = [f'local/class2-{i:02d}' for i in range(2, 12)]

def git_json(branch: str, filename: str) -> dict:
    raw = subprocess.check_output(['git', 'show', f'{branch}:{filename}'], cwd=ROOT)
    return json.loads(raw)

def main() -> None:
    audit = json.loads(AUDIT.read_text())
    inventory_sha = audit['branches'][0]['sourceInventorySha256']
    records: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    source_artifacts = []
    for branch in BRANCHES:
        chunk = branch.rsplit('-', 1)[1]
        filename = f'public/data/preview_class2_physical_class2-{chunk}.json'
        digest = hashlib.sha256(subprocess.check_output(['git', 'show', f'{branch}:{filename}'], cwd=ROOT)).hexdigest()
        source_artifacts.append({'branch': branch, 'commit': subprocess.check_output(['git', 'rev-parse', branch], cwd=ROOT, text=True).strip(), 'path': filename, 'sha256': digest})
        artifact = git_json(branch, filename)
        source_commit = subprocess.check_output(['git', 'rev-parse', branch], cwd=ROOT, text=True).strip()
        for record in artifact['records']:
            slug = record['slug'] if 'slug' in record else record.get('waterSlug')
            if not slug:
                # Historical artifacts use the record's canonicalSlug in some chunks.
                slug = record.get('canonicalSlug')
            if not slug:
                raise ValueError(f'missing slug in {branch}: {record.keys()}')
            for candidate in record.get('physicalCandidates', []):
                cid = str(candidate.get('id', ''))
                gh = str(candidate.get('geometryHash', ''))
                key = (slug, cid, gh)
                if key in seen:
                    continue
                seen.add(key)
                candidate['sourceBranch'] = branch
                candidate['sourceCommit'] = source_commit
            record['sourceBranch'] = branch
            record['sourceCommit'] = source_commit
            records.append(record)
    records.sort(key=lambda r: (r['slug'], r['sourceBranch']))
    payload = {
        'artifact': 'class2-physical-preview-aggregate',
        'schemaVersion': 1,
        'class': 2,
        'previewOnly': True,
        'canonicalMutation': False,
        'legalStatus': 'legal sector unverified',
        'disclosure': 'Traseu fizic experimental; limitele sectorului contractual nu sunt verificate.',
        'sourceInventorySha256': inventory_sha,
        'excludedChunks': ['CLASS2-01'],
        'deduplication': {'key': ['waterSlug', 'candidate.id', 'candidate.geometryHash'], 'rule': 'retain distinct source candidates; remove exact repeated keys only'},
        'sourceArtifacts': source_artifacts,
        'recordCount': len(records),
        'candidateCount': sum(len(r.get('physicalCandidates', [])) for r in records),
        'records': records,
    }
    text = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    OUT.write_text(text)
    print(json.dumps({'path': str(OUT), 'sha256': hashlib.sha256(text.encode()).hexdigest(), 'records': len(records), 'candidates': payload['candidateCount']}))

if __name__ == '__main__':
    main()
