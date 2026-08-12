# Raport — râuri contractate mapate suplimentar (t_1f8b1b06)

## Problema raportată

Utilizator (mobil, 2026-08-12): zona Moinești / Comănești / Dărmănești
(Bacău, bazinul Trotușului) afișa multe râuri doar ca linii albastre de
basemap — fără evidențiere portocalie și fără card clicabil. „Au rămas multe
râuri nemapate.”

## Cauza rădăcină

Auditul anterior (t_242be1eb) clasifica râurile OSM după lista ANPA
„contractate” (682 ape). Dar lista **Romsilva** („Lista habitatelor piscicole
naturale din apele de munte rămase în administrarea directă a RNP-Romsilva”,
Protocol 12935/LAV/17.09.2013, ANEXA 1 — 289 ape de munte) nu era folosită
corect:

1. `audit_regions.py` avea un parser defect al fișierului txt — regex-ul
   captura textul limitelor în nume (`'Dofteana de la izvoare - la confl. cu
   raul Trotuș'`), deci nu se potrivea NICIODATĂ cu clusterul OSM `dofteana`.
   Mai grav: potrivirea pe județ compara `BACĂU` (sursă) cu `Bacău`
   (waters.json) → distanța era mereu 1e9 → nicio clasificare
   anpa-missing/romsilva. Ambele bug-uri reparate.
2. Râurile Romsilva (Dofteana, Bărzăuța, Cașinul Superior — exact zona
   raportată!) nu existau deloc în waters.json.

## Ce s-a mapat

### 1. 207 ape Romsilva adăugate în waters.json (89 cu geometrie OSM)

Fiecare are asociația **Direcția Silvică <județ>** (RNP-Romsilva), limitele și
lungimea din lista oficială, plus geometria cursului OSM când există potrivire.

| Județ | Adăugate | Cu geometrie |
|---|---|---|
| Alba | 19 | 7 |
| Arad | 14 | 3 |
| Argeș | 12 | 7 |
| Bacău | 3 | 2 |
| Bihor | 7 | 3 |
| Bistrița-Năsăud | 3 | 2 |
| Brașov | 4 | 3 |
| Buzău | 2 | 2 |
| Caraș-Severin | 16 | 5 |
| Cluj | 8 | 0 |
| Covasna | 6 | 3 |
| Dâmbovița | 3 | 1 |
| Gorj | 7 | 4 |
| Harghita | 6 | 2 |
| Hunedoara | 15 | 7 |
| Maramureș | 18 | 10 |
| Mehedinți | 3 | 0 |
| Mureș | 12 | 8 |
| Neamț | 7 | 3 |
| Prahova | 3 | 1 |
| Sibiu | 8 | 4 |
| Suceava | 13 | 7 |
| Sălaj | 3 | 1 |
| Timiș | 2 | 1 |
| Vrancea | 6 | 2 |
| Vâlcea | 7 | 1 |
| **Total** | **207** | **89** |

### 2. 8 râuri ANPA fără geometrie, acum mapate (matcher agresiv cu gardă de județ)

- Valea Sebeșului (Brașov) → OSM `raul sebes`
- Valea Slănicului (Buzău) → OSM `paraul slanic`
- Râul Izvoarele Ampoiului (Alba) → OSM `ampoi`
- Valea Drăganului (Bihor) → OSM `dragan`
- Râul Vl. Finiş (Finişului) (Bihor) → OSM `finis`
- Râul Izvoarele Timișului (Caraș-Severin) → OSM `timis`
- Râul Izvoarele Cracăului (Neamț) → OSM `cracaul negru`
- Râul Pârâul Bistrița (Vâlcea) → OSM `bistrita`

### 3. Grupuri multi-sector corectate

Râurile Romsilva împărțite în sector superior/mijlociu/inferior împart acum
ACELAȘI riverGroup cu un singur posesor de geometrie (click-ul rezolvă
sectorul prin `course_frac` / `sectorStart-End`):

- Vișeul (superior/mijlociu/inferior, Maramureș), Barcăul (Sălaj),
  Ruscova, Neagra (Suceava), Gurghiul (Mureș), Latorița (Vâlcea),
  Sadu (Sibiu), Bicazul (Harghita), Tarcău (Neamț), Cerna (Caraș-Severin +
  Mehedinți = același râu Herculane), Someșul Rece (Cluj), etc.
- Sectorizare explicită: Bărzăuța Covasna [0, 15/33) / Bacău [15/33, 1];
  Bâsca Mică Covasna [0, 15/83) / Buzău [15/83, 1]; Cașinul Superior
  [0, 0.73) / Casinul inferior [0.73, 1].

### 4. Nu s-au amestecat râuri diferite cu același nume

Corecții explicite: Harghita Cașin (bazin Olt) ≠ Bacău Cașinul (bazin Siret);
Mureș Bistra ≠ Sibiu Bistra; Vâlcea Cerna ≠ Cerna Herculane;
Suceava Putna ≠ Vrancea Putna; Bistricioara Vâlcea/Gorj/Harghita sunt 3 râuri.

## Stare finală

- waters.json: **994** ape (**524** cu geometrie), față de 790 / 429 înainte
- asociatii: 94 (10 Direcții Silvice noi: arad, bacau, bistrita-nasaud,
  brasov, mures, prahova, salaj, suceava, timis, vrancea)
- Build Next.js OK, deployed la https://undepescuim.vercel.app (auto-deploy
  din main, verificat live: 994 ape, Dofteana/Bărzăuța/Cașinul Superior
  clicabile cu Direcția Silvică Bacău)
- Verificare click: 5/5 cazuri multi-sector (Bărzăuța, Cașinul) rezolvă
  corect; râurile single-contract (Dofteana, Trotuș, Tazlău, Uzul) cad pe
  propriul slug.

## Rămase nemapate (documentate, fără curs OSM găsit)

~161 râuri contractate (canale de irigații, japșe, bălți, mici pâraie fără
nume OSM) rămân fără geometrie — invizibile pe hartă prin design, dar
prezente în date. Lista completă în `data/audit_regions.json` (clasa
`uncontracted` / fără OSM match) și în rapoartele de potrivire.
