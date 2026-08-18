#!/usr/bin/env python3
"""Check exact OSM index names for specific river candidates (both extracts)."""
import json, sys, unicodedata, re
sys.path.insert(0, 'scripts')
from audit_missing_rivers import norm, core, load_osm_index

name_index, geoms = load_osm_index()
all_names = sorted(name_index.keys())

def find(substr):
    hits = [n for n in all_names if substr in n]
    return hits[:12]

checks = {
    'holod': ['holod', 'holodul', 'paraul holod'],
    'jilt': ['jilt', 'jilț', 'jiltul'],
    'drăgan': ['dragan', 'draganul', 'valea dragan'],
    'iara/ierii': ['iara', 'ierii', 'paraul ierii'],
    'vadului': ['vadului', 'valea vadului'],
    'sabasa': ['sabasa'],
    'cârlibaba': ['carlibaba', 'cirlibaba'],
    'gepiș': ['gepis', 'gepiu', 'ghepiu'],
    'sighiștel': ['sighistel', 'sighishtel'],
    'șoimului': ['soimului', 'paraul soimului'],
    'răcătău': ['racatau', 'racataului'],
    'ierului': ['ierului', 'paraul ierului'],
    'topa': ['topa', 'paraul topa'],
    'bistrei': ['bistrei', 'bistra', 'paraul bistra'],
    'lesuntu': ['lesuntu', 'lesun', 'lesu'],
    'nou roman': ['roman', 'nou roman'],
    'leșului': ['lesului', 'paraul lesului'],
    'rîndiboului': ['rindiboului', 'rindibou', 'rindib'],
    'strâmbii': ['strambii', 'stramba', 'stramb'],
    'grotului': ['grotului', 'grotu', 'grot'],
    'măgura cisnădiei': ['magura cisnadiei', 'cisnadiei', 'cisnadie'],
    'potop': ['potop', 'potopul'],
    'râmești': ['ramesti', 'rameste'],
    'tărcăița': ['tarca', 'tarcaita'],
    'teleajen': ['teleajen'],
    'ilvei': ['ilvei', 'valea ilvei'],
    'volovăț': ['volovat', 'volovatul'],
    'vorona': ['vorona', 'voron'],
    'buduresei': ['buduresei', 'budureasa'],
    'călinești': ['calinesti', 'calinestilor'],
    'țibăului': ['tibaului', 'tibaul', 'tibau'],
    'lonei': ['lonei', 'lona'],
    'mișidului': ['misidului', 'misid'],
    'omului': ['omului', 'paraul omului'],
    'sartasului': ['sartasului', 'sartas'],
    'rau vadului': ['raul vadului', 'vadului'],
    'izvorul lotrului': ['lotrului', 'lotrisor', 'izvorul lotrului'],
    'cibin': ['cibin'],
    'noul roman': ['noul roman'],
    'geamartal': ['geamartal'],
    'doamnei': ['doamnei', 'paraul doamnei'],
    'sadu': ['sadu', 'paraul sadu'],
    'arpaș': ['arpas', 'arpasu', 'paraul arpasu'],
    'avrig': ['avrig', 'paraul avrig'],
    'racovița': ['racovita'],
    'scoreiu': ['scoreiu', 'scorei'],
    'olteț': ['oltet'],
    'voila': ['voila'],
    'urlea': ['urlea'],
    'oasa': ['oasa'],
    'podragu': ['podrag', 'podragu'],
    'doamnei lac': ['lacul doamnei', 'batca doamnei'],
    'pecineagu': ['pecineagu'],
    'rausor': ['rausor'],
    'bolboci': ['bolboci'],
    'scropoasa': ['scropoasa'],
    'cornetu': ['cornetu', 'corne'],
    'caineni': ['caineni', 'caineni'],
    'dopca': ['dopca'],
    'muntinu': ['muntinu', 'munteni'],
    'vlădești': ['vladesti'],
    'petrimanu': ['petrimanu'],
    'vidra': ['vidra'],
    'balindru': ['balindru'],
    'malaia': ['malaia'],
    'grot': ['grot'],
    'jilip': ['jilip'],
    'jiet': ['jiet'],
}

for label, subs in checks.items():
    found = set()
    for s in subs:
        found.update(find(s))
    if found:
        print(f"\n### {label}:")
        for n in sorted(found)[:12]:
            print(f"   '{n}'")
    else:
        print(f"\n### {label}: <none>")
