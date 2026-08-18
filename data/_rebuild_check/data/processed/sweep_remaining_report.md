# Geometry sweep report (t_68dabead)

Sweep of the remaining 32 bbox-only rectangles + 147 waters with no
geometry/bbox (no group owner). 159 group-shared waters render via their
group owner's course by design (one-owner-per-group).

**Update (run 127):** a fuzzy re-scan of the 22 documented-unmatchable
bbox-only waters + the 74 bbox-added waters found 2 real misses fixed in
`scripts/fix_missed_unmatchables.py`:
- Pârâul Murgoci (`ii25s9zo`, Vâlcea) ← OSM 'Valea Murgaciu' (15 pts, inside
  bbox, ends at the Uria confluence the limits name; sister contract
  anpa-0644 names the Murgoci).
- Valea Curpenului (`anpa-anpa-0631`, Vâlcea) ← OSM 'Curpănu' (289 pts,
  contains bbox; village Curpănu Câineni sits on the course; Wikipedia Olt
  tributary list matches 'Afluent Râul Olt').
Remaining 20 documented-unmatchable bbox-only waters re-verified against the
local OSM cluster index + raw ways: no named or unnamed in-county course
exists for them (Bihor small valleys: relation children without waterway
tags; Jilț: only the Jiu cluster, wrong river; Grotului: 'Valea Satului' is
an adjacent different stream, name sim 0.58; Volovăț/Bistrei: foreign
Nistru/Vilia clusters only).

## PART 1 — 32 bbox-only: 11 fixed, 21 documented keep-bbox

### Fixed (11)

- Râul Geoagiu Superior (`z8u6g69z`) — Alba: bbox dropped (renders via group owner) 
- Lac Pâncota (`u74mudgv`) — Arad: matched (unnamed OSM polygon near locality) ← unnamed-water
- Lac Zădăreni (`v568f04x`) — Arad: matched (unnamed OSM polygon near locality) ← unnamed-
- Râul Doamnei Superior (`d5xhbhta`) — Argeș: bbox dropped (renders via group owner) 
- Valea Ierului (`0b5imfgi`) — Bihor: matched (real geometry) ← Ier
- Lac Reconstrucția (`mmakw97b`) — Neamț: matched (unnamed OSM polygon near locality) ← unnamed-water
- Lacul de acumulare Lățunaș (`315lt84w`) — Timiș: matched (unnamed OSM polygon near locality) ← unnamed-wetland
- Lacul Vlădești  (`0tzvnk1y`) — Vâlcea: matched (unnamed OSM polygon near locality) ← unnamed-water
- Râul Izvorul Lotrului (`romsilva-valcea-izvorul-lotrului`) — Vâlcea: bbox dropped (renders via group owner) 
- Râul Lotrul Inferior (`teziodii`) — Vâlcea: bbox dropped (renders via group owner) 
- Pârâul Murgoci (`ii25s9zo`) — Vâlcea: matched (OSM 'Valea Murgaciu', run 127) ← manual-miss-fix

### Kept bbox fallback — documented unmatchable (21)

- Râul Valea Morilor (`fee3lhad`) — Alba: kept bbox fallback (documented unmatchable) 
- Valea Bistrei (`ys4a4vw8`) — Alba: kept bbox fallback (documented unmatchable) 
- Valea Bistrei (`p3puv4bx`) — Alba: kept bbox fallback (documented unmatchable) 
- Râul Holod (`0dsbiw28`) — Bihor: kept bbox fallback (documented unmatchable) 
- Râul Poiana (`dre11dij`) — Bihor: kept bbox fallback (documented unmatchable) 
- Râul Tărcăița (`ab4t7anb`) — Bihor: kept bbox fallback (documented unmatchable) 
- Valea Buduresei (`nb7yzcmh`) — Bihor: kept bbox fallback (documented unmatchable) 
- Valea Gepiș (`gunskubl`) — Bihor: kept bbox fallback (documented unmatchable) 
- Valea Omului (`7jpc32e8`) — Bihor: kept bbox fallback (documented unmatchable) 
- Valea Șoimului (`msh7jb28`) — Bihor: kept bbox fallback (documented unmatchable) 
- Lacul Izvorul (Măgurii) (`7yg1hoia`) — Bistrița-Năsăud: kept bbox fallback (documented unmatchable) 
- Râul Bahna (`pgabr5sd`) — Botoșani: kept bbox fallback (documented unmatchable) 
- Râul Volovăț (`eebjo69e`) — Botoșani: kept bbox fallback (documented unmatchable) 
- Râul Vorona (`w9ifusdl`) — Botoșani: kept bbox fallback (documented unmatchable) 
- Râul Potop (`ebhj5eyj`) — Dâmbovița: kept bbox fallback (documented unmatchable) 
- Râul Jilț  (`g39ohi12`) — Gorj: kept bbox fallback (documented unmatchable) 
- Pârâul Nou Roman (`gxjd56ii`) — Sibiu: kept bbox fallback (documented unmatchable) 
- Pârâul Râul Vadului (`1f162p36`) — Sibiu: kept bbox fallback (documented unmatchable) 
- Lacul Pojorâta (Iezer) (`4fg24m45`) — Suceava: kept bbox fallback (documented unmatchable) 
- Râul Grotului  (`aksrc2lo`) — Vâlcea: kept bbox fallback (documented unmatchable) 
- Râul Râmești (`tozghzao`) — Vâlcea: kept bbox fallback (documented unmatchable) 

## PART 2 — 147 truly-invisible: 38 matched, 73 bbox-added, 35 hidden, 4 other

### Matched (38)

- Râul Izvoarele Ampoiului (`romsilva-alba-izvoarele-ampoiului`) — Alba: matched (real geometry) ← Izvoarele
- Lac Mortărel (`anpa-anpa-0034`) — Arad: matched (unnamed OSM polygon near locality) ← unnamed-
- Cumpana Mare (`romsilva-arges-cumpana-mare`) — Argeș: matched (unnamed OSM polygon near locality) ← unnamed-water
- Lacul Izvorul(Măgurii) (`anpa-anpa-0120`) — Bistrița-Năsăud: matched (unnamed OSM polygon near locality) ← unnamed-wetland
- Valea Mare – Crizbav (`anpa-anpa-0179`) — Brașov: matched (real geometry) ← Pârâul Mare
- Valea Mare (`anpa-anpa-0227`) — Caraș-Severin: matched (real geometry) ← Valea Mare
- 8 Lacul Valea Calului (`romsilva-cluj-8-lacul-valea-calului`) — Cluj: matched (unnamed OSM polygon near locality) ← unnamed-water
- Lac Săcălaia (`anpa-anpa-0246`) — Cluj: matched (unnamed OSM polygon near locality) ← unnamed-wetland
- Lacul Floroiu (`romsilva-cluj-lacul-floroiu`) — Cluj: matched (unnamed OSM polygon near locality) ← unnamed-water
- Balta Valea Mare (`anpa-anpa-0233`) — Călărași: matched (unnamed OSM polygon near locality) ← unnamed-wetland
- Balta ecluza Oltenița (`anpa-anpa-0234`) — Călărași: matched (unnamed OSM polygon near locality) ← unnamed-
- Canalul Scoiceni (`anpa-anpa-0235`) — Călărași: matched (unnamed OSM ways near locality) ← unnamed-way(s)
- Balta Geormane (`anpa-anpa-0285`) — Dolj: matched (unnamed OSM polygon near locality) ← unnamed-wetland
- Balta Marica (`anpa-anpa-0286`) — Dolj: matched (unnamed OSM polygon near locality) ← unnamed-water
- Baraj Ișalnița (`anpa-anpa-0289`) — Dolj: matched (unnamed OSM polygon near locality) ← unnamed-water
- Râul Șușița Verde (`anpa-anpa-0304`) — Gorj: matched (real geometry) ← Șușița
- Lac baraj pârâul Roșu (`romsilva-harghita-lac-baraj-paraul-rosu`) — Harghita: matched (unnamed OSM polygon near locality) ← unnamed-water
- Lac Hațeg (`anpa-anpa-0365`) — Hunedoara: matched (unnamed OSM polygon near locality) ← unnamed-water
- Lac Ostrov (`anpa-anpa-0363`) — Hunedoara: matched (unnamed OSM polygon near locality) ← unnamed-water
- Râul Mare inf. II (`anpa-anpa-0356`) — Hunedoara: matched (real geometry) ← Valea Mare
- Râul Steiul montan inferior (`anpa-anpa-0355`) — Hunedoara: matched (unnamed OSM ways near locality) ← unnamed-way(s)
- Borjuc (`romsilva-maramures-borjuc`) — Maramureș: matched (unnamed OSM polygon near locality) ← unnamed-water
- Râul Chechiș (`anpa-anpa-0399`) — Maramureș: matched (real geometry) ← Chechișel
- Râul Minghet (`anpa-anpa-0420`) — Maramureș: matched (unnamed OSM ways near locality) ← unnamed-way(s)
- CCPFB Paulian (`anpa-anpa-0498`) — Satu Mare: matched (unnamed OSM polygon near locality) ← unnamed-water
- CCRM Ruseni (`anpa-anpa-0497`) — Satu Mare: matched (unnamed OSM polygon near locality) ← unnamed-water
- Pârâul Valea Strâmbei (`anpa-anpa-0539`) — Sibiu: matched (real geometry) ← Pârâul Vale
- Balta Rădășeni (`anpa-anpa-0560`) — Suceava: matched (unnamed OSM polygon near locality) ← unnamed-water
- Râul Brodina (`romsilva-suceava-brodina`) — Suceava: matched (unnamed OSM ways near locality) ← unnamed-way(s)
- Valea Putnei (`romsilva-suceava-valea-putnei`) — Suceava: matched (unnamed OSM ways near locality) ← unnamed-way(s)
- Năpradea– braț mort Someșul Mare (`anpa-anpa-0515`) — Sălaj: matched (unnamed OSM ways near locality) ← unnamed-way(s)
- Valea Barcăului (`anpa-anpa-0514`) — Sălaj: matched (real geometry) ← Barcău
- Pârâul Ier (`anpa-anpa-0606`) — Timiș: matched (real geometry) ← Iercicu
- Doaga (`anpa-anpa-0675`) — Vrancea: matched (unnamed OSM polygon near locality) ← unnamed-wetland
- Acumularea Drăgășani cu bălțile adiacente (`anpa-anpa-0649`) — Vâlcea: matched (unnamed OSM polygon near locality) ← unnamed-water
- Acumularea Ionești cu bălțile adiacente (`anpa-anpa-0648`) — Vâlcea: matched (unnamed OSM polygon near locality) ← unnamed-
- Acumularea Robești si Valea Robești (`anpa-anpa-0638`) — Vâlcea: matched (real geometry) ← Robești
- Valea Curpenului (`anpa-anpa-0631`) — Vâlcea: matched (OSM 'Curpănu', run 127) ← manual-miss-fix

### Bbox added — renders as marker (73)

- Mihoești (`anpa-anpa-0008`) — Alba: bbox added (renders) 
- Râul Vîltori - Feneș (`romsilva-alba-viltori-fenes`) — Alba: bbox added (renders) 
- Valea Gâlzii (`romsilva-alba-valea-galzii`) — Alba: bbox added (renders) 
- Râul Avram Iancu (`romsilva-arad-avram-iancu`) — Arad: bbox added (renders) 
- Râul Beliu (`romsilva-arad-beliu`) — Arad: bbox added (renders) 
- Râul Iacobini (`romsilva-arad-iacobini`) — Arad: bbox added (renders) 
- Râul Stejar (`romsilva-arad-stejar`) — Arad: bbox added (renders) 
- Râul Toc (`romsilva-arad-toc`) — Arad: bbox added (renders) 
- Râul Zimbru (`romsilva-arad-zimbru`) — Arad: bbox added (renders) 
- Canalul Cefa III (`anpa-anpa-0094`) — Bihor: bbox added (renders) 
- Canalul Tăut – Barmod (`anpa-anpa-0097`) — Bihor: bbox added (renders) 
- Canalul colector (`anpa-anpa-0091`) — Bihor: bbox added (renders) 
- Văratic (`anpa-anpa-0098`) — Bihor: bbox added (renders) 
- Pârâul Iliuța (`anpa-anpa-0131`) — Bistrița-Năsăud: bbox added (renders) 
- Bajura (`anpa-anpa-0168`) — Botoșani: bbox added (renders) 
- Pietroaia (`anpa-anpa-0158`) — Botoșani: bbox added (renders) 
- Râul Balinți (`anpa-anpa-0161`) — Botoșani: bbox added (renders) 
- Râul Bodeasa (`anpa-anpa-0160`) — Botoșani: bbox added (renders) 
- Râul Corogea (`anpa-anpa-0154`) — Botoșani: bbox added (renders) 
- Râul Ghireni (`anpa-anpa-0152`) — Botoșani: bbox added (renders) 
- Râul Podriga (`anpa-anpa-0162`) — Botoșani: bbox added (renders) 
- Râul Podul Plopii (`anpa-anpa-0156`) — Botoșani: bbox added (renders) 
- Râul Sărata (`anpa-anpa-0159`) — Botoșani: bbox added (renders) 
- Râul Ursoiu (`anpa-anpa-0157`) — Botoșani: bbox added (renders) 
- Râul Șercaia inferioară (`anpa-anpa-0184`) — Brașov: bbox added (renders) 
- Valea Pojorâtei (`anpa-anpa-0188`) — Brașov: bbox added (renders) 
- Valea Șercaia (`anpa-anpa-0185`) — Brașov: bbox added (renders) 
- Pârâul Valea Sibiciului (`anpa-anpa-0212`) — Buzău: bbox added (renders) 
- Râul Higeg (`romsilva-caras-severin-higeg`) — Caraș-Severin: bbox added (renders) 
- Râul Higigel (`romsilva-caras-severin-higigel`) — Caraș-Severin: bbox added (renders) 
- Canal Poarta Albă – Midia Năvodari (`anpa-anpa-0248`) — Constanța: bbox added (renders) 
- Brațele secundare ale Râului Negru (`anpa-anpa-0252`) — Covasna: bbox added (renders) 
- Pârâu Szaldoboș (`anpa-anpa-0253`) — Covasna: bbox added (renders) 
- Pârâu Șomko (`anpa-anpa-0254`) — Covasna: bbox added (renders) 
- Canal Săpata (`anpa-anpa-0278`) — Dolj: bbox added (renders) 
- Canalul CET Ișalnița – apă caldă (`anpa-anpa-0295`) — Dolj: bbox added (renders) 
- Canalul Dăbuleni CO (`anpa-anpa-0293`) — Dolj: bbox added (renders) 
- Canalul Ianoși (`anpa-anpa-0279`) — Dolj: bbox added (renders) 
- Râul Șaica (`anpa-anpa-0302`) — Giurgiu: bbox added (renders) 
- Râul Jaleș (`anpa-anpa-0310`) — Gorj: bbox added (renders) 
- Fondul piscicol 24 Ciceu: include Pârâul Tekero – 5 km, Pârâul Ferii – 6 km, Pârâul Cetății – 9 km, Pârâul Fierăstrăului- 9 km, Pârâul Stâncii - 8 km (`anpa-anpa-0344`) — Harghita: bbox added (renders) 
- Râul Ivo (`anpa-anpa-0329`) — Harghita: bbox added (renders) 
- Valea Corbului (`anpa-anpa-0354`) — Harghita: bbox added (renders) 
- Bulzești (`anpa-anpa-0373`) — Hunedoara: bbox added (renders) 
- Brațul Închis(mort) al râului Jijia (`anpa-anpa-0393`) — Iași: bbox added (renders) 
- Râul Botiza (`romsilva-maramures-botiza`) — Maramureș: bbox added (renders) 
- Râul Băiuț (`anpa-anpa-0417`) — Maramureș: bbox added (renders) 
- Râul Chiuzbaia (`romsilva-maramures-chiuzbaia`) — Maramureș: bbox added (renders) 
- Râul Craica (`anpa-anpa-0413`) — Maramureș: bbox added (renders) 
- Râul Ruoaia Lăpuș (`anpa-anpa-0416`) — Maramureș: bbox added (renders) 
- Râul Sălăjel (`anpa-anpa-0400`) — Maramureș: bbox added (renders) 
- Valea Dobric (`anpa-anpa-0425`) — Maramureș: bbox added (renders) 
- Valea Rohia (`anpa-anpa-0423`) — Maramureș: bbox added (renders) 
- Valea Rotundă (`anpa-anpa-0422`) — Maramureș: bbox added (renders) 
- Glăjărie (`anpa-anpa-0443`) — Mureș: bbox added (renders) 
- Pârâul Solocma (`anpa-anpa-0437`) — Mureș: bbox added (renders) 
- Pârâul Vețca (`anpa-anpa-0440`) — Mureș: bbox added (renders) 
- Râul Bistra (`romsilva-sibiu-bistra`) — Sibiu: bbox added (renders) 
- Râul Ciban (`romsilva-sibiu-ciban`) — Sibiu: bbox added (renders) 
- Râul Bărnărel (`romsilva-suceava-barnarel`) — Suceava: bbox added (renders) 
- Sonia (`anpa-anpa-0508`) — Sălaj: bbox added (renders) 
- Valea Sălajului (`anpa-anpa-0512`) — Sălaj: bbox added (renders) 
- Pârâul Birdanca (`anpa-anpa-0615`) — Timiș: bbox added (renders) 
- Pârâul Cernabora (`anpa-anpa-0609`) — Timiș: bbox added (renders) 
- Pârâul Cherestau (`anpa-anpa-0611`) — Timiș: bbox added (renders) 
- Pârâul Iarcoș (`anpa-anpa-0612`) — Timiș: bbox added (renders) 
- Pârâul Voiteg (`anpa-anpa-0614`) — Timiș: bbox added (renders) 
- Pârâu Elan (`anpa-anpa-0627`) — Vaslui: bbox added (renders) 
- Râul Coza (`romsilva-vrancea-coza`) — Vrancea: bbox added (renders) 
- Râul Zăbăluța (`anpa-anpa-0680`) — Vrancea: bbox added (renders) 
- Râul Izvoarele Latoriței (`romsilva-valcea-izvoarele-latoritei`) — Vâlcea: bbox added (renders) 
- Râul Sturișori (`anpa-anpa-0671`) — Vâlcea: bbox added (renders) 
- Râul „Izvor” (`anpa-anpa-0669`) — Vâlcea: bbox added (renders) 

### Hidden — documented unmatchable (35)

- Râul Fenesasa (`romsilva-alba-fenesasa`) — Alba: kept hidden (documented unmatchable) 
- Râul Sălciuța (`anpa-anpa-0011`) — Alba: kept hidden (documented unmatchable) 
- Valea Bistricioarei (`anpa-anpa-0015`) — Alba: kept hidden (documented unmatchable) 
- Balta Ghilin I și II (`anpa-anpa-0024`) — Arad: kept hidden (documented unmatchable) 
- Canalele din zona Turnu (`anpa-anpa-0023`) — Arad: kept hidden (documented unmatchable) 
- Canalele hidroameliorative Socodor (`anpa-anpa-0026`) — Arad: kept hidden (documented unmatchable) 
- Râul Pămești (`romsilva-arad-pamesti`) — Arad: kept hidden (documented unmatchable) 
- Râul Colibița inferioară (`anpa-anpa-0135`) — Bistrița-Năsăud: kept hidden (documented unmatchable) 
- Râul Colibița superioară (`anpa-anpa-0134`) — Bistrița-Năsăud: kept hidden (documented unmatchable) 
- Japșa Corotisca (`anpa-anpa-0203`) — Brăila: kept hidden (documented unmatchable) 
- Japșa Poala Albă (`anpa-anpa-0205`) — Brăila: kept hidden (documented unmatchable) 
- Valea Encii (`anpa-anpa-0206`) — Brăila: kept hidden (documented unmatchable) 
- Râul Izvoarele Timișului (`romsilva-caras-severin-izvoarele-timisului`) — Caraș-Severin: kept hidden (documented unmatchable) 
- Canal apă caldă Cernavodă (`anpa-anpa-0249`) — Constanța: kept hidden (documented unmatchable) 
- Canal irigații Jirlău (`anpa-anpa-0231`) — Călărași: kept hidden (documented unmatchable) 
- Canalul Milotina (`anpa-anpa-0236`) — Călărași: kept hidden (documented unmatchable) 
- Canalul Siderurgic (`anpa-anpa-0228`) — Călărași: kept hidden (documented unmatchable) 
- Rețeaua de canale de irigații cu excepția canalelor        Rasa și Gălățui (`anpa-anpa-0229`) — Călărași: kept hidden (documented unmatchable) 
- Gârla Mălăieni (`anpa-anpa-0287`) — Dolj: kept hidden (documented unmatchable) 
- Valea Bratcului (`romsilva-gorj-valea-bratcului`) — Gorj: kept hidden (documented unmatchable) 
- Râul Grădiștea superioară (`romsilva-hunedoara-gradistea-superioara`) — Hunedoara: kept hidden (documented unmatchable) 
- Râul Steiul montan mijlociu (`anpa-anpa-0370`) — Hunedoara: kept hidden (documented unmatchable) 
- Canalul Saltava (`anpa-anpa-0387`) — Ialomița: kept hidden (documented unmatchable) 
- Potcoava Bordușani (`anpa-anpa-0386`) — Ialomița: kept hidden (documented unmatchable) 
- Râul Făina-Wasser (`romsilva-maramures-faina-wasser`) — Maramureș: kept hidden (documented unmatchable) 
- Râul Groșii Dămăcușeni, cu afluenții (`anpa-anpa-0415`) — Maramureș: kept hidden (documented unmatchable) 
- Pârâul Hodoș-Patec (`anpa-anpa-0435`) — Mureș: kept hidden (documented unmatchable) 
- Lac Reconstrucția (1) (`anpa-anpa-0464`) — Neamț: kept hidden (documented unmatchable) 
- CP 9 stația mică (`anpa-anpa-0499`) — Satu Mare: kept hidden (documented unmatchable) 
- Valea Stegii (`anpa-anpa-0530`) — Sibiu: kept hidden (documented unmatchable) 
- Acumulare Dragomira (`anpa-anpa-0559`) — Suceava: kept hidden (documented unmatchable) 
- Izvoarele Moldovei și Sucevei (`anpa-anpa-0574`) — Suceava: kept hidden (documented unmatchable) 
- Râul Afluenţii Suhei (`romsilva-suceava-afluentii-suhei`) — Suceava: kept hidden (documented unmatchable) 
- Râul Izvoarele Dornei (`romsilva-suceava-izvoarele-dornei`) — Suceava: kept hidden (documented unmatchable) 
- Râul Șomuzul Mic și afluenții (`anpa-anpa-0555`) — Suceava: kept hidden (documented unmatchable) 

### Other (4)

- Râul Fenesasa (`romsilva-alba-fenesasa`) — Alba: kept hidden (wrong-feature-class guard) 
- Valea Drăganului (`romsilva-bihor-valea-draganului`) — Bihor: skipped full attach (sector-only contract) 
- Râul Colibița inferioară (`anpa-anpa-0135`) — Bistrița-Năsăud: kept hidden (wrong-feature-class guard) 
- Râul Colibița superioară (`anpa-anpa-0134`) — Bistrița-Năsăud: kept hidden (wrong-feature-class guard) 

## Final state

- waters: 1013, with geometry: 720, with bbox: 598, neither: 196
- bbox-only rectangles: 97 (was 32 at task start; 74 of the Part-2 bbox-added
  waters render as small markers instead of being invisible, 21 Part-1
  documented keep-bbox + 2 Pojorâta/Fenesasa anchors)

## Verification

- validate_geometry_county.py: 0 flags (wrong-county/outside-romania)
- _verify_county_clip.py: ALL CHECKS PASSED
- npm run build: OK

Known caveats:
- Râul Fenesasa (Alba), Colibița superioară/inferioară (Bistrița-Năsăud),
  Lacul Pojorâta (Suceava): kept hidden with a village-anchor bbox because
  OSM has no credible same-name course (only wrong-county Feneș clusters /
  the Colibița lake polygon / a Pojorâta river cluster that is not the lake).
- Bihor small valleys (Holod, Tărcăița, Buduresei, Gepiș, Omului, Șoimului,
  Poiana) kept bbox: the OSM extract has no named course for them and the
  unnamed ways in their bboxes are relation children without waterway tags.
