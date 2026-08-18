# Raport mapare ape contractate — bazinul Bistrița (Broșteni/Borsec/Ceahlău) + sweep național (t_66b48ee0)

Data: 2026-08-12. Continuare a t_1f8b1b06 (215 râuri mapate). `waters.json`: **994 → 1014** ape, **524 → 543** cu geometrie.

## 1. Zona raportată de utilizator (Bistrița, Neamț/Harghita)

Raportul „mai sunt ape nemapate" în jurul Broșteni / Borsec / Parcul Național Ceahlău a fost **confirmat și reparat**. Cauza principală: grupul `bistrita` avea ca owner de geometrie **Râul Bistrița din județul Bistrița-Năsăud** (bazinul Someșul Mare, lon 24.4–24.6) — un râu complet diferit de Bistrița din bazinul Siretului (lon 25.0–26.9, prin Broșteni/Bicaz/Piatra Neamț). Cursul real prin zona raportată **nu era desenat deloc**, iar contractele NEAMȚ (32 km) și BACĂU (39 km) lipseau din waters.json.

### Remedieri
1. **Grup `bistrita` corectat**:
   - Râul Bistrița (B-N, Someșul Mare) mutat în propriul grup `bistrita-bn`; i s-a adăugat și al doilea contract ANPA (28 km; cel de 25 km exista deja).
   - Duplicatul legacy „Bistra Aurie II" (jfwp7w1y) comasat în „Râul Bistrița Aurie II".
   - Cursul real (clusterurile OSM `bistrita` 25.0–26.3 + 26.3–27.0) atașat ca **un singur LineString ordonat sursă→gură** (partile dublu-mapate au fost deduplicate) — click-resolution funcționează monoton.
   - **Intervale de sector exacte** (sectorStart/sectorEnd) pe tot cursul, din limitele oficiale ANPA/Romsilva: Aurie I→Cârlibaba, Aurie II→Mestecăniș, Aurie III→conf. Dorna, I Zugreni→baraj Zugreni, II→pod Mălișor, IV→Lunca–Fărcașa, V→Fărcașa–Zahorna, VI→Baraj Bicaz–Pangrati, NEAMȚ 32→Reconstrucția–jud. Bacău, BACĂU 39→jud. Bacău–Siret.
2. **Contracte adăugate** (bazinul Bistrița + Moldova + Târnava Mică):
   - Râul Bistrița NEAMȚ (AJVPS NEAMȚ, 32 km), Râul Bistrița BACĂU (AJVPS BACĂU, 39 km)
   - Râul Moldova NEAMȚ (AVPS BRADUL PIATRA NEAMȚ, 40 km) + NEAMȚ (AVPS ROMAN, 40 km, sectorul gurii) + SUCEAVA (AJVPS BOTOȘANI, 59 km)
   - Râul Târnava Mică HARGHITA (5 km) + MUREȘ (96 km)
3. **Geometrie atașată** pentru Romsilva din zonă care era invizibilă: Bistricioara tronson I (Harghita, curs OSM complet), Izvoarele Cracăului (Neamț). Sabasa (Neamț) — fără curs OSM cu nume → geocodat (bbox clickabil la 47.20N 25.82E).

### Verificare click (acoperită acum de testele `river-course` și E2E `map-segment-qa`)
23/23 PASS: Broșteni→Bistrița II (A.LUCIOPERCA), Bicaz→AJVPS NEAMȚ, Piatra Neamț→AJVPS NEAMȚ (32 km), Bacău→AJVPS BACĂU (39 km), Bistricioara→D.S. Harghita, Moldova (gura)→AVPS ROMAN, Târnava Mică→sectoarele corecte.

## 2. Sweep național — toate rândurile rămase „missing"

### Contracte ANPA adăugate (12) — toate cu geometrie OSM unde există curs numit
| Râu | Județ | Asociație | km | Geometrie |
|---|---|---|---|---|
| Râul Someșul Mare | Bistrița-Năsăud | AJVPS BISTRIȚA-NĂSĂUD | 61 | grup `somesul-mare` (curs desenat de owner) |
| Râul Someșul Mare | Sălaj | AJVPS SĂLAJ | 93 | grup `somes` (sectorul Sălaj al Someșului) |
| Râul Crasna | Sălaj | AJVPS SĂLAJ | 65 | grup `crasna` |
| Râul Crasna | Vaslui | AJVPS VASLUI | 43 | cluster OSM `crasna` (Vaslui) |
| Râul Sebeș | Mureș | AJVPS MUREȘ | 21 | cluster OSM `sebes` (Mureș) |
| Râul Miletin | Iași | AVPS IAȘI | 35 | cluster OSM `miletin` |
| Râul Țibleș | Maramureș | AJVPS MARAMUREȘ | 27 | cluster OSM `tibles` |
| Râul Neajlov | Giurgiu | AJVPS GIURGIU | — | cluster OSM `neajlov` |
| Râul Câlniștea | Teleorman | AJVPS TELEORMAN | — | cluster OSM `calnistea` |
| Râul Călmățui | Teleorman | AJVPS TELEORMAN | — | cluster OSM `calmatui` |
| Râul Șușița | Vrancea | AJVPS VRANCEA | 61 | cluster OSM `susita` (Vrancea) |
| Râul Râmnicu Sărat | Vrancea | AJVPS VRANCEA | — | cluster OSM `ramnicu sarat` |
| Lac acumulare Arpașu | Brașov | AVPS FĂGĂRAȘ | — | geocodat (bbox clickabil 45.60N 24.69E) |

### Romsilva — 6 ape cu nume dublat greșit („Râul Râul X") + geometrie lipsă
| Apă | Județ | Fix |
|---|---|---|
| Râul Şes | Hunedoara | redenumit + geometrie `raul ses` (12 km) |
| Râul Mare Superior | Hunedoara | redenumit + geometrie `raul mare` |
| Râul Bărbat Superior/Inferior | Hunedoara | redenumite + geometrie `barbat`, sectoare exacte 17/42 km |
| Râul Mare Porumbacu | Sibiu | redenumit + geometrie `porumbacu` |
| Pârâul Bistrița | Vâlcea | redenumit + geometrie `bistrita` (Vâlcea) |
| Izvorul Lotrului | Vâlcea | în grupul `lotru`, sector sursă [0, 0.47] (restul Lotrului sectorizat explicit) |

### Remediere bug date: Râul Călmățui (Brăila) avea geometria Călmățuiului din TELEORMAN (lon 24.6) — reatașat clusterul Buzău/Brăila (lon 27.3), corectând și centroidul județului Brăila folosit la matching.

### present-hidden reparate (8 din 14)
Japșa Veriga, Japșa Stanca (Brăila), Bega superior-Luncani (Timiș), grupul Cerna-Herculane (Caraș-Severin/Mehedinți, owner pe Cerna Superioară), Râul Călmățui Brăila, plus cele 6 Romsilva de mai sus.

## 3. Rămase vizibil-nemapate — cu motiv explicit (6 clusteruri OSM, 3 ape distincte)
| Apă | Județ | Motiv |
|---|---|---|
| Lacul Izvorul (Măgurii) | Bistrița-Năsăud | lac, fără curs OSM numit (nu se inventează geometrie) |
| Râul Botiza | Maramureș | singurul cluster OSM `botiza` e în alt județ (44.3N) |
| Valea Iadului Superior | Bihor | singurul cluster OSM `valea iadului` e în Covasna (45.5N) |
| Acumulare Dragomira | Botoșani | singurul cluster OSM `dragomira` e lângă Focșani (46.0N) |

Pârâul Pământ Alb (Timiș): auditul o marca „anpa-missing" printr-un fals pozitiv — contractul EXISTĂ (anpa-anpa-0603, cu geometrie); clusterul OSM „valea paraul alb" din Vâlcea e un alt curs, necontractat.

## 4. Statistici finale
- waters.json: **1014** ape (994 → +20 net: 21 adăugate, 1 comasat), **543** cu geometrie (524 → +19).
- Asociații: `ape` recalculate pentru 16 intrări (scripts/recompute_assoc_counts.py).
- Audit (scripts/audit_regions.py): present 911, present-bbox 26, present-hidden 6 (toate cu motiv), anpa-missing 1 (fals pozitiv explicat), romsilva 0.
- Build Next.js: OK. Verificare click bazin Bistrița: 23/23 PASS.
