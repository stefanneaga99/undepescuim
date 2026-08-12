#!/usr/bin/env python3
"""Fix Romsilva 'Buzăul superior': join the buzau group as a geometry-less
sector [0, Brădet] instead of its own group + 60km geometry that double-draws
the upper course and shadows AJVPS Covasna's sector in click resolution."""
import json

WATERS = 'public/data/waters.json'
data = json.load(open(WATERS, encoding='utf-8'))

target = None
for w in data:
    if w.get('slug') == 'romsilva-brasov-buzaul-superior':
        target = w
        break
assert target is not None, 'water not found'

print('BEFORE:')
print('  riverGroup:', target.get('riverGroup'))
print('  course_frac:', target.get('course_frac'))
print('  sectorStart/End:', target.get('sectorStart'), target.get('sectorEnd'))
print('  geometry:', 'Y' if target.get('geometry') else 'N')
print('  bbox:', target.get('bbox'))

# Join the ANPA group, drop own geometry, own the headwater sector izvoare→Brădet.
target['riverGroup'] = 'buzau'
target['geometry'] = None
target['bbox'] = None
target['course_frac'] = 0.04          # Voronoi anchor near source (fallback path)
target['sectorStart'] = 0.0           # izvoare
target['sectorEnd'] = 0.081           # localitatea Brădet (village, Covasna, frac 0.0803)
target['mainCourse'] = True           # sector of the shared course, not a tributary

# Sanity: the remaining members of the old group
old_members = [w['slug'] for w in data if w.get('riverGroup') == 'buzaul-superior']
print('  remaining buzaul-superior members:', old_members)

json.dump(data, open(WATERS, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('AFTER:')
print('  riverGroup:', target.get('riverGroup'))
print('  course_frac:', target.get('course_frac'))
print('  sectorStart/End:', target.get('sectorStart'), target.get('sectorEnd'))
print('  geometry:', 'Y' if target.get('geometry') else 'N')
print('  bbox:', target.get('bbox'))
print('done')
