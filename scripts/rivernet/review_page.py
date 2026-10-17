"""Standalone Leaflet review page (plan T3.5). Output is not shipped (gitignored)."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .report import flatten_lines, sector_coords
from .textnorm import fold

LEAFLET = "1.9.4"

TEMPLATE = """<!doctype html><html lang="ro"><head><meta charset="utf-8"><title>__TITLE__</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/__LV__/leaflet.min.css">
<style>html,body{height:100%;margin:0;font:14px system-ui}#app{display:flex;height:100%}
#list{width:340px;overflow:auto;border-right:1px solid #ccc;padding:8px}#map{flex:1}
.it{padding:6px;border-bottom:1px solid #eee;cursor:pointer}.it:hover{background:#f3f3f3}
.s-resolved{border-left:4px solid #d32f2f}.s-review{border-left:4px solid #f57c00}.s-unresolved{border-left:4px solid #9e9e9e}
small{color:#555}.lg{font-size:12px;margin:6px 0 10px;line-height:1.7}
.lg i{display:inline-block;width:22px;height:0;vertical-align:middle;margin-right:4px}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;border:2px solid #fff;box-shadow:0 0 0 1px #333;vertical-align:middle;margin-right:4px}</style></head><body><div id="app"><div id="list">
<h3>__TITLE__</h3>
<div class="lg"><i style="border-top:5px solid #d32f2f"></i>sector nou (resolved)
<i style="border-top:5px solid #f57c00;margin-left:8px"></i>review<br>
<i style="border-top:3px dashed #333"></i>geometria veche
<span class="dot" style="background:#2e7d32;margin-left:8px"></span>de la
<span class="dot" style="background:#1565c0;margin-left:8px"></span>până la</div><label>Status <select id="f"><option value="">all</option><option>resolved</option><option>review</option><option>unresolved</option></select></label>
<div id="items"></div></div><div id="map"></div></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/__LV__/leaflet.min.js"></script>
<script>
const DATA = __DATA__;
const map = L.map('map').setView([45.9, 24.9], 7);
// Esri basemaps: they load from file:// pages and previews (no Referer), unlike
// tile.openstreetmap.org, whose usage policy blocks those. Light grey by
// default so the sector lines stand out; topographic map for place names.
const esri = (svc) => `https://server.arcgisonline.com/ArcGIS/rest/services/${svc}/MapServer/tile/{z}/{y}/{x}`;
const light = L.tileLayer(esri('Canvas/World_Light_Gray_Base'), {maxZoom: 16, attribution: 'Tiles &copy; Esri'}).addTo(map);
const labels = L.tileLayer(esri('Canvas/World_Light_Gray_Reference'), {maxZoom: 16}).addTo(map);
const topo = L.tileLayer(esri('World_Topo_Map'), {maxZoom: 19, attribution: 'Tiles &copy; Esri'});
L.control.layers({'Hartă deschisă': light, 'Hartă topografică': topo}, {'Nume localități': labels}).addTo(map);
const layers = {};
const items = document.getElementById('items');
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function ep(e){return e?esc(e.kind)+' ('+esc(e.method)+', '+e.confidence+') m='+e.m:'-';}
DATA.forEach(d=>{
  const g = L.layerGroup();
  if (d.old) L.geoJSON(d.old,{style:{color:'#333',weight:3,opacity:.85,dashArray:'6 6'}}).addTo(g);
  if (d.coords && d.coords.length) {
    const ll = d.coords.map(c=>[c[1],c[0]]);
    L.polyline(ll,{color:'#fff',weight:9,opacity:.9}).addTo(g);  // white casing
    L.polyline(ll,{color:d.status==='resolved'?'#d32f2f':'#f57c00',weight:5}).addTo(g);
    [['from',d.coords[0],'#2e7d32'],['to',d.coords[d.coords.length-1],'#1565c0']].forEach(([k,c,col])=>{
      L.circleMarker([c[1],c[0]],{radius:8,color:'#fff',weight:3,fillColor:col,fillOpacity:1})
        .bindTooltip(k==='from'?'de la':'până la',{permanent:false}).bindPopup(k+': '+ep(d[k])).addTo(g);});
  }
  g.bindPopup('<b>'+esc(d.name)+'</b><br>'+esc(d.limite)+'<br>contract '+esc(d.contract_km)+' km, drawn '+esc(d.drawn_km)+' km<br>'+esc(d.status)+' / '+esc(d.confidence)+'<br>'+esc((d.reasons||[]).join(', ')));
  layers[d.slug] = g;
  const el = document.createElement('div');
  el.className = 'it s-' + d.status; el.dataset.status = d.status; el.dataset.slug = d.slug;
  el.innerHTML = '<b>'+esc(d.name)+'</b> <small>'+esc(d.judet)+'</small><br><small>'+esc(d.limite)+'</small><br><small>'+esc(d.status)+'/'+esc(d.confidence)+' ratio '+esc(d.km_ratio)+'</small>';
  el.onclick = ()=>{ Object.values(layers).forEach(l=>map.removeLayer(l)); g.addTo(map);
    const b = L.featureGroup(g.getLayers()).getBounds(); if (b.isValid()) map.fitBounds(b.pad(.2)); };
  items.appendChild(el);
});
document.getElementById('f').onchange = e => { document.querySelectorAll('.it').forEach(el => el.style.display = (!e.target.value || el.dataset.status===e.target.value) ? '' : 'none'); };
</script></body></html>"""


def render(
    sectors: Iterable[Mapping[str, Any]],
    waters: Mapping[str, Mapping[str, Any]],
    courses: Mapping[str, Mapping[str, Any]],
    county: str | None = None,
) -> str:
    rows: list[dict[str, Any]] = []
    for s in sectors:
        if county and fold(s.get("judet")) != fold(county):
            continue
        w = waters.get(s["slug"], {})
        coords: list[Any] = []
        c = courses.get((s.get("course") or {}).get("course_id") or "")
        if s.get("from") and s.get("to") and c:
            coords = [list(p) for p in sector_coords(c, s["from"]["m"], s["to"]["m"])]
        old = {"type": "MultiLineString", "coordinates": [[list(p) for p in ln] for ln in flatten_lines(w.get("geometry"))]} if w.get("geometry") else None
        rows.append({
            "slug": s["slug"], "name": s.get("name"), "judet": s.get("judet"), "limite": s.get("limite"),
            "contract_km": s.get("contract_km"), "drawn_km": None if s.get("length_m") is None else round(s["length_m"] / 1000, 2),
            "km_ratio": s.get("km_ratio"), "status": s["status"], "confidence": s["confidence"],
            "reasons": s["reasons"], "from": s.get("from"), "to": s.get("to"), "coords": coords, "old": old,
        })
    rows.sort(key=lambda r: (r["status"] != "review", r["name"] or "", r["slug"]))
    # '<' escaped so no data string can close the script element
    data = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    title = "Review: " + (county or "all counties")
    return TEMPLATE.replace("__DATA__", data).replace("__LV__", LEAFLET).replace("__TITLE__", html.escape(title))


def cli(argv: list[str]) -> int:
    import argparse
    import gzip
    import sys

    ap = argparse.ArgumentParser(prog="rivernet review-page")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--county")
    g.add_argument("--all", action="store_true")
    ap.add_argument("--sectors", default="data/sectors/sectors.jsonl")
    ap.add_argument("--courses", default="data/rivernet/courses.jsonl.gz")
    ap.add_argument("--waters", default="public/data/waters.json")
    ap.add_argument("--out-dir", default="data/sectors/review")
    ns = ap.parse_args(argv)
    for p in (ns.sectors, ns.courses):
        if not Path(p).exists():
            print(f"rivernet review-page: {p} missing", file=sys.stderr)
            return 1
    sectors = [json.loads(x) for x in Path(ns.sectors).read_text(encoding="utf-8").splitlines() if x.strip()]
    with gzip.open(ns.courses, "rt", encoding="utf-8") as f:
        courses = {c["course_id"]: c for c in (json.loads(x) for x in f if x.strip())}
    waters = {w["slug"]: w for w in json.loads(Path(ns.waters).read_text(encoding="utf-8"))} if Path(ns.waters).exists() else {}
    out = Path(ns.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    counties = sorted({s.get("judet") for s in sectors if s.get("judet")}) if ns.all else [ns.county]
    for c in counties:
        name = fold(c).replace(" ", "-") or "county"
        (out / f"{name}.html").write_text(render(sectors, waters, courses, c), encoding="utf-8", newline="\n")
    print(f"wrote {len(counties)} page(s) to {out}")
    return 0
