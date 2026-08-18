#!/usr/bin/env python3
"""Build a stable relation/way index from a local Overpass snapshot.
No network is ever used; --no-network is retained as an explicit contract.
"""
from __future__ import annotations
import argparse, gzip, hashlib, json
from pathlib import Path

def load(path):
    with open(path,encoding='utf-8') as f: return json.load(f)

def build(doc):
    els=doc.get('elements',doc if isinstance(doc,list) else [])
    nodes={int(e['id']):[e.get('lon'),e.get('lat')] for e in els if e.get('type')=='node' and 'lon' in e}
    ways={int(e['id']):e for e in els if e.get('type')=='way'}
    relations=[]
    for r in els:
        if r.get('type')!='relation': continue
        members=[]; ids=[]
        for m in r.get('members',[]):
            if m.get('type')!='way': continue
            wid=int(m['ref']); ids.append(wid)
            w=ways.get(wid); coords=[nodes[n] for n in (w or {}).get('nodes',[]) if n in nodes]
            members.append({'way_id':wid,'role':m.get('role',''),'sequence':len(members),'present':w is not None and len(coords)>=2})
        relations.append({'osm_id':int(r['id']),'kind':'relation','name':(r.get('tags') or {}).get('name',''),'named_aliases':sorted({v for k,v in (r.get('tags') or {}).items() if k in ('name','alt_name','old_name','loc_name')}), 'all_way_ids':sorted(ids), 'members':members})
    indexed=[]
    for rid in relations:
        indexed.append(rid)
    for wid,w in sorted(ways.items()):
        if not w.get('nodes'): continue
        indexed.append({'osm_id':wid,'kind':'way','name':(w.get('tags') or {}).get('name',''),'named_aliases':sorted({v for k,v in (w.get('tags') or {}).items() if k in ('name','alt_name','old_name','loc_name')}),'all_way_ids':[wid],'node_ids':w['nodes'],'coordinates':[nodes[n] for n in w['nodes'] if n in nodes]})
    return indexed, len(nodes), len(ways), len(relations)

def main():
    p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--out',required=True); p.add_argument('--manifest',required=True); p.add_argument('--no-network',action='store_true'); a=p.parse_args()
    raw=Path(a.input).read_bytes()
    doc=load(a.input)
    entries,n,w,r=build(doc); out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('wb') as raw_out:
        with gzip.GzipFile(filename='',fileobj=raw_out,mode='wb',mtime=0) as gz:
            import io
            with io.TextIOWrapper(gz,encoding='utf-8',newline='\n') as f:
                for item in entries: f.write(json.dumps(item,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n')
    meta=load(a.input).get('osm3s',{}) if isinstance(load(a.input),dict) else {}
    manifest={'schema_version':1,'indexer_version':'river-segment-index-v1','source':{'url':'https://overpass-api.de/api/interpreter','snapshot_timestamp':meta.get('timestamp_osm_base'),'copyright':meta.get('copyright')},'snapshot':{'path':str(Path(a.input)),'sha256':hashlib.sha256(raw).hexdigest(),'size_bytes':len(raw)},'index':{'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'entries':len(entries)},'counts':{'nodes':n,'ways':w,'relations':r}}
    Path(a.manifest).write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__': main()
