#!/usr/bin/env python3
"""Probe HOTOSM waterways.geojson for candidate names of unmatched bbox rivers/lakes."""
import json, sys, difflib, unicodedata, re
sys.path.insert(0, 'scripts')
from audit_missing_rivers import norm, core

fc = json.load(open('data/sources/waterways.geojson'))
feats = fc['features']

def norm2(s):
    if not s: return ''
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', s.lower()).strip()

# all name fields per feature
def names_of(p):
    return [p.get('name'), p.get('name_ro'), p.get('name_en'), p.get('name_latin')]

targets = ['Lesuntu','Nou Roman','Râul Vadului','Valea Leșului','Valea Rîndiboului','Valea Strâmbii',
'Grotului','Holod','Jilț','Măgura Cisnădiei','Potop','Râmești','Tărcăița','Teleajen','Valea Ilvei',
'Volovăț','Vorona','Topa','Valea Bistrei','Buduresei','Călinești','Cârlibabei','Drăganului','Gepiș',
'Ierii','Valea Ierului','Lonei','Mișidului','Valea Omului','Răcătăului','Sighiștelului','Şartăşului',
'Șoimului','Țibăului','Valea Vadului','Sabasa','Izvorul Lotrului','Oașa','Podrăgel','Urlea',
'Doamnei','Sadu','Arpașu','Avrig','Racovița','Scoreiu','Olteț','Voila','Pecineagu','Râușor',
'Bolboci','Scropoasa','Cornetu','Câineni','Dopca','Pâncota','Zădăreni','Poiana Uzului','Pangrati',
'Reconstrucția','Vaduri','Secu','Gura Golumbului','Trei Ape','Bistra Iezer','Tismana','Valea Mare',
'Vâja','Cinciș','Ostrov','Subcetate','Hațeg','Valea de Pești','Câmpu lui Neag','Tăul Teliucului',
'Bondureasa','Someșul Cald','Săcălaia','Valea Băii','Beliș','Floroiu','Gilău','Șoimu','Gheorgheni',
'Colibița','Izvorul Măgurii','Tăul Zânelor','Bentu','Lighet','Vinderel','Ivanul','Pojorâta',
'Topolovăț','Lățunaș','Malaia','Muntinu','Vlădești','Petrimanu','Vidra','Balindru','Prisaca Cerna',
'Mărghitaș','Mărul superior','Tăria Mare','Lia','Mija','Peleaga','Roşiile','Slăvei','Tăul Verde',
'Zănoaga','Ştevia','Viorica','Tăul Ţapului','Tăul Înghetat','Oglinda Mândrii','Acumulare Arpașu',
'Lacul montan Avrig','Lacul montan Doamnei','Lacul montan Podrăgel','Lacul Urlea','Oașa','Podragu Mare',
'Râul Cibinul Inferior','Râul Măgura Cisnădiei','Sadu V','Sadu II','Pârâul Valea Strâmbii',
'Râul Grotului','Râul Jilț','Râul Holod','Râul Potop','Râul Râmești','Râul Tărcăița',
'Râul Sabasa','Râul Izvorul Lotrului','Valea Drăganului','Valea Ierii','Valea Răcătăului',
'Valea Vadului','Valea Sighiștelului','Valea Șoimului','Valea Omului','Valea Mișidului',
'Valea Buduresei','Valea Gepiș','Valea Bistrei','Valea Cârlibabei','Valea Țibăului','Valea Lonei']

index = {}
for f in feats:
    p = f['properties']
    for n in names_of(p):
        if n:
            key = norm2(n)
            if key and key not in index:
                index[key] = f

for t in targets:
    c = core(t)
    ct = set(c.split()) if c else set()
    cands = []
    for key, f in index.items():
        oc = core(key)
        if not oc: continue
        ot = set(oc.split())
        inter = ct & ot
        if inter:
            cands.append((len(inter), key, f))
        elif len(ct) >= 1:
            fw = next(iter(ct))
            if len(fw) >= 4 and difflib.SequenceMatcher(None, fw, oc).ratio() > 0.6:
                cands.append((0.5, key, f))
    cands.sort(key=lambda x: -x[0])
    print(f"\n### {t}")
    for sc, key, f in cands[:5]:
        p = f['properties']
        g = f['geometry']
        print(f"   {sc} | '{key}' | {g['type']} | waterway={p.get('waterway')} water={p.get('water')} nc={p.get('natural_class')}")
