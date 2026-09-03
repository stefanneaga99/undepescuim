# Phase-1 River Geometry Audit

JSON is authoritative; this Markdown is a human-readable projection.

## Scope and non-goals

Only `subtype == rau` records are selected. Lakes are excluded. This is read-only: no canonical record was fixed, and physical geometry is not contractual/legal-sector geometry. No legal endpoints, ownership, association, or contracts were inferred.

## Source availability and hashes

| Source | Exists | SHA-256 |
|---|---:|---|
| `.local-work/unresolved-class3-6-audit.json` | True | `4e503b8c6b4507c9fd7d8f4252434ab5f5a410160f36947425584b10deb049d5` |
| `.local-work/unresolved-geometry-inventory.json` | True | `10a3a36de5d0201719eba9da42f60a66f05bea737cff338732f064ceeafedaa3` |
| `data/processed/geometry_render_repair_provenance.json` | True | `e0eee331cec48c8c9db3afda68217b66727cc651294a13fd60834dd368ebb0d5` |
| `data/processed/river_segment_audit.json` | True | `9232fbadaa9ee3c80b0718cb9ea49eef61e1cab954c5c25b0eed0d8a2093ef35` |
| `public/data/preview_class2_physical.json` | False | `null` |
| `public/data/waters.json` | True | `56380740bbc6a9f91a49b1f4f57ee8465821e9d144eaa39822e9d19d8caab7c0` |
| `public/data/waters_county_clips.json` | True | `4bf26bb9d352bc112782f5dc2bc9950e5c341ee369493d39b7b84ebe2eda5e92` |

## Selection

Selected **295** river records (cap 312); rejected/non-river/missing joins: **17**.

## Canonical no-mutation

All allowlisted source hashes were identical before/after reads; only the three audit outputs are written.

## First reproduction: anpa-anpa-0211

`anpa-anpa-0211` is `Valea Buzăului inferior` (Buzău), subtype `rau`, with canonical `geometry: null` and `bbox: null`. Therefore no line can be withheld by viewport culling; this is an absent-geometry baseline. Browser rendering/culling was not asserted or reproduced.

## Classification counts

| Classification | Count |
|---|---:|
| RENDERING_FIX | 4 |
| SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | 161 |
| CONTRACT_ENDPOINT_MISSING | 12 |
| SAME_NAME_REVIEW | 10 |
| NO_SAFE_GEOMETRY | 108 |
| NOT_REPRODUCED | 0 |

## Record audit

| Slug | Name | County | Classification | Geometry | County clip | Reproduction |
|---|---|---|---|---|---|---|
| `0a4d89le` | Râul Prahova mijlocie  | Prahova | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `0djgr9l8` | Râul Argeșel Superior | Argeș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `0dsbiw28` | Râul Holod | Bihor | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `1f162p36` | Pârâul Râul Vadului | Sibiu | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `1zqkhha4` | Topa – Holod | Bihor | SAME_NAME_REVIEW | present | absent | NOT_REPRODUCED |
| `2dxykcpr` | Râul Târgului mijlociu | Argeș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `2g9hg98a` | Râul Prahova superioară | Prahova | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `2tehod7w` | Râul Dâmbovița Superioară | Argeș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `3e8t20hn` | Râul Olt | Vâlcea | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `3gl3r1sa` | Râul Olt | Brașov | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `44plkztf` | Râul Teleajen inferior | Prahova | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `7jpc32e8` | Valea Omului | Bihor | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `7oju77qb` | Râul Bistrița | Bistrița-Năsăud | SAME_NAME_REVIEW | present | absent | NOT_REPRODUCED |
| `7ull4jnk` | Râul Crișul Negru mijlociu | Bihor | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `8rd9jm0l` | Râul Sohodol II  | Gorj | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `9h06oubr` | Râul Arieș | Cluj | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `9y116j3m` | Someșu Rece Mijlociu | Cluj | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `a2qs9hkg` | Râul Someșul Mare inferior | Bistrița-Năsăud | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | absent | NOT_REPRODUCED |
| `ab4t7anb` | Râul Tărcăița | Bihor | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `aksrc2lo` | Râul Grotului  | Vâlcea | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0011` | Râul Sălciuța | Alba | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0015` | Valea Bistricioarei | Alba | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0018` | Valea Morilor | Alba | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0019` | Râul Vălișoara | Alba | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0023` | Canalele din zona Turnu | Arad | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0026` | Canalele hidroameliorative Socodor | Arad | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0040` | Râul Ierul | Arad | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0056` | Râul Dâmbovița mijlocie | Argeș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0066` | Râul Siret | Bacău | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0091` | Canalul colector | Bihor | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0094` | Canalul Cefa III | Bihor | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0097` | Canalul Tăut – Barmod | Bihor | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0098` | Văratic | Bihor | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0125` | Râul Sălăuța Superioară | Bistrița-Năsăud | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0131` | Pârâul Iliuța | Bistrița-Năsăud | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0134` | Râul Colibița superioară | Bistrița-Năsăud | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0135` | Râul Colibița inferioară | Bistrița-Năsăud | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0152` | Râul Ghireni | Botoșani | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0154` | Râul Corogea | Botoșani | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0156` | Râul Podul Plopii | Botoșani | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0157` | Râul Ursoiu | Botoșani | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0158` | Pietroaia | Botoșani | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0159` | Râul Sărata | Botoșani | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0160` | Râul Bodeasa | Botoșani | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0161` | Râul Balinți | Botoșani | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0162` | Râul Podriga | Botoșani | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0168` | Bajura | Botoșani | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0184` | Râul Șercaia inferioară | Brașov | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0185` | Valea Șercaia | Brașov | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0192` | Râul Olt și afluenții săi | Brașov | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0206` | Valea Encii | Brăila | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0207` | Râul Buzăul superior cu afluenții săi | Buzău | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0210` | Valea Buzăului superior | Buzău | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0211` | Valea Buzăului inferior | Buzău | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0212` | Pârâul Valea Sibiciului | Buzău | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0213` | Râul Călmățui cu afluenții săi | Buzău | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0214` | Râul Buzăul inferior | Buzău | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0215` | Râul Râmnicu Sărat | Buzău | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0220` | Râul Bârzava inferioară | Caraș-Severin | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0221` | Râul Timișul inferior | Caraș-Severin | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0228` | Canalul Siderurgic | Călărași | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0229` | Rețeaua de canale de irigații cu excepția canalelor        Rasa și Gălățui | Călărași | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0230` | Râul Argeș | Călărași | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0231` | Canal irigații Jirlău | Călărași | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0236` | Canalul Milotina | Călărași | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0248` | Canal Poarta Albă – Midia Năvodari | Constanța | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0249` | Canal apă caldă Cernavodă | Constanța | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0250` | Râul Olt | Covasna | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0252` | Brațele secundare ale Râului Negru | Covasna | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0253` | Pârâu Szaldoboș | Covasna | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0254` | Pârâu Șomko | Covasna | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0261` | Pârâu Buzăul Mijlociu | Covasna | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0264` | Râul Negru I | Covasna | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0278` | Canal Săpata | Dolj | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0279` | Canalul Ianoși | Dolj | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0280` | Râul Jiu și afluenții săi | Dolj | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0293` | Canalul Dăbuleni CO | Dolj | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0295` | Canalul CET Ișalnița – apă caldă | Dolj | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0296` | Râul Siret | Galați | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0297` | Râul Prut | Galați | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0298` | Râul Argeș | Giurgiu | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0302` | Râul Șaica | Giurgiu | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0310` | Râul Jaleș | Gorj | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0323` | Râul Mureș II | Harghita | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0326` | Târnava Mare | Harghita | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0329` | Râul Ivo | Harghita | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0331` | Râul Iuhodul Praidului | Harghita | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0332` | Râul Târnava Mare superior | Harghita | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0333` | Râul Târnava Mare mijlocie | Harghita | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0334` | Râul Târnava Mare inferior | Harghita | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0337` | Râul Mureș I | Harghita | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0339` | Râul Oltul superior | Harghita | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0341` | Râul Uzul superior | Harghita | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0354` | Valea Corbului | Harghita | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0370` | Râul Steiul montan mijlociu | Hunedoara | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0373` | Bulzești | Hunedoara | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0377` | Râul Mureș, cu afluenții | Hunedoara | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0378` | Râul Strei, cu afluenții | Hunedoara | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0379` | Râul Crișul Alb, cu afluenții | Hunedoara | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0387` | Canalul Saltava | Ialomița | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0388` | Raul Ialomița | Ialomița | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0389` | Râul Prut | Iași | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0390` | Râul Siret | Iași | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0392` | Râul Jijia curs principal | Iași | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0393` | Brațul Închis(mort) al râului Jijia | Iași | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0400` | Râul Sălăjel | Maramureș | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0402` | Râul Someș | Maramureș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0407` | Izvorul Izei | Maramureș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0408` | Râul Iza superioară | Maramureș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0413` | Râul Craica | Maramureș | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0415` | Râul Groșii Dămăcușeni, cu afluenții | Maramureș | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0416` | Râul Ruoaia Lăpuș | Maramureș | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0417` | Râul Băiuț | Maramureș | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0418` | Râul Strâmbu Băiuț | Maramureș | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0422` | Valea Rotundă | Maramureș | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0423` | Valea Rohia | Maramureș | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0425` | Valea Dobric | Maramureș | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0426` | Râul Mureș | Mureș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0435` | Pârâul Hodoș-Patec | Mureș | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0437` | Pârâul Solocma | Mureș | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0440` | Pârâul Vețca | Mureș | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0453` | Râul Mureș IV | Mureș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0454` | Râul Târnava Mare | Mureș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0455` | Râul Bistrița VI | Neamț | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0463` | Râul Bistrița V | Neamț | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0469` | Râul Siret | Neamț | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0496` | Râul Someș | Satu Mare | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0504` | Râul Tur superior | Satu Mare | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0505` | Râul Tur mijlociu | Satu Mare | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0508` | Sonia | Sălaj | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0512` | Valea Sălajului | Sălaj | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0519` | Râul Olt | Sibiu | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0521` | Râul Târnava Mare | Sibiu | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0530` | Valea Stegii | Sibiu | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0552` | Râul Siret | Suceava | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0555` | Râul Șomuzul Mic și afluenții | Suceava | CONTRACT_ENDPOINT_MISSING | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0562` | Râul Bistrița Aurie III | Suceava | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0563` | Râul Bistrița I Zugreni | Suceava | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0565` | Râul Moldova III | Suceava | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0566` | Râul Moldova I | Suceava | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0567` | Râul Moldova II | Suceava | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0568` | Râul Moldova IV | Suceava | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0569` | Râul Bistrița II | Suceava | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0570` | Râul Bistrița Aurie I | Suceava | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0574` | Izvoarele Moldovei și Sucevei | Suceava | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0581` | Râul Olt | Teleorman | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0584` | Râul Mureș | Timiș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0585` | Râul Bârzava | Timiș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0609` | Pârâul Cernabora | Timiș | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0611` | Pârâul Cherestau | Timiș | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0612` | Pârâul Iarcoș | Timiș | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0614` | Pârâul Voiteg | Timiș | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0615` | Pârâul Birdanca | Timiș | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0622` | Râul Prut și revărsări | Vaslui | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0623` | Râul Racova | Vaslui | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0627` | Pârâu Elan | Vaslui | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0669` | Râul „Izvor” | Vâlcea | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0671` | Râul Sturișori | Vâlcea | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-anpa-0674` | Râul Siret | Vrancea | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0677` | Râul Zăbala inferioara | Vrancea | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-anpa-0680` | Râul Zăbăluța | Vrancea | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `anpa-bacau-bistrita-39` | Râul Bistrița | Bacău | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-bn-bistrita-28` | Râul Bistrița | Bistrița-Năsăud | SAME_NAME_REVIEW | absent | absent | NOT_REPRODUCED |
| `anpa-bn-somesul-mare-61` | Râul Someșul Mare | Bistrița-Năsăud | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | absent | NOT_REPRODUCED |
| `anpa-harghita-tarnava-mica-5` | Râul Târnava Mică | Harghita | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-mures-tarnava-mica-96` | Râul Târnava Mică | Mureș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-neamt-bistrita-32` | Râul Bistrița | Neamț | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-neamt-moldova-bradul` | Râul Moldova | Neamț | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-neamt-moldova-roman` | Râul Moldova | Neamț | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-romsilva-0239` | Râul Jiu | Gorj | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-salaj-crasna-65` | Râul Crasna | Sălaj | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-salaj-somesul-mare-93` | Râul Someșul Mare | Sălaj | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `anpa-suceava-moldova-59` | Râul Moldova | Suceava | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `basca-mare-covasna` | Râul Bâsca Mare | Covasna | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `bv8qho87` | Crișul Repede Superior | Cluj | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `c1gifahb` | Râul Teleajen inferior - Bucov | Prahova | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `d5xhbhta` | Râul Doamnei Superior | Argeș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `dcomrepi` | Râul Jiul de vest mijlociu | Hunedoara | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `do8k78x0` | Râul Crișul Repede Mijlociu | Bihor | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `dre11dij` | Râul Poiana | Bihor | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `e8r6r01g` | Râul Olteț | Olt | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `ebhj5eyj` | Râul Potop | Dâmbovița | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `eebjo69e` | Râul Volovăț | Botoșani | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `f553avch` | Râul Colentina | Dâmbovița | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `fanvixkg` | Râul Jiul Inferior | Hunedoara | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `fee3lhad` | Râul Valea Morilor | Alba | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `fouqynmq` | Râul Argeș | Argeș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `g39ohi12` | Râul Jilț  | Gorj | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `ggka27ea` | Râul Dâmbovița | Dâmbovița | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `gunskubl` | Valea Gepiș | Bihor | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `gvmaf2tz` | Râul Budacul superior | Bistrița-Năsăud | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | absent | NOT_REPRODUCED |
| `gxjd56ii` | Pârâul Nou Roman | Sibiu | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `hao8h0b2` | Râul Someșul Mic | Cluj | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `hmidzduu` | Valea Robești | Vâlcea | SAME_NAME_REVIEW | absent | materialized | NOT_REPRODUCED |
| `i9uffwbx` | Someșu Rece Superior | Cluj | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `jw9il5yo` | Râul Crișul Negru inferior | Bihor | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `k44320iw` | Râul Târgului superior | Argeș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `msh7jb28` | Valea Șoimului | Bihor | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `n7cuf5cs` | Crișul Repede Mijlociu | Cluj | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `nb7yzcmh` | Valea Buduresei | Bihor | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `p3puv4bx` | Valea Bistrei | Alba | SAME_NAME_REVIEW | absent | absent | NOT_REPRODUCED |
| `pgabr5sd` | Râul Bahna | Botoșani | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `romsilva-alba-ariesul-mare` | Râul Ariesul Mare | Alba | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-alba-ariesul-mare-inferior` | Râul Arieșul Mare Inferior | Alba | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-alba-ariesul-mare-mijlociu` | Râul Arieșul Mare Mijlociu | Alba | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-alba-fenesasa` | Râul Fenesasa | Alba | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `romsilva-alba-sebesul-inferior` | Râul Sebeșul Inferior | Alba | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-alba-sebesul-mijlociu` | Râul Sebesul Mijlociu | Alba | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-alba-valea-galzii` | Valea Gâlzii | Alba | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `romsilva-alba-valea-mare` | Valea Mare | Alba | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-arad-avram-iancu` | Râul Avram Iancu | Arad | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `romsilva-arad-beliu` | Râul Beliu | Arad | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `romsilva-arad-iacobini` | Râul Iacobini | Arad | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `romsilva-arad-moneasa-inferioara` | Râul Moneasa Inferioară | Arad | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-arad-pamesti` | Râul Pămești | Arad | CONTRACT_ENDPOINT_MISSING | absent | absent | NOT_REPRODUCED |
| `romsilva-arad-stejar` | Râul Stejar | Arad | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `romsilva-arad-toc` | Râul Toc | Arad | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `romsilva-arad-zimbru` | Râul Zimbru | Arad | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `romsilva-arges-doamnei-mijlociu` | Râul Doamnei mijlociu | Argeș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-arges-rausor` | Râul Râușor | Argeș | SAME_NAME_REVIEW | present | absent | NOT_REPRODUCED |
| `romsilva-arges-rausor-2` | Râul Râușor | Argeș | SAME_NAME_REVIEW | absent | materialized | NOT_REPRODUCED |
| `romsilva-bacau-barzauta` | Râul Bărzăuța | Bacău | RENDERING_FIX | present | absent | NOT_REPRODUCED |
| `romsilva-bacau-casinul-superior` | Râul Cașinul Superior | Bacău | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-bihor-valea-draganului` | Valea Drăganului | Bihor | CONTRACT_ENDPOINT_MISSING | absent | absent | NOT_REPRODUCED |
| `romsilva-bihor-valea-iadului-inferior` | Valea Iadului Inferior | Bihor | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-bistrita-nasaud-somesul-mare-superior` | Râul Someșul Mare superior | Bistrița-Năsăud | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | absent | NOT_REPRODUCED |
| `romsilva-brasov-buzaul-superior` | Râul Buzăul superior | Brașov | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-caras-severin-barzava-superioara` | Râul Bârzava Superioară | Caraș-Severin | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | absent | NOT_REPRODUCED |
| `romsilva-caras-severin-cerna-inferioara` | Râul Cerna inferioară | Caraș-Severin | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | absent | NOT_REPRODUCED |
| `romsilva-caras-severin-cerna-mijlocie` | Râul Cerna mijlocie | Caraș-Severin | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | absent | NOT_REPRODUCED |
| `romsilva-caras-severin-cernisoara-iardastrita` | Râul Cernișoara (Iardaștrița) | Caraș-Severin | CONTRACT_ENDPOINT_MISSING | absent | absent | NOT_REPRODUCED |
| `romsilva-caras-severin-higeg` | Râul Higeg | Caraș-Severin | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `romsilva-caras-severin-higigel` | Râul Higigel | Caraș-Severin | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `romsilva-caras-severin-izvoarele-timisului` | Râul Izvoarele Timișului | Caraș-Severin | CONTRACT_ENDPOINT_MISSING | absent | absent | NOT_REPRODUCED |
| `romsilva-cluj-2-somesul-cald-mijlociu` | Râul 2 Somesul Cald Mijlociu | Cluj | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-cluj-somesul-rece-mijlociu` | Râul Someșul Rece mijlociu | Cluj | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-cluj-somesul-rece-superior` | Râul Someșul Rece superior | Cluj | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-covasna-barzauta` | Râul Bărzăuța | Covasna | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-covasna-basca-mica` | Râul Bâsca Mică | Covasna | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | absent | NOT_REPRODUCED |
| `romsilva-covasna-sugo` | Râul Șugo | Covasna | RENDERING_FIX | present | absent | NOT_REPRODUCED |
| `romsilva-dambovita-ialomita-superioara` | Râul Ialomița superioară | Dâmbovița | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-dambovita-runcu` | Râul Runcu | Dâmbovița | CONTRACT_ENDPOINT_MISSING | absent | absent | NOT_REPRODUCED |
| `romsilva-gorj-bistricioara` | Râul Bistricioara | Gorj | CONTRACT_ENDPOINT_MISSING | absent | absent | NOT_REPRODUCED |
| `romsilva-gorj-oltet` | Râul Olteț | Gorj | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-gorj-valea-bratcului` | Valea Bratcului | Gorj | CONTRACT_ENDPOINT_MISSING | absent | absent | NOT_REPRODUCED |
| `romsilva-harghita-bicazul-mijlociu` | Râul Bicazul Mijlociu | Harghita | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-harghita-bistricioara-tronson-ii` | Râul Bistricioara tronson II | Harghita | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-hunedoara-gradistea-superioara` | Râul Grădiștea superioară | Hunedoara | CONTRACT_ENDPOINT_MISSING | absent | absent | NOT_REPRODUCED |
| `romsilva-hunedoara-nucsorul-inferior` | Râul Nucşorul Inferior | Hunedoara | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-hunedoara-raul-barbat-inferior` | Râul Râul Bărbat Inferior | Hunedoara | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-maramures-botiza` | Râul Botiza | Maramureș | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `romsilva-maramures-chiuzbaia` | Râul Chiuzbaia | Maramureș | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `romsilva-maramures-crasna-frumusaua` | Râul Crasna (Frumușaua) | Maramureș | RENDERING_FIX | present | absent | NOT_REPRODUCED |
| `romsilva-maramures-faina-wasser` | Râul Făina-Wasser | Maramureș | CONTRACT_ENDPOINT_MISSING | absent | absent | NOT_REPRODUCED |
| `romsilva-maramures-ruscova-inferioara` | Râul Ruscova Inferioară | Maramureș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-maramures-viseul-inferior` | Râul Vișeul inferior | Maramureș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-maramures-viseul-mijlociu` | Râul Vișeul mijlociu | Maramureș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-mehedinti-cerna` | Râul Cerna | Mehedinți | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-mures-gurghiul-mijlociu` | Râul Gurghiul mijlociu | Mureș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-mures-mures-iii` | Râul Mureş III | Mureș | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-neamt-bistrita-iv` | Râul Bistrița IV | Neamț | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-neamt-tarcau` | Râul Tarcău | Neamț | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-salaj-barcaul-inferior` | Râul Barcaul Inferior | Sălaj | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-salaj-barcaul-mijlociu` | Râul Barcăul Mijlociu | Sălaj | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-sibiu-bistra` | Râul Bistra | Sibiu | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `romsilva-sibiu-ciban` | Râul Ciban | Sibiu | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `romsilva-sibiu-sadu-mijlociu` | Râul Sadu Mijlociu | Sibiu | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-sibiu-sadu-superior` | Râul Sadu Superior | Sibiu | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-sibiu-sebesul-superior` | Râul Sebeșul Superior | Sibiu | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-suceava-afluentii-suhei` | Râul Afluenţii Suhei | Suceava | CONTRACT_ENDPOINT_MISSING | absent | absent | NOT_REPRODUCED |
| `romsilva-suceava-barnarel` | Râul Bărnărel | Suceava | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `romsilva-suceava-izvoarele-dornei` | Râul Izvoarele Dornei | Suceava | CONTRACT_ENDPOINT_MISSING | absent | absent | NOT_REPRODUCED |
| `romsilva-suceava-neagra-inferioara` | Râul Neagra Inferioară | Suceava | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-valcea-izvoarele-latoritei` | Râul Izvoarele Latoriței | Vâlcea | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `romsilva-valcea-izvorul-lotrului` | Râul Izvorul Lotrului | Vâlcea | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-valcea-latorita-inferioara` | Râul Latorița Inferioară | Vâlcea | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-valcea-lotru-superior` | Râul Lotru Superior | Vâlcea | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-vrancea-coza` | Râul Coza | Vrancea | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `romsilva-vrancea-putna-mijlocie` | Râul Putna Mijlocie | Vrancea | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-vrancea-putna-superioara` | Râul Putna Superioara | Vrancea | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `romsilva-vrancea-zabala-superioara` | Râul Zăbala Superioară | Vrancea | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `sopv2vba` | Râul Siret | Botoșani | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `teziodii` | Râul Lotrul Inferior | Vâlcea | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `tozghzao` | Râul Râmești | Vâlcea | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `u84uqnip` | Râul Crișul Repede inferior | Bihor | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `vb2p0152` | Râul Geamărtălui  | Olt | RENDERING_FIX | present | absent | NOT_REPRODUCED |
| `w69nse7i` | Râul Crișul Negru | Bihor | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `w9ifusdl` | Râul Vorona | Botoșani | NO_SAFE_GEOMETRY | absent | absent | NOT_REPRODUCED |
| `y6i6nikh` | Râul Olt | Olt | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `yfzdgchv` | Râul Teleajenul inferior | Prahova | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `ys4a4vw8` | Valea Bistrei | Alba | SAME_NAME_REVIEW | absent | absent | NOT_REPRODUCED |
| `yu63lkif` | Râul Mureș | Alba | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `z8u6g69z` | Râul Geoagiu Superior | Alba | SOURCE_BACKED_PHYSICAL_PREVIEW_ONLY | absent | materialized | NOT_REPRODUCED |
| `zdjui15p` | Topa - Holod | Bihor | SAME_NAME_REVIEW | present | absent | NOT_REPRODUCED |
| `zryn07zh` | Valea Robești | Vâlcea | SAME_NAME_REVIEW | present | absent | NOT_REPRODUCED |

## Preview/legal separation

Missing preview input is recorded as unavailable. Physical preview candidates, where present in prior evidence, are never promoted to canonical geometry or legal sectors. Contract text and course fractions remain diagnostic only.

## Batch eligibility

`confirmedExecutionBatches: []`. No candidate has a two-pass reproducible rendering root cause and reviewer acceptance; no implementation batches were created.

No claims of fixed records are made.
