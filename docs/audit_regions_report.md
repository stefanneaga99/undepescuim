# Audit pe zone — râuri OSM vs. date contractate

Total grupuri de râuri OSM cu nume: **7699**  
Clasificare globală:
- **uncontracted**: 6755
- **present**: 936
- **present-hidden**: 6
- **present-bbox**: 1
- **anpa-missing**: 1

## Zona raportată: Covasna / Târgu Secuiesc (DN11, DN13E)

Toate cele 16 ape contractate AJVPS COVASNA există în waters.json. După audit:
- **Pârâu Cașin, Ghelința, Pădureni, Vârghiș, Baraolt inferior** — erau `subtype=lac` și fără geometrie → invizibile; acum `rau` + curs OSM complet (fixate).
- **Râul Negru I / Râul Olt / Pârâu Buzăul Mijlociu** — nu au geometrie proprie, dar sunt grup-rendered: cursul e desenat de partenerul de grup (Râul Negru II / Râul Olt și afluenții / Râul Buzău) → click funcționează.
- **Pârâu Szaldoboș / Pârâu Șomko / Brațele secundare ale Râului Negru** — contractate dar fără curs OSM identificabil (pâraie mici / brațe secundare) → raportate doar, nu se inventează geometrie.
- Râurile vizibile fără card în zonă (Turia, Cernat, Estelnic etc.) sunt **necontractate** — nu apar în ANPA/arebaltapeste/Romsilva → corect să nu aibă card.

## Pe județ
| Județ | total | prezent | anpa-missing | areba-missing | romsilva | uncontracted |
|---|---|---|---|---|---|---|
| Alba | 207 | 57 | 0 | 0 | 0 | 150 |
| Arad | 245 | 7 | 0 | 0 | 0 | 238 |
| Argeș | 164 | 36 | 0 | 0 | 0 | 128 |
| Bacău | 83 | 21 | 0 | 0 | 0 | 62 |
| Bihor | 282 | 34 | 0 | 0 | 0 | 246 |
| Bistrița-Năsăud | 174 | 24 | 0 | 0 | 0 | 148 |
| Botoșani | 89 | 37 | 0 | 0 | 0 | 52 |
| Brașov | 369 | 31 | 0 | 0 | 0 | 338 |
| Brăila | 59 | 8 | 0 | 0 | 0 | 51 |
| Buzău | 110 | 3 | 0 | 0 | 0 | 107 |
| Caraș-Severin | 722 | 41 | 0 | 0 | 0 | 681 |
| Cluj | 164 | 34 | 0 | 0 | 0 | 130 |
| Constanța | 143 | 1 | 0 | 0 | 0 | 142 |
| Covasna | 259 | 37 | 0 | 0 | 0 | 222 |
| Călărași | 75 | 0 | 0 | 0 | 0 | 75 |
| Dolj | 192 | 19 | 0 | 0 | 0 | 173 |
| Dâmbovița | 99 | 34 | 0 | 0 | 0 | 65 |
| Giurgiu | 63 | 7 | 0 | 0 | 0 | 56 |
| Gorj | 85 | 29 | 0 | 0 | 0 | 56 |
| Harghita | 364 | 56 | 0 | 0 | 0 | 308 |
| Hunedoara | 133 | 33 | 0 | 0 | 0 | 100 |
| Ialomița | 214 | 3 | 0 | 0 | 0 | 211 |
| Iași | 81 | 22 | 0 | 0 | 0 | 59 |
| Ilfov | 12 | 6 | 0 | 0 | 0 | 6 |
| Maramureș | 297 | 38 | 0 | 0 | 0 | 258 |
| Mehedinți | 376 | 5 | 0 | 0 | 0 | 371 |
| Mureș | 174 | 41 | 0 | 0 | 0 | 133 |
| Neamț | 442 | 10 | 0 | 0 | 0 | 432 |
| Olt | 93 | 8 | 0 | 0 | 0 | 85 |
| Prahova | 163 | 23 | 0 | 0 | 0 | 140 |
| Satu Mare | 85 | 4 | 0 | 0 | 0 | 81 |
| Sibiu | 152 | 36 | 0 | 0 | 0 | 116 |
| Suceava | 236 | 24 | 0 | 0 | 0 | 210 |
| Sălaj | 133 | 8 | 0 | 0 | 0 | 125 |
| TIMIȘ | 1 | 0 | 1 | 0 | 0 | 0 |
| Teleorman | 52 | 16 | 0 | 0 | 0 | 36 |
| Timiș | 281 | 54 | 0 | 0 | 0 | 227 |
| Vaslui | 441 | 16 | 0 | 0 | 0 | 425 |
| Vrancea | 37 | 16 | 0 | 0 | 0 | 21 |
| Vâlcea | 348 | 57 | 0 | 0 | 0 | 291 |

## Pe celulă (0.5°×0.5°)

### Celulă 43.4-43.9N, 20.0-20.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| banja | uncontracted |  |  |
| slatinska reka | uncontracted |  |  |
| бајановац | uncontracted |  |  |
| борошница | uncontracted |  |  |
| бјелица | uncontracted |  |  |
| вичка река | uncontracted |  |  |
| врањица | uncontracted |  |  |
| голијска моравица | uncontracted |  |  |
| грабска река | uncontracted |  |  |
| драгачица | uncontracted |  |  |
| западна морава | uncontracted |  |  |
| лазачка река | uncontracted |  |  |
| липничка река | uncontracted |  |  |
| лопатница | uncontracted |  |  |
| лупњача | uncontracted |  |  |
| лучка река | uncontracted |  |  |
| моравица | uncontracted |  |  |
| петничка река | uncontracted |  |  |
| премећка река | uncontracted |  |  |
| рогачка река | uncontracted |  |  |
| рћанска река | uncontracted |  |  |
| самаилска река | uncontracted |  |  |
| толишница | uncontracted |  |  |
| топлица | uncontracted |  |  |
| трнавска река | uncontracted |  |  |
| чемерница | uncontracted |  |  |
| јежевачка река | uncontracted |  |  |

### Celulă 43.4-43.9N, 20.5-21.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| dulenka | uncontracted |  |  |
| ibar / iber | uncontracted |  |  |
| kapetanovac | uncontracted |  |  |
| slatinska reka | uncontracted |  |  |
| бајмаковачки поток | uncontracted |  |  |
| бајовац | uncontracted |  |  |
| бајчетински поток | uncontracted |  |  |
| бинићки поток | uncontracted |  |  |
| бресница | uncontracted |  |  |
| брђански поток | uncontracted |  |  |
| бубан | uncontracted |  |  |
| буковац | uncontracted |  |  |
| велика река | uncontracted |  |  |
| вишњевац | uncontracted |  |  |
| врњачка река | uncontracted |  |  |
| годачичка река | uncontracted |  |  |
| грачачка река | uncontracted |  |  |
| грдичка река | uncontracted |  |  |
| грошница | uncontracted |  |  |
| гружа | uncontracted |  |  |
| дебељак | uncontracted |  |  |
| дебељачки поток | uncontracted |  |  |
| дрлупа | uncontracted |  |  |
| дубоки поток | uncontracted |  |  |
| дубочица | uncontracted |  |  |
| дуленка | uncontracted |  |  |
| жичка река | uncontracted |  |  |
| жутаја | uncontracted |  |  |
| закутска река | uncontracted |  |  |
| западна морава | uncontracted |  |  |
| ибар | uncontracted |  |  |
| каленићка река | uncontracted |  |  |
| каменица | uncontracted |  |  |
| ковачки поток | uncontracted |  |  |
| кремењак | uncontracted |  |  |
| кулинац | uncontracted |  |  |
| лађевачка река | uncontracted |  |  |
| липарски поток | uncontracted |  |  |
| липничка река | uncontracted |  |  |
| липовачка река | uncontracted |  |  |
| лопатница | uncontracted |  |  |
| лојанички поток | uncontracted |  |  |
| маглашница | uncontracted |  |  |
| маква | uncontracted |  |  |
| мељаница | uncontracted |  |  |
| милавчанска река | uncontracted |  |  |
| милочајски поток | uncontracted |  |  |
| мрсаћка река | uncontracted |  |  |
| мулинац | uncontracted |  |  |
| мусина река | uncontracted |  |  |
| новоселска река | uncontracted |  |  |
| орнички поток | uncontracted |  |  |
| пећинац | uncontracted |  |  |
| попинска река | uncontracted |  |  |
| поток мрсаћ | uncontracted |  |  |
| поток чађавац моравац | uncontracted |  |  |
| раваничка река | uncontracted |  |  |
| расина | uncontracted |  |  |
| ратинска река | uncontracted |  |  |
| ревеница | uncontracted |  |  |
| рибеж | uncontracted |  |  |
| рибница | uncontracted |  |  |
| ристића поток | uncontracted |  |  |
| самаилска река | uncontracted |  |  |
| сирчанска река | uncontracted |  |  |
| сурдулија | uncontracted |  |  |
| таревића поток | uncontracted |  |  |
| татарлук | uncontracted |  |  |
| товарница | uncontracted |  |  |
| топлица | uncontracted |  |  |
| трговиштанска река | uncontracted |  |  |
| црна река | uncontracted |  |  |
| црни поток | uncontracted |  |  |
| чађавац | uncontracted |  |  |
| чађавац моравац | uncontracted |  |  |
| честинска река | uncontracted |  |  |
| јосевик | uncontracted |  |  |
| љубостињска река | uncontracted |  |  |

### Celulă 43.4-43.9N, 21.0-21.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| буковац | uncontracted |  |  |
| велика морава | uncontracted |  |  |
| гарски поток | uncontracted |  |  |
| грза | uncontracted |  |  |
| дуленка | uncontracted |  |  |
| жупањевачка | uncontracted |  |  |
| западна морава | uncontracted |  |  |
| каленићка река | uncontracted |  |  |
| каменица | uncontracted |  |  |
| кочански поток | uncontracted |  |  |
| липница | uncontracted |  |  |
| липнички поток | uncontracted |  |  |
| лугомир | uncontracted |  |  |
| мијајловачка река | uncontracted |  |  |
| орловачки поток | uncontracted |  |  |
| ражањска река | uncontracted |  |  |
| расина | uncontracted |  |  |
| рибарска река | uncontracted |  |  |
| риљачка река | uncontracted |  |  |
| топлик | uncontracted |  |  |
| црквени поток | uncontracted |  |  |
| црница | uncontracted |  |  |
| шупљаја | uncontracted |  |  |
| јовановачка река | uncontracted |  |  |
| јужна морава | uncontracted |  |  |
| љубостињска река | uncontracted |  |  |

### Celulă 43.4-43.9N, 21.5-22.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bogdasinska reka | uncontracted |  |  |
| ivanstica | uncontracted |  |  |
| milusinacka reka | uncontracted |  |  |
| nikolinacka reka | uncontracted |  |  |
| slemenski potok | uncontracted |  |  |
| velika reka | uncontracted |  |  |
| vosacka reka | uncontracted |  |  |
| арнаута | uncontracted |  |  |
| боговина | uncontracted |  |  |
| бршка река | uncontracted |  |  |
| в честобродица | uncontracted |  |  |
| ваља маре | uncontracted |  |  |
| велика река | uncontracted |  |  |
| велика суваја | uncontracted |  |  |
| врбовачки поток | uncontracted |  |  |
| врело | uncontracted |  |  |
| врелски поток | uncontracted |  |  |
| врмџанска река | uncontracted |  |  |
| грабовачка река | uncontracted |  |  |
| градашница | uncontracted |  |  |
| грза | uncontracted |  |  |
| грнчарски поток | uncontracted |  |  |
| зарвина | uncontracted |  |  |
| змијанац | uncontracted |  |  |
| изгаре | uncontracted |  |  |
| крћева | uncontracted |  |  |
| крћеваа | uncontracted |  |  |
| лозанска река | uncontracted |  |  |
| лозица | uncontracted |  |  |
| лопушњански поток | uncontracted |  |  |
| лудачки поток | uncontracted |  |  |
| м честобродица | uncontracted |  |  |
| мала суваја | uncontracted |  |  |
| манастирски поток | uncontracted |  |  |
| мађарска река | uncontracted |  |  |
| мировска река | uncontracted |  |  |
| моравица | uncontracted |  |  |
| мратиња | uncontracted |  |  |
| огашу бурдуш | uncontracted |  |  |
| огашу виљор | uncontracted |  |  |
| огашу куљорда | uncontracted |  |  |
| огашу сатулуј | uncontracted |  |  |
| паклешки поток | uncontracted |  |  |
| петровац | uncontracted |  |  |
| прчевица | uncontracted |  |  |
| радованска река | uncontracted |  |  |
| ражањска река | uncontracted |  |  |
| рашинац | uncontracted |  |  |
| репушнички п | uncontracted |  |  |
| рибарска река | uncontracted |  |  |
| рујевачки поток | uncontracted |  |  |
| рујишка река | uncontracted |  |  |
| свињски поток | uncontracted |  |  |
| селинска река | uncontracted |  |  |
| сеоски поток | uncontracted |  |  |
| сесалачка река | uncontracted |  |  |
| станикићева јаруга | uncontracted |  |  |
| стрњак | uncontracted |  |  |
| сувара | uncontracted |  |  |
| суваја радованске реке | uncontracted |  |  |
| топлик | uncontracted |  |  |
| трска | uncontracted |  |  |
| трска река | uncontracted |  |  |
| црни тимок | uncontracted |  |  |
| јавор | uncontracted |  |  |
| јовановачка река | uncontracted |  |  |
| јошаничка река | uncontracted |  |  |
| јужна морава | uncontracted |  |  |

### Celulă 43.4-43.9N, 22.0-22.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| crnobarski potok | uncontracted |  |  |
| gladna reka | uncontracted |  |  |
| izgare | uncontracted |  |  |
| milusinacka reka | uncontracted |  |  |
| mitrovska reka | uncontracted |  |  |
| nenadovski potok | uncontracted |  |  |
| pavlovacka reka | uncontracted |  |  |
| suvi potok | uncontracted |  |  |
| tija | uncontracted |  |  |
| tisovik | uncontracted |  |  |
| urdeski potok | uncontracted |  |  |
| арнаута | uncontracted |  |  |
| арчар | uncontracted |  |  |
| бачевичка река | uncontracted |  |  |
| бачевички поток | uncontracted |  |  |
| бели тимок | uncontracted |  |  |
| братински поток | uncontracted |  |  |
| бучјанска река | uncontracted |  |  |
| ваља маре | uncontracted |  |  |
| видбол | uncontracted |  |  |
| горња река | uncontracted |  |  |
| грлишка река | uncontracted |  |  |
| давидова бара | uncontracted |  |  |
| драганин поток | uncontracted |  |  |
| иванчовец | uncontracted |  |  |
| изгаре | uncontracted |  |  |
| коритска река | uncontracted |  |  |
| корманица | uncontracted |  |  |
| кръстина | uncontracted |  |  |
| курдуман | uncontracted |  |  |
| ласовачка река | uncontracted |  |  |
| леновачка река | uncontracted |  |  |
| лозанска река | uncontracted |  |  |
| лубничка река | uncontracted |  |  |
| манастирски дол | uncontracted |  |  |
| манастирски поток | uncontracted |  |  |
| негалица | uncontracted |  |  |
| ненов до | uncontracted |  |  |
| огашу бурдуш | uncontracted |  |  |
| огашу бурћи | uncontracted |  |  |
| огашу војни | uncontracted |  |  |
| огашу куљорда | uncontracted |  |  |
| оснићка река | uncontracted |  |  |
| паралво | uncontracted |  |  |
| планиничка река | uncontracted |  |  |
| планински поток | uncontracted |  |  |
| плочака | uncontracted |  |  |
| прлитски поток | uncontracted |  |  |
| рашов поток | uncontracted |  |  |
| рајин поток | uncontracted |  |  |
| салашка | uncontracted |  |  |
| селачка | uncontracted |  |  |
| селишки поток | uncontracted |  |  |
| смръдля | uncontracted |  |  |
| соколовачка река | uncontracted |  |  |
| станикићева јаруга | uncontracted |  |  |
| стублата | uncontracted |  |  |
| стублешки дол | uncontracted |  |  |
| тополовец | uncontracted |  |  |
| трска река | uncontracted |  |  |
| црни тимок | uncontracted |  |  |
| чичилска | uncontracted |  |  |
| ђаволски поток | uncontracted |  |  |
| јелашничка река | uncontracted |  |  |

### Celulă 43.4-43.9N, 22.5-23.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| danube | uncontracted |  |  |
| dunarea дунав | uncontracted |  |  |
| арчар | uncontracted |  |  |
| асанка | uncontracted |  |  |
| барски дол | uncontracted |  |  |
| бел мустак | uncontracted |  |  |
| богомоя | uncontracted |  |  |
| бубински дол | uncontracted |  |  |
| видбол | uncontracted |  |  |
| влашки дол | uncontracted |  |  |
| вълчешки дол | uncontracted |  |  |
| въртопски дол | uncontracted |  |  |
| гаитански дол | uncontracted |  |  |
| гачов дол | uncontracted |  |  |
| градска | uncontracted |  |  |
| грамадска | uncontracted |  |  |
| зебляшки дол | uncontracted |  |  |
| кожухарски дол | uncontracted |  |  |
| конов дол | uncontracted |  |  |
| корманица | uncontracted |  |  |
| кукуренски дол | uncontracted |  |  |
| курляк | uncontracted |  |  |
| кучовец | uncontracted |  |  |
| кърповец | uncontracted |  |  |
| къси дол | uncontracted |  |  |
| кюнеца | uncontracted |  |  |
| липовски дол | uncontracted |  |  |
| лозарска бара | uncontracted |  |  |
| лозарски дол | uncontracted |  |  |
| лом | uncontracted |  |  |
| манкулишки дол | uncontracted |  |  |
| милчинска | uncontracted |  |  |
| нечинска | uncontracted |  |  |
| огоста | uncontracted |  |  |
| ошанска | uncontracted |  |  |
| парков дол | uncontracted |  |  |
| пенански дол | uncontracted |  |  |
| пльочешки дол | uncontracted |  |  |
| пунов дол | uncontracted |  |  |
| пунчов дол | uncontracted |  |  |
| първанов дол | uncontracted |  |  |
| р цибрица | uncontracted |  |  |
| ранкин дол | uncontracted |  |  |
| раповски дол | uncontracted |  |  |
| салашка | uncontracted |  |  |
| сврачи дол | uncontracted |  |  |
| сеньов дол | uncontracted |  |  |
| синявец | uncontracted |  |  |
| скомля | uncontracted |  |  |
| сливовишка | uncontracted |  |  |
| смръдля | uncontracted |  |  |
| стакевска река | uncontracted |  |  |
| стакевска_река | uncontracted |  |  |
| стубленски дол | uncontracted |  |  |
| студенски дол | uncontracted |  |  |
| съботинка | uncontracted |  |  |
| табашки дол | uncontracted |  |  |
| тополовец | uncontracted |  |  |
| уморов дол | uncontracted |  |  |
| церов дол | uncontracted |  |  |
| чавков дол | uncontracted |  |  |
| чемеришки дол | uncontracted |  |  |
| чичилска | uncontracted |  |  |
| ясова бара | uncontracted |  |  |

### Celulă 43.4-43.9N, 23.0-23.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| balasan | present | AJVPS DOLJ |  |
| balta sarbilor | uncontracted |  |  |
| danube | uncontracted |  |  |
| dunarea дунав | uncontracted |  |  |
| барски дол | uncontracted |  |  |
| гаговица | uncontracted |  |  |
| градински дол | uncontracted |  |  |
| гугувишка бара | uncontracted |  |  |
| джумаиски дол | uncontracted |  |  |
| лом | uncontracted |  |  |
| манастирски дол | uncontracted |  |  |
| мрътвицата | uncontracted |  |  |
| нечинска | uncontracted |  |  |
| огоста | uncontracted |  |  |
| р цибрица | uncontracted |  |  |

### Celulă 43.4-43.9N, 23.5-24.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| danube | uncontracted |  |  |
| dunarea дунав | uncontracted |  |  |
| jiu | present | AJVPS GORJ |  |
| raul desnatui | present | AJVPS DOLJ |  |
| raul jiet | present | AJVPS DOLJ |  |
| огоста | uncontracted |  |  |
| правия дол | uncontracted |  |  |
| р цибрица | uncontracted |  |  |
| река скът | uncontracted |  |  |
| скът | uncontracted |  |  |

### Celulă 43.4-43.9N, 24.0-24.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| coscan | uncontracted |  |  |
| crusovul | uncontracted |  |  |
| danube | uncontracted |  |  |
| dunarea дунав | uncontracted |  |  |
| obarsia | uncontracted |  |  |
| paraul morilor | present | AJVPS ALBA | audit_match:override |
| paraul obarsia | uncontracted |  |  |
| sneagul | uncontracted |  |  |
| valea jiu | present | AJVPS GORJ |  |
| григлин дол | uncontracted |  |  |
| дълбоки дол | uncontracted |  |  |
| искър | uncontracted |  |  |
| правия дол | uncontracted |  |  |
| селската бара | uncontracted |  |  |

### Celulă 43.4-43.9N, 24.5-25.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| calmatui | present | AJVPS TELEORMAN | anpa_map:sweep:calmatui |
| coscan | uncontracted |  |  |
| crusovul | uncontracted |  |  |
| danube | uncontracted |  |  |
| dunarea дунав | uncontracted |  |  |
| ecluza izbiceni | uncontracted |  |  |
| obarsia | uncontracted |  |  |
| olt | present | AJVPS OLT |  |
| sai | uncontracted |  |  |
| sultan | uncontracted |  |  |
| valea ursii | uncontracted |  |  |
| вит | uncontracted |  |  |
| осъм | uncontracted |  |  |

### Celulă 43.4-43.9N, 25.0-25.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bratul belina | uncontracted |  |  |
| calmatui | present | AJVPS TELEORMAN | anpa_map:sweep:calmatui |
| danube | uncontracted |  |  |
| ducna | uncontracted |  |  |
| dunarea дунав | uncontracted |  |  |
| putul ogarului | uncontracted |  |  |
| raul pasarea | uncontracted |  |  |
| raul teleorman | present | AJVPS TELEORMAN |  |
| raul urlui | present | AJVPS TELEORMAN |  |
| raul vedea | present | AJVPS TELEORMAN | multiway_chain |
| teleorman | present | AJVPS TELEORMAN |  |
| urlui | present | AJVPS TELEORMAN |  |
| vedea | present | AJVPS TELEORMAN | multiway_chain |
| vidrosu | uncontracted |  |  |
| дунав | uncontracted |  |  |
| осъм | uncontracted |  |  |
| студената река | uncontracted |  |  |
| текир дере | uncontracted |  |  |

### Celulă 43.4-43.9N, 25.5-26.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bratul ara | uncontracted |  |  |
| danube | uncontracted |  |  |
| dunarea | uncontracted |  |  |
| dunarea дунав | uncontracted |  |  |
| raul pasarea | uncontracted |  |  |
| raul vedea | present | AJVPS TELEORMAN | multiway_chain |
| vedea | present | AJVPS TELEORMAN | multiway_chain |
| дунав | uncontracted |  |  |
| русенски лом | uncontracted |  |  |
| студената река | uncontracted |  |  |
| черни лом | uncontracted |  |  |
| янтра | uncontracted |  |  |

### Celulă 43.4-43.9N, 26.0-26.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bratul ara | uncontracted |  |  |
| danube | uncontracted |  |  |
| dunarea дунав | uncontracted |  |  |
| бели лом | uncontracted |  |  |
| малък лом | uncontracted |  |  |
| преливник | uncontracted |  |  |
| р сараджииска | uncontracted |  |  |
| русенски лом | uncontracted |  |  |
| топчииска река | uncontracted |  |  |
| черни лом | uncontracted |  |  |

### Celulă 43.4-43.9N, 26.5-27.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| бели лом | uncontracted |  |  |
| воина | uncontracted |  |  |
| канагьол | uncontracted |  |  |
| сенковец | uncontracted |  |  |
| топчииска река | uncontracted |  |  |
| царацар | uncontracted |  |  |
| чаирлък | uncontracted |  |  |

### Celulă 43.4-43.9N, 27.0-27.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| канагьол | uncontracted |  |  |
| карамандере | uncontracted |  |  |
| хърсовска | uncontracted |  |  |

### Celulă 43.4-43.9N, 27.5-28.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| добричка река | uncontracted |  |  |
| карамандере | uncontracted |  |  |
| суха река | uncontracted |  |  |

### Celulă 43.9-44.4N, 20.0-20.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| бацковац | uncontracted |  |  |
| башчића река | uncontracted |  |  |
| босута | uncontracted |  |  |
| брајићка река | uncontracted |  |  |
| буковац | uncontracted |  |  |
| букуља | uncontracted |  |  |
| велика букуља | uncontracted |  |  |
| велика дичина | uncontracted |  |  |
| венчанска река | uncontracted |  |  |
| грабовац | uncontracted |  |  |
| деспотовица | uncontracted |  |  |
| дичина | uncontracted |  |  |
| драгобиљ | uncontracted |  |  |
| драгобиљица | uncontracted |  |  |
| дреновача | uncontracted |  |  |
| западна морава | uncontracted |  |  |
| златарица | uncontracted |  |  |
| ивички | uncontracted |  |  |
| каменица | uncontracted |  |  |
| качер | uncontracted |  |  |
| клатичевска река | uncontracted |  |  |
| козељица | uncontracted |  |  |
| колубара | uncontracted |  |  |
| лесковица | uncontracted |  |  |
| лукавица | uncontracted |  |  |
| мала букуља | uncontracted |  |  |
| мала дичина | uncontracted |  |  |
| оњег | uncontracted |  |  |
| пештан | uncontracted |  |  |
| плана | uncontracted |  |  |
| равна река | uncontracted |  |  |
| раковица | uncontracted |  |  |
| речица | uncontracted |  |  |
| ријека | uncontracted |  |  |
| селац | uncontracted |  |  |
| славковачка река | uncontracted |  |  |
| смрдуша | uncontracted |  |  |
| чемерница | uncontracted |  |  |
| шибан | uncontracted |  |  |
| шишковац | uncontracted |  |  |
| јабланичка река | uncontracted |  |  |
| јакљево | uncontracted |  |  |
| јововац | uncontracted |  |  |
| љиг | uncontracted |  |  |

### Celulă 43.9-44.4N, 20.5-21.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| kudrecki potok | uncontracted |  |  |
| manastirska reka | uncontracted |  |  |
| studenac | uncontracted |  |  |
| блатар | uncontracted |  |  |
| борачка река | uncontracted |  |  |
| босута | uncontracted |  |  |
| буковац | uncontracted |  |  |
| букуља | uncontracted |  |  |
| велика букуља | uncontracted |  |  |
| виција | uncontracted |  |  |
| вињиштански поток | uncontracted |  |  |
| врбичка река | uncontracted |  |  |
| грошница | uncontracted |  |  |
| грошничка река | uncontracted |  |  |
| гружа | uncontracted |  |  |
| губераш | uncontracted |  |  |
| дебељак | uncontracted |  |  |
| доловски поток | uncontracted |  |  |
| драчка река | uncontracted |  |  |
| дугачки поток | uncontracted |  |  |
| ердечица | uncontracted |  |  |
| ждраљичка река | uncontracted |  |  |
| златарица | uncontracted |  |  |
| ивак | uncontracted |  |  |
| каменица | uncontracted |  |  |
| клисура | uncontracted |  |  |
| кошарна | uncontracted |  |  |
| кубршница | uncontracted |  |  |
| лепеница | uncontracted |  |  |
| лимовац | uncontracted |  |  |
| липничка река | uncontracted |  |  |
| луг | uncontracted |  |  |
| луцин поток | uncontracted |  |  |
| мадупски поток | uncontracted |  |  |
| мала букуља | uncontracted |  |  |
| мали луг | uncontracted |  |  |
| мамутовац | uncontracted |  |  |
| милатовица | uncontracted |  |  |
| мисача | uncontracted |  |  |
| осаоница | uncontracted |  |  |
| пештан | uncontracted |  |  |
| поломски поток | uncontracted |  |  |
| прњаворски поток | uncontracted |  |  |
| рача | uncontracted |  |  |
| рибеж | uncontracted |  |  |
| сребреница | uncontracted |  |  |
| стара јасеница | uncontracted |  |  |
| сушички поток | uncontracted |  |  |
| тицина вода | uncontracted |  |  |
| трстена | uncontracted |  |  |
| угљешница | uncontracted |  |  |
| церовити поток | uncontracted |  |  |
| ђуринци | uncontracted |  |  |
| ђуриселски поток | uncontracted |  |  |
| јаворски поток | uncontracted |  |  |
| јасеница | uncontracted |  |  |

### Celulă 43.9-44.4N, 21.0-21.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| danube | uncontracted |  |  |
| gibavica | uncontracted |  |  |
| racnicka reka | uncontracted |  |  |
| белица | uncontracted |  |  |
| бешњаја | uncontracted |  |  |
| бељево | uncontracted |  |  |
| бистричка река | uncontracted |  |  |
| бошњачки поток | uncontracted |  |  |
| брзоходски поток | uncontracted |  |  |
| булињак | uncontracted |  |  |
| бусур | uncontracted |  |  |
| велика морава | uncontracted |  |  |
| витовница | uncontracted |  |  |
| витовничка река | uncontracted |  |  |
| вољевица | uncontracted |  |  |
| гигово | uncontracted |  |  |
| грабовик | uncontracted |  |  |
| грабовичка река | uncontracted |  |  |
| дабовачки поток | uncontracted |  |  |
| деонички поток | uncontracted |  |  |
| доловски поток | uncontracted |  |  |
| дражевац | uncontracted |  |  |
| дубочки поток | uncontracted |  |  |
| кореница | uncontracted |  |  |
| лепеница | uncontracted |  |  |
| липовити поток | uncontracted |  |  |
| личина јаруга | uncontracted |  |  |
| лугомир | uncontracted |  |  |
| луди поток | uncontracted |  |  |
| мелничка река | uncontracted |  |  |
| мело | uncontracted |  |  |
| млава | uncontracted |  |  |
| мртвички поток | uncontracted |  |  |
| осаоница | uncontracted |  |  |
| пањевачка река | uncontracted |  |  |
| попов поток | uncontracted |  |  |
| раваница | uncontracted |  |  |
| рача | uncontracted |  |  |
| рачничка река | uncontracted |  |  |
| ресава | uncontracted |  |  |
| решковица | uncontracted |  |  |
| средњевршки поток | uncontracted |  |  |
| стамничка река | uncontracted |  |  |
| топлик | uncontracted |  |  |
| трстена | uncontracted |  |  |
| хајдучки поток | uncontracted |  |  |
| црвени поток | uncontracted |  |  |
| црница | uncontracted |  |  |
| четерешки поток | uncontracted |  |  |
| чокордин | uncontracted |  |  |
| шетоњска река | uncontracted |  |  |
| шибовити поток | uncontracted |  |  |
| штипљанска река | uncontracted |  |  |
| јасеница | uncontracted |  |  |
| јошаница | uncontracted |  |  |
| југовачки поток | uncontracted |  |  |

### Celulă 43.9-44.4N, 21.5-22.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| crveni potok | uncontracted |  |  |
| danube | uncontracted |  |  |
| debeloglavski potok | uncontracted |  |  |
| ivanstica | uncontracted |  |  |
| jablanicki potok | uncontracted |  |  |
| jeremiski potok | uncontracted |  |  |
| sanonski potok | uncontracted |  |  |
| stanojev potok | uncontracted |  |  |
| zabar | uncontracted |  |  |
| амугин поток | uncontracted |  |  |
| бабин поток | uncontracted |  |  |
| бела река | uncontracted |  |  |
| бељаничка река | uncontracted |  |  |
| бељевина | uncontracted |  |  |
| бигор | uncontracted |  |  |
| бистричка река | uncontracted |  |  |
| бобовачка река | uncontracted |  |  |
| богданов поток | uncontracted |  |  |
| боговина | uncontracted |  |  |
| божина река | uncontracted |  |  |
| божулуј | uncontracted |  |  |
| бреза | uncontracted |  |  |
| брезничка река | uncontracted |  |  |
| брезовица | uncontracted |  |  |
| бук | uncontracted |  |  |
| бурдељски поток | uncontracted |  |  |
| бусовата | uncontracted |  |  |
| ваља бледари | uncontracted |  |  |
| ваља де мижлок | uncontracted |  |  |
| ваља кршијори | uncontracted |  |  |
| ваља лучак | uncontracted |  |  |
| ваља маре | uncontracted |  |  |
| ваља маслака | uncontracted |  |  |
| ваља мика | uncontracted |  |  |
| ваља микуљ | uncontracted |  |  |
| ваља петру | uncontracted |  |  |
| ваља рнж | uncontracted |  |  |
| ваља станоје | uncontracted |  |  |
| ваља стрази | uncontracted |  |  |
| велика гложана | uncontracted |  |  |
| велика равна река | uncontracted |  |  |
| велика сакаштица | uncontracted |  |  |
| велика тисница | uncontracted |  |  |
| велики валкалуци | uncontracted |  |  |
| велики кленовник | uncontracted |  |  |
| велики пек | uncontracted |  |  |
| велики поток | uncontracted |  |  |
| веј | uncontracted |  |  |
| вејска река | uncontracted |  |  |
| винатовачка река | uncontracted |  |  |
| витовница | uncontracted |  |  |
| витовничка река | uncontracted |  |  |
| војал | uncontracted |  |  |
| врело | uncontracted |  |  |
| галоња | uncontracted |  |  |
| грабова река | uncontracted |  |  |
| грабовачка река | uncontracted |  |  |
| дебели поток | uncontracted |  |  |
| до | uncontracted |  |  |
| дубашница | uncontracted |  |  |
| дубочица | uncontracted |  |  |
| дубравски поток | uncontracted |  |  |
| жида | uncontracted |  |  |
| звералуј | uncontracted |  |  |
| злотска река | uncontracted |  |  |
| илијев поток | uncontracted |  |  |
| каменичка река | uncontracted |  |  |
| карапанџа | uncontracted |  |  |
| кеј | uncontracted |  |  |
| кленцуш | uncontracted |  |  |
| клочаница | uncontracted |  |  |
| ковеј | uncontracted |  |  |
| комненска река | uncontracted |  |  |
| комша | uncontracted |  |  |
| краварица | uncontracted |  |  |
| крепољинска река | uncontracted |  |  |
| кривуља | uncontracted |  |  |
| крлинац | uncontracted |  |  |
| крупаја | uncontracted |  |  |
| крупајска река | uncontracted |  |  |
| крушевачки поток | uncontracted |  |  |
| лазарев поток | uncontracted |  |  |
| лазарева река | uncontracted |  |  |
| лалин поток | uncontracted |  |  |
| липа | uncontracted |  |  |
| липуца | uncontracted |  |  |
| мала равна река | uncontracted |  |  |
| мала река | uncontracted |  |  |
| мала тисница | uncontracted |  |  |
| мала црвена | uncontracted |  |  |
| мали валкалуци | uncontracted |  |  |
| мали кленовник | uncontracted |  |  |
| мали пек | uncontracted |  |  |
| мара миш | uncontracted |  |  |
| марканов поток | uncontracted |  |  |
| мацин поток | uncontracted |  |  |
| мелничка река | uncontracted |  |  |
| милатовачка река | uncontracted |  |  |
| млава | uncontracted |  |  |
| мускал | uncontracted |  |  |
| некудово | uncontracted |  |  |
| николин поток | uncontracted |  |  |
| огасу ал иарг | uncontracted |  |  |
| огасу дојдјути | uncontracted |  |  |
| огашу ал ларг | uncontracted |  |  |
| огашу гриљеи | uncontracted |  |  |
| огашу девесел | uncontracted |  |  |
| огашу зронцан | uncontracted |  |  |
| огашу кровулуј | uncontracted |  |  |
| огашу ла роу | uncontracted |  |  |
| огашу мори | uncontracted |  |  |
| огашу пиран | uncontracted |  |  |
| огашу србулуј | uncontracted |  |  |
| огашу тилва | uncontracted |  |  |
| огашу шершел | uncontracted |  |  |
| огашу шинушари | uncontracted |  |  |
| огашул попоран | uncontracted |  |  |
| огашул фреалан | uncontracted |  |  |
| осаничка река | uncontracted |  |  |
| падина маре | uncontracted |  |  |
| пађина лунга | uncontracted |  |  |
| пањевачка река | uncontracted |  |  |
| пек | uncontracted |  |  |
| пераст | uncontracted |  |  |
| пећинска река | uncontracted |  |  |
| полом | uncontracted |  |  |
| попов поток | uncontracted |  |  |
| појењска река | uncontracted |  |  |
| пјатра њагра | uncontracted |  |  |
| раваница | uncontracted |  |  |
| равна река | uncontracted |  |  |
| равноречки поток | uncontracted |  |  |
| радованска река | uncontracted |  |  |
| ресава | uncontracted |  |  |
| ресавица | uncontracted |  |  |
| речке | uncontracted |  |  |
| решковица | uncontracted |  |  |
| сарака | uncontracted |  |  |
| скорушки поток | uncontracted |  |  |
| стамничка река | uncontracted |  |  |
| старчев поток | uncontracted |  |  |
| стењка | uncontracted |  |  |
| стопањски поток | uncontracted |  |  |
| стрмљана | uncontracted |  |  |
| студени поток | uncontracted |  |  |
| сува река | uncontracted |  |  |
| сувар | uncontracted |  |  |
| сувара | uncontracted |  |  |
| суваја клочанице | uncontracted |  |  |
| суваја радованске реке | uncontracted |  |  |
| тајски поток | uncontracted |  |  |
| тодорова река | uncontracted |  |  |
| топлик | uncontracted |  |  |
| удубашница | uncontracted |  |  |
| умкин поток | uncontracted |  |  |
| фаљешана | uncontracted |  |  |
| црвена река | uncontracted |  |  |
| црна река | uncontracted |  |  |
| црница | uncontracted |  |  |
| чемернички поток | uncontracted |  |  |
| шашка река | uncontracted |  |  |
| јагнило | uncontracted |  |  |
| јелови поток | uncontracted |  |  |

### Celulă 43.9-44.4N, 22.0-22.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| danube | uncontracted |  |  |
| vujana | uncontracted |  |  |
| zetnja reka | uncontracted |  |  |
| zmiljnja reka | uncontracted |  |  |
| алапин | uncontracted |  |  |
| арнаута | uncontracted |  |  |
| бабин поток | uncontracted |  |  |
| бањица | uncontracted |  |  |
| бањски поток | uncontracted |  |  |
| безданица | uncontracted |  |  |
| бездъница | uncontracted |  |  |
| бели тимок | uncontracted |  |  |
| бигар | uncontracted |  |  |
| бигрен | uncontracted |  |  |
| бориловски поток | uncontracted |  |  |
| борска река | uncontracted |  |  |
| браћевачка река | uncontracted |  |  |
| бреза | uncontracted |  |  |
| брестовачка река | uncontracted |  |  |
| бруснички поток | uncontracted |  |  |
| бучинац | uncontracted |  |  |
| буљевица | uncontracted |  |  |
| ваља ку фрасн | uncontracted |  |  |
| ваља маре | uncontracted |  |  |
| велика близна река | uncontracted |  |  |
| велика бреза | uncontracted |  |  |
| велика сакаштица | uncontracted |  |  |
| велики габар | uncontracted |  |  |
| ветрења | uncontracted |  |  |
| вирови | uncontracted |  |  |
| влашки дол | uncontracted |  |  |
| вратна | uncontracted |  |  |
| врањевац | uncontracted |  |  |
| врелска река | uncontracted |  |  |
| вучак | uncontracted |  |  |
| габар | uncontracted |  |  |
| глоговичка река | uncontracted |  |  |
| градишка река | uncontracted |  |  |
| градски поток | uncontracted |  |  |
| дабинац | uncontracted |  |  |
| дреновачки поток | uncontracted |  |  |
| дубоки поток | uncontracted |  |  |
| дугорница | uncontracted |  |  |
| дупљанска река | uncontracted |  |  |
| замна | uncontracted |  |  |
| злотска река | uncontracted |  |  |
| калатин | uncontracted |  |  |
| каменичка река | uncontracted |  |  |
| клокочевачки поток | uncontracted |  |  |
| кортар | uncontracted |  |  |
| крагујевац | uncontracted |  |  |
| кривељска река | uncontracted |  |  |
| крлинац | uncontracted |  |  |
| крушевачки поток | uncontracted |  |  |
| лева река | uncontracted |  |  |
| лозовица | uncontracted |  |  |
| лубничка јаруга | uncontracted |  |  |
| лучка река | uncontracted |  |  |
| мала близна река | uncontracted |  |  |
| мала бреза | uncontracted |  |  |
| мали габар | uncontracted |  |  |
| мали превод | uncontracted |  |  |
| мастакан | uncontracted |  |  |
| мачка река | uncontracted |  |  |
| мачкин поток | uncontracted |  |  |
| медвеђа река | uncontracted |  |  |
| михајлов поток | uncontracted |  |  |
| миљаковац | uncontracted |  |  |
| ненов до | uncontracted |  |  |
| несторов поток | uncontracted |  |  |
| ников дол | uncontracted |  |  |
| николичевска река | uncontracted |  |  |
| нишорски дол | uncontracted |  |  |
| огаш лу маринку | uncontracted |  |  |
| огашу борулуј | uncontracted |  |  |
| огашу брестовац | uncontracted |  |  |
| огашу бугарин | uncontracted |  |  |
| огашу драгули | uncontracted |  |  |
| огашу корнули | uncontracted |  |  |
| огашу кровулуј | uncontracted |  |  |
| огашу крчагулуј | uncontracted |  |  |
| огашу ку пјатра | uncontracted |  |  |
| огашу кучајни | uncontracted |  |  |
| огашу лу виње | uncontracted |  |  |
| огашу лу кобила | uncontracted |  |  |
| огашу лупша | uncontracted |  |  |
| огашу маре | uncontracted |  |  |
| огашу пери | uncontracted |  |  |
| огашу раји | uncontracted |  |  |
| огашу реу | uncontracted |  |  |
| огашу траила | uncontracted |  |  |
| огашу урсан | uncontracted |  |  |
| огашу ђени | uncontracted |  |  |
| оснићка река | uncontracted |  |  |
| павлов поток | uncontracted |  |  |
| патранов поток | uncontracted |  |  |
| плочака | uncontracted |  |  |
| полянски дол | uncontracted |  |  |
| попадија | uncontracted |  |  |
| поповичка река | uncontracted |  |  |
| поречка река | uncontracted |  |  |
| поток турија | uncontracted |  |  |
| преводски поток | uncontracted |  |  |
| преки поток | uncontracted |  |  |
| пунђилов поток | uncontracted |  |  |
| пујица | uncontracted |  |  |
| пјатра њагра | uncontracted |  |  |
| рабровска | uncontracted |  |  |
| равна река | uncontracted |  |  |
| радовица | uncontracted |  |  |
| реуморилор | uncontracted |  |  |
| ружана | uncontracted |  |  |
| рукјавица | uncontracted |  |  |
| рујарац | uncontracted |  |  |
| салашка река | uncontracted |  |  |
| сарака | uncontracted |  |  |
| саставци | uncontracted |  |  |
| селишки поток | uncontracted |  |  |
| селиштанска река | uncontracted |  |  |
| селиштански поток | uncontracted |  |  |
| сиколска река | uncontracted |  |  |
| скорушки поток | uncontracted |  |  |
| скочка река | uncontracted |  |  |
| скроботанов поток | uncontracted |  |  |
| слатинска река | uncontracted |  |  |
| совинац | uncontracted |  |  |
| соја | uncontracted |  |  |
| стањев поток | uncontracted |  |  |
| стопањски поток | uncontracted |  |  |
| стрмљана | uncontracted |  |  |
| стублата | uncontracted |  |  |
| стублешки дол | uncontracted |  |  |
| сува река | uncontracted |  |  |
| суви поток | uncontracted |  |  |
| суводолска река | uncontracted |  |  |
| сурдуп | uncontracted |  |  |
| табаковачки поток | uncontracted |  |  |
| тимок | uncontracted |  |  |
| тополница | uncontracted |  |  |
| топљански поток | uncontracted |  |  |
| турија | uncontracted |  |  |
| туријица | uncontracted |  |  |
| търновски дол | uncontracted |  |  |
| удубашница | uncontracted |  |  |
| умишни поток | uncontracted |  |  |
| умния дол | uncontracted |  |  |
| ујовица | uncontracted |  |  |
| хајдучки поток | uncontracted |  |  |
| цакин поток | uncontracted |  |  |
| црвена река | uncontracted |  |  |
| црнајка | uncontracted |  |  |
| црни тимок | uncontracted |  |  |
| чубранска река | uncontracted |  |  |
| чулин поток | uncontracted |  |  |
| шарбановачка река | uncontracted |  |  |
| шаркаменска река | uncontracted |  |  |
| шашка река | uncontracted |  |  |
| ђаволски поток | uncontracted |  |  |
| јаз | uncontracted |  |  |
| јасеничка река | uncontracted |  |  |
| јасење | uncontracted |  |  |
| јелашничка река | uncontracted |  |  |
| љубова река | uncontracted |  |  |
| џанов поток | uncontracted |  |  |

### Celulă 43.9-44.4N, 22.5-23.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| blahnita | present | AJVPS GORJ |  |
| danube | uncontracted |  |  |
| drincea | present | AJVPS DOLJ |  |
| drincea 1 | uncontracted |  |  |
| dunarea | uncontracted |  |  |
| dunarea дунав | uncontracted |  |  |
| dunav/dunarea | uncontracted |  |  |
| paraul blahnita | present | AJVPS GORJ |  |
| paraul orevita | uncontracted |  |  |
| барата | uncontracted |  |  |
| белорадска | uncontracted |  |  |
| белорадски дол | uncontracted |  |  |
| бориловски поток | uncontracted |  |  |
| бранчински дол | uncontracted |  |  |
| браћевачка река | uncontracted |  |  |
| видбол | uncontracted |  |  |
| видровец | uncontracted |  |  |
| воинишка | uncontracted |  |  |
| делеинска | uncontracted |  |  |
| дубоки поток | uncontracted |  |  |
| дупљанска река | uncontracted |  |  |
| замна | uncontracted |  |  |
| каменичка река | uncontracted |  |  |
| канал јасеничке реке | uncontracted |  |  |
| корманица | uncontracted |  |  |
| куси дол | uncontracted |  |  |
| манастирски поток | uncontracted |  |  |
| нишора | uncontracted |  |  |
| нишорски дол | uncontracted |  |  |
| поповски дол | uncontracted |  |  |
| потока | uncontracted |  |  |
| рабровска | uncontracted |  |  |
| радулуј | uncontracted |  |  |
| свети петър | uncontracted |  |  |
| сиколска река | uncontracted |  |  |
| стоикин дол | uncontracted |  |  |
| студена вода | uncontracted |  |  |
| студени дол | uncontracted |  |  |
| тимок | uncontracted |  |  |
| тополовец | uncontracted |  |  |
| чичилска | uncontracted |  |  |
| чубранска река | uncontracted |  |  |
| јасеничка река | uncontracted |  |  |

### Celulă 43.9-44.4N, 23.0-23.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| baboia | present | AJVPS DOLJ |  |
| balasan | present | AJVPS DOLJ |  |
| balta sarbilor | uncontracted |  |  |
| cetatuia | uncontracted |  |  |
| danube | uncontracted |  |  |
| drincea | present | AJVPS DOLJ |  |
| drincea 1 | uncontracted |  |  |
| dunarea дунав | uncontracted |  |  |
| paraul cilieni | present | AJVPS DOLJ | bbox_fix:lake:Bălăsan |
| paraul clielieni / balasan | uncontracted |  |  |
| raul baboia | present | AJVPS DOLJ |  |
| raul brabova | uncontracted |  |  |
| raul desnatui | present | AJVPS DOLJ |  |
| raul terpezita | present | AJVPS DOLJ |  |
| urdinita | uncontracted |  |  |

### Celulă 43.9-44.4N, 23.5-24.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| amaradia | present | AJVPS GORJ |  |
| baboia | present | AJVPS DOLJ |  |
| balacasanca | uncontracted |  |  |
| baldal | uncontracted |  |  |
| brancoveanca | uncontracted |  |  |
| brestuica | uncontracted |  |  |
| buzat | uncontracted |  |  |
| ciliboaica | uncontracted |  |  |
| danube | uncontracted |  |  |
| desnatui | present | AJVPS DOLJ |  |
| gabru | uncontracted |  |  |
| gioroc | uncontracted |  |  |
| jiet | present | AJVPS DOLJ |  |
| jiu | present | AJVPS GORJ |  |
| langa | uncontracted |  |  |
| lazu | uncontracted |  |  |
| leul | uncontracted |  |  |
| meretel | uncontracted |  |  |
| portaresti | uncontracted |  |  |
| raul brabova | uncontracted |  |  |
| raul desnatui | present | AJVPS DOLJ |  |
| raul terpezita | present | AJVPS DOLJ |  |
| raznic | uncontracted |  |  |
| tejac | uncontracted |  |  |
| terpezita | present | AJVPS DOLJ |  |
| teslui | present | AJVPS DOLJ |  |
| ulm | uncontracted |  |  |
| ungureni | uncontracted |  |  |
| urdinita | uncontracted |  |  |
| valea alba | uncontracted |  |  |
| valea bisericii | uncontracted |  |  |
| valea manastirii | uncontracted |  |  |
| valea preajba | present | AJVPS DOLJ | audit_match:override |
| valea predestilor | uncontracted |  |  |
| valea rea | uncontracted |  |  |
| valea sarpelui | uncontracted |  |  |
| vlasca | uncontracted |  |  |

### Celulă 43.9-44.4N, 24.0-24.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| balta dascalului | uncontracted |  |  |
| bobu | uncontracted |  |  |
| brancoveanca | uncontracted |  |  |
| crusovul | uncontracted |  |  |
| danube | uncontracted |  |  |
| darjov | present | AJVPS OLT |  |
| geamartalui | present | AJVPS OLT |  |
| gengea | uncontracted |  |  |
| gioroc | uncontracted |  |  |
| gologan | uncontracted |  |  |
| olt | present | AJVPS OLT |  |
| oltet | present | AJVPS OLT |  |
| oltisor | uncontracted |  |  |
| pararul rosu | uncontracted |  |  |
| paraul cinculeasa | uncontracted |  |  |
| paraul crusovul | uncontracted |  |  |
| paraul darjov | present | AJVPS OLT |  |
| paraul gologanul | uncontracted |  |  |
| paraul milcov | uncontracted |  |  |
| paraul oboga | uncontracted |  |  |
| paraul vladila | uncontracted |  |  |
| raul barlui | uncontracted |  |  |
| raul ciocarlia | uncontracted |  |  |
| raul crusov | uncontracted |  |  |
| raul darjov | present | AJVPS OLT |  |
| raul deveselu | uncontracted |  |  |
| raul gologanul | uncontracted |  |  |
| raul iminog | uncontracted |  |  |
| raul miloveanu | uncontracted |  |  |
| raul redea | uncontracted |  |  |
| raul suhatul | uncontracted |  |  |
| raul teslui | present | AJVPS DOLJ |  |
| raul vladila | uncontracted |  |  |
| redisoara | uncontracted |  |  |
| suhat | uncontracted |  |  |
| teslui | present | AJVPS DOLJ |  |
| ungureni | uncontracted |  |  |
| vaslui | uncontracted |  |  |
| voineasa mare | uncontracted |  |  |
| voineasa mica | uncontracted |  |  |

### Celulă 43.9-44.4N, 24.5-25.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bratcov | uncontracted |  |  |
| calmatui | present | AJVPS TELEORMAN | anpa_map:sweep:calmatui |
| calmatuiul sec | uncontracted |  |  |
| danube | uncontracted |  |  |
| deviere paraul tecuci | uncontracted |  |  |
| gologan | uncontracted |  |  |
| iminog | uncontracted |  |  |
| olt | present | AJVPS OLT |  |
| paraul burdea | uncontracted |  |  |
| paraul gologanul | uncontracted |  |  |
| paraul tecuci | uncontracted |  |  |
| paraul zambreasca | uncontracted |  |  |
| raul calmatui | present | AJVPS TELEORMAN | anpa_map:sweep:calmatui |
| raul cleja | uncontracted |  |  |
| raul cotmeana | uncontracted |  |  |
| raul dorofei | uncontracted |  |  |
| raul gologanul | uncontracted |  |  |
| raul iminog | uncontracted |  |  |
| raul redea | uncontracted |  |  |
| raul urlui | present | AJVPS TELEORMAN |  |
| raul vedea | present | AJVPS TELEORMAN | multiway_chain |
| raul vladila | uncontracted |  |  |
| redisoara | uncontracted |  |  |
| sai | uncontracted |  |  |
| sodol | uncontracted |  |  |
| urlui | present | AJVPS TELEORMAN |  |
| valea bungetului | uncontracted |  |  |
| valea dracsenulului | uncontracted |  |  |
| vedea | present | AJVPS TELEORMAN | multiway_chain |

### Celulă 43.9-44.4N, 25.0-25.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bratcov | uncontracted |  |  |
| burnaia | uncontracted |  |  |
| calmatui | present | AJVPS TELEORMAN | anpa_map:sweep:calmatui |
| danube | uncontracted |  |  |
| paraul burdea | uncontracted |  |  |
| paraul cainelui | uncontracted |  |  |
| paraul zambreasca | uncontracted |  |  |
| raul cainelui | uncontracted |  |  |
| raul clanita | uncontracted |  |  |
| raul milcovat | uncontracted |  |  |
| raul teleorman | present | AJVPS TELEORMAN |  |
| raul urlui | present | AJVPS TELEORMAN |  |
| raul vedea | present | AJVPS TELEORMAN | multiway_chain |
| teleorman | present | AJVPS TELEORMAN |  |
| tinoasa | uncontracted |  |  |
| urlui | present | AJVPS TELEORMAN |  |
| vedea | present | AJVPS TELEORMAN | multiway_chain |

### Celulă 43.9-44.4N, 25.5-26.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| arges | present | AJVPS DÂMBOVIȚA |  |
| botiza | present-hidden | Direcția Silvică Maramureș | romsilva_map |
| bratul smarda | uncontracted |  |  |
| calinstea | uncontracted |  |  |
| calnistea | present | AJVPS GIURGIU |  |
| ciorogarla | uncontracted |  |  |
| dambovnic | uncontracted |  |  |
| danube | uncontracted |  |  |
| ilfovat | uncontracted |  |  |
| ismar | uncontracted |  |  |
| neajlov | present | AJVPS GIURGIU | anpa_map:sweep:neajlov |
| raul dambovnic | uncontracted |  |  |
| raul glavacioc | uncontracted |  |  |
| raul gurbanu | uncontracted |  |  |
| raul milcovat | uncontracted |  |  |
| raul neajlov | present | AJVPS GIURGIU | anpa_map:sweep:neajlov |
| raul sabar | present | AJVPS DÂMBOVIȚA |  |
| sabar | present | AJVPS DÂMBOVIȚA |  |
| valea alba | uncontracted |  |  |
| valea lesilor | uncontracted |  |  |

### Celulă 43.9-44.4N, 26.0-26.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| arges | present | AJVPS DÂMBOVIȚA |  |
| bratul ara | uncontracted |  |  |
| bratul smarda | uncontracted |  |  |
| calnau | uncontracted |  |  |
| ciorogarla | uncontracted |  |  |
| cocioc | uncontracted |  |  |
| colentina | present | AVPS ACVILA |  |
| dambovita | present | AVPS ACVILA |  |
| danube | uncontracted |  |  |
| dunarea | uncontracted |  |  |
| dunarea дунав | uncontracted |  |  |
| neajlov | present | AJVPS GIURGIU | anpa_map:sweep:neajlov |
| pasarea | uncontracted |  |  |
| raul sabar | present | AJVPS DÂMBOVIȚA |  |
| sabar | present | AJVPS DÂMBOVIȚA |  |
| р сараджииска | uncontracted |  |  |
| сяновска река | uncontracted |  |  |

### Celulă 43.9-44.4N, 26.5-27.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| arges | present | AJVPS DÂMBOVIȚA |  |
| argova | uncontracted |  |  |
| bratul chilia | uncontracted |  |  |
| corata | uncontracted |  |  |
| cucuveanu | uncontracted |  |  |
| danube | uncontracted |  |  |
| dunarea дунав | uncontracted |  |  |
| mostistea | uncontracted |  |  |
| raul vanata | uncontracted |  |  |
| сенковец | uncontracted |  |  |
| сяновска река | uncontracted |  |  |
| тутраканска | uncontracted |  |  |
| царацар | uncontracted |  |  |

### Celulă 43.9-44.4N, 27.0-27.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| almalau | uncontracted |  |  |
| bratul borcea | uncontracted |  |  |
| danube | uncontracted |  |  |
| dunarea | uncontracted |  |  |
| dunarea bratul florica | uncontracted |  |  |
| dunarea bratul jianu | uncontracted |  |  |
| dunarea bratul pacuiululi | uncontracted |  |  |
| dunarea дунав | uncontracted |  |  |
| канагьол | uncontracted |  |  |
| сенковец | uncontracted |  |  |
| хърсовска | uncontracted |  |  |

### Celulă 43.9-44.4N, 27.5-28.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bratul bala | uncontracted |  |  |
| bratul borcea | uncontracted |  |  |
| bratul iepurasului | uncontracted |  |  |
| bratul rau | uncontracted |  |  |
| canal lebada | uncontracted |  |  |
| canaraua fetei | uncontracted |  |  |
| danube | uncontracted |  |  |
| dunarea | uncontracted |  |  |
| urluia | uncontracted |  |  |
| суха река | uncontracted |  |  |

### Celulă 43.9-44.4N, 28.0-28.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| agi cabul | uncontracted |  |  |
| cocos | uncontracted |  |  |
| danube | uncontracted |  |  |
| dunarea | uncontracted |  |  |
| urluia | uncontracted |  |  |
| valea silistii | uncontracted |  |  |
| valea siminocului | uncontracted |  |  |

### Celulă 43.9-44.4N, 28.5-29.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| casimcea | uncontracted |  |  |
| tasaul | uncontracted |  |  |
| valea agigea | uncontracted |  |  |
| valea cismelelor | uncontracted |  |  |
| valea pestera | uncontracted |  |  |
| valea silistii | uncontracted |  |  |

### Celulă 44.4-44.9N, 20.0-20.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| danube | uncontracted |  |  |
| duboki potk | uncontracted |  |  |
| авалски поток | uncontracted |  |  |
| балатон | uncontracted |  |  |
| барајевица | uncontracted |  |  |
| бањички поток | uncontracted |  |  |
| бела река | uncontracted |  |  |
| бељаница | uncontracted |  |  |
| венчанска река | uncontracted |  |  |
| визељ | uncontracted |  |  |
| витковица | uncontracted |  |  |
| влашки поток | uncontracted |  |  |
| враничина | uncontracted |  |  |
| гајин поток | uncontracted |  |  |
| губеревачка река | uncontracted |  |  |
| доњански поток | uncontracted |  |  |
| дрењачки поток | uncontracted |  |  |
| дунав | uncontracted |  |  |
| железничка река | uncontracted |  |  |
| змајевац | uncontracted |  |  |
| кадинац | uncontracted |  |  |
| каљави поток | uncontracted |  |  |
| кијевски поток | uncontracted |  |  |
| колубара | uncontracted |  |  |
| крушик | uncontracted |  |  |
| крља | uncontracted |  |  |
| кумодрашки поток | uncontracted |  |  |
| липице | uncontracted |  |  |
| лукавица | uncontracted |  |  |
| манастирине | uncontracted |  |  |
| марица | uncontracted |  |  |
| милошев поток | uncontracted |  |  |
| милојкин поток | uncontracted |  |  |
| мокролушки поток | uncontracted |  |  |
| остружничка река | uncontracted |  |  |
| паланачки поток | uncontracted |  |  |
| паригуз | uncontracted |  |  |
| париповац | uncontracted |  |  |
| пештан | uncontracted |  |  |
| пројања | uncontracted |  |  |
| раковички поток | uncontracted |  |  |
| рајаковац | uncontracted |  |  |
| рњаковац | uncontracted |  |  |
| сава | uncontracted |  |  |
| сава sava | uncontracted |  |  |
| сеона | uncontracted |  |  |
| сибничка река | uncontracted |  |  |
| сибовик | uncontracted |  |  |
| сикијевац | uncontracted |  |  |
| сикљевац | uncontracted |  |  |
| смољковац | uncontracted |  |  |
| сремачки поток | uncontracted |  |  |
| стара колубара | uncontracted |  |  |
| стојничка река | uncontracted |  |  |
| сува река | uncontracted |  |  |
| сурчиновица | uncontracted |  |  |
| суљин поток | uncontracted |  |  |
| тамнава | uncontracted |  |  |
| топчидерска река | uncontracted |  |  |
| турија | uncontracted |  |  |
| хајдучки поток | uncontracted |  |  |
| шиндраковац | uncontracted |  |  |
| јелезовац | uncontracted |  |  |

### Celulă 44.4-44.9N, 20.5-21.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| danube | uncontracted |  |  |
| kudrecki potok | uncontracted |  |  |
| leskovaca | uncontracted |  |  |
| timis | present | AJVPS TIMIȘ |  |
| авалски поток | uncontracted |  |  |
| алинац | uncontracted |  |  |
| бабин поток | uncontracted |  |  |
| бадрика | uncontracted |  |  |
| балабановац | uncontracted |  |  |
| баташев поток | uncontracted |  |  |
| бегаљичка река | uncontracted |  |  |
| бели поток | uncontracted |  |  |
| бесна река | uncontracted |  |  |
| болечица | uncontracted |  |  |
| брестовица | uncontracted |  |  |
| бубањ поток | uncontracted |  |  |
| бутуч | uncontracted |  |  |
| бучине | uncontracted |  |  |
| велика бара | uncontracted |  |  |
| врановац | uncontracted |  |  |
| врелски поток | uncontracted |  |  |
| врчинска река | uncontracted |  |  |
| вучачки поток | uncontracted |  |  |
| глеђевац | uncontracted |  |  |
| грочица | uncontracted |  |  |
| губеревачка река | uncontracted |  |  |
| дојник | uncontracted |  |  |
| доњи луг | uncontracted |  |  |
| дрењак | uncontracted |  |  |
| дубока долина | uncontracted |  |  |
| дубочај | uncontracted |  |  |
| дунав | uncontracted |  |  |
| дућевац | uncontracted |  |  |
| завојничка река | uncontracted |  |  |
| зубанска река | uncontracted |  |  |
| каловита | uncontracted |  |  |
| калуђерачки поток | uncontracted |  |  |
| камена вода | uncontracted |  |  |
| караулски поток | uncontracted |  |  |
| кастељан | uncontracted |  |  |
| кленићки поток | uncontracted |  |  |
| кленовац | uncontracted |  |  |
| кокорин | uncontracted |  |  |
| коњевац | uncontracted |  |  |
| коњска река | uncontracted |  |  |
| краљевац | uncontracted |  |  |
| кумодрашки поток | uncontracted |  |  |
| куса јаруга | uncontracted |  |  |
| липски поток | uncontracted |  |  |
| луг | uncontracted |  |  |
| мале воде | uncontracted |  |  |
| мали луг | uncontracted |  |  |
| манастирски поток | uncontracted |  |  |
| микуљски поток | uncontracted |  |  |
| милатовица | uncontracted |  |  |
| милошев поток | uncontracted |  |  |
| миријевски поток | uncontracted |  |  |
| млакачки поток | uncontracted |  |  |
| мокролушки поток | uncontracted |  |  |
| морава | uncontracted |  |  |
| надела | uncontracted |  |  |
| обзовље | uncontracted |  |  |
| паланачки поток | uncontracted |  |  |
| плавиначки поток | uncontracted |  |  |
| поток | uncontracted |  |  |
| поњавица | uncontracted |  |  |
| пречица | uncontracted |  |  |
| раковички поток | uncontracted |  |  |
| раља | uncontracted |  |  |
| рибник | uncontracted |  |  |
| риј | uncontracted |  |  |
| савушница | uncontracted |  |  |
| саставци | uncontracted |  |  |
| серава | uncontracted |  |  |
| сибница | uncontracted |  |  |
| сленичар | uncontracted |  |  |
| смрдански поток | uncontracted |  |  |
| средњи бегеј | uncontracted |  |  |
| стара језава | uncontracted |  |  |
| стојничка река | uncontracted |  |  |
| тамиш | uncontracted |  |  |
| топчидерска река | uncontracted |  |  |
| трнава | uncontracted |  |  |
| турија | uncontracted |  |  |
| турчић | uncontracted |  |  |
| чергадин | uncontracted |  |  |
| јабланица | uncontracted |  |  |
| језава | uncontracted |  |  |
| јованов поток | uncontracted |  |  |

### Celulă 44.4-44.9N, 21.0-21.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| danube | uncontracted |  |  |
| divici | uncontracted |  |  |
| karas | uncontracted |  |  |
| leskovaca | uncontracted |  |  |
| nera | present | AJVPS CARAȘ-SEVERIN | audit_match:prefix |
| velika reka | uncontracted |  |  |
| бадрика | uncontracted |  |  |
| бобрешка река | uncontracted |  |  |
| велика бара | uncontracted |  |  |
| велика морава | uncontracted |  |  |
| велики поток | uncontracted |  |  |
| витовница | uncontracted |  |  |
| витовничка река | uncontracted |  |  |
| грабовачки поток | uncontracted |  |  |
| дабовачки поток | uncontracted |  |  |
| дунав | uncontracted |  |  |
| дунав/dunarea | uncontracted |  |  |
| заовачки поток | uncontracted |  |  |
| кисиљевачка река | uncontracted |  |  |
| коњска река | uncontracted |  |  |
| крак | uncontracted |  |  |
| краљевац | uncontracted |  |  |
| кршка река | uncontracted |  |  |
| личина јаруга | uncontracted |  |  |
| луг | uncontracted |  |  |
| луди поток | uncontracted |  |  |
| минин поток | uncontracted |  |  |
| млава | uncontracted |  |  |
| обршки поток | uncontracted |  |  |
| поток бресје | uncontracted |  |  |
| поток забелски виногради | uncontracted |  |  |
| поток звезда | uncontracted |  |  |
| поток кладањ | uncontracted |  |  |
| поток мореч | uncontracted |  |  |
| поток тулба | uncontracted |  |  |
| поњавица | uncontracted |  |  |
| сеоски поток | uncontracted |  |  |
| сојин поток | uncontracted |  |  |
| стари караш | uncontracted |  |  |
| старчевачки поток | uncontracted |  |  |
| трест | uncontracted |  |  |
| трстена | uncontracted |  |  |
| урвински поток | uncontracted |  |  |
| црвени поток | uncontracted |  |  |
| чачалички поток | uncontracted |  |  |
| четерешки поток | uncontracted |  |  |
| чокордин | uncontracted |  |  |
| шапински поток | uncontracted |  |  |
| шљивовачки поток | uncontracted |  |  |
| јаруга | uncontracted |  |  |
| језава | uncontracted |  |  |
| југовачки поток | uncontracted |  |  |

### Celulă 44.4-44.9N, 21.5-22.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| belobresca | uncontracted |  |  |
| berzasca | present | AP BANATUL |  |
| buceava | uncontracted |  |  |
| danube | uncontracted |  |  |
| gornea | uncontracted |  |  |
| haimeliug | uncontracted |  |  |
| liborajdina | uncontracted |  |  |
| meliugel | uncontracted |  |  |
| moceris | uncontracted |  |  |
| nera | present | AJVPS CARAȘ-SEVERIN | audit_match:prefix |
| ogasu mare | uncontracted |  |  |
| ogasul babei | uncontracted |  |  |
| ogasul cu raci | uncontracted |  |  |
| ogasul porcariului | uncontracted |  |  |
| ogasul porcului | uncontracted |  |  |
| ogasul rogozului | uncontracted |  |  |
| oravita | uncontracted |  |  |
| oulmu mic | uncontracted |  |  |
| padina seaca | uncontracted |  |  |
| paraul bresnic | uncontracted |  |  |
| paraul slatina | uncontracted |  |  |
| parvareca | uncontracted |  |  |
| pojejena | uncontracted |  |  |
| radimna | uncontracted |  |  |
| radovanu | uncontracted |  |  |
| susara | uncontracted |  |  |
| susca | uncontracted |  |  |
| ulmu mare | uncontracted |  |  |
| ungureanu | uncontracted |  |  |
| valea mare | present | CS HUNEDOARA |  |
| valea pojejena | uncontracted |  |  |
| valea rea | uncontracted |  |  |
| бобрешка река | uncontracted |  |  |
| бродица | uncontracted |  |  |
| брњичка река | uncontracted |  |  |
| буковска река | uncontracted |  |  |
| ваља кумаре | uncontracted |  |  |
| ваља лупјеску | uncontracted |  |  |
| ваља сака | uncontracted |  |  |
| ваљаре | uncontracted |  |  |
| велика албина | uncontracted |  |  |
| велика гложана | uncontracted |  |  |
| велика равна река | uncontracted |  |  |
| велика река | uncontracted |  |  |
| велика чезава | uncontracted |  |  |
| велики ујевац | uncontracted |  |  |
| вујин поток | uncontracted |  |  |
| гложана | uncontracted |  |  |
| грабешница | uncontracted |  |  |
| добранска река | uncontracted |  |  |
| дунав/dunarea | uncontracted |  |  |
| железник | uncontracted |  |  |
| кисела вода | uncontracted |  |  |
| кожица | uncontracted |  |  |
| комша | uncontracted |  |  |
| кршка река | uncontracted |  |  |
| кучајнска река | uncontracted |  |  |
| кључата | uncontracted |  |  |
| лесковачки поток | uncontracted |  |  |
| мала албина | uncontracted |  |  |
| мала гложана | uncontracted |  |  |
| мала равна река | uncontracted |  |  |
| мала река | uncontracted |  |  |
| мала чезава | uncontracted |  |  |
| мали пек | uncontracted |  |  |
| мали ујевац | uncontracted |  |  |
| мелничка река | uncontracted |  |  |
| паскова река | uncontracted |  |  |
| пек | uncontracted |  |  |
| пошец | uncontracted |  |  |
| раденка | uncontracted |  |  |
| рађина река | uncontracted |  |  |
| рајкова река | uncontracted |  |  |
| речица | uncontracted |  |  |
| селиште | uncontracted |  |  |
| сува река | uncontracted |  |  |
| туманска река | uncontracted |  |  |
| ујевац | uncontracted |  |  |
| чезава | uncontracted |  |  |
| чубера | uncontracted |  |  |

### Celulă 44.4-44.9N, 22.0-22.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| ada kaleh | uncontracted |  |  |
| alion | uncontracted |  |  |
| barza | uncontracted |  |  |
| belareca | uncontracted |  |  |
| berzasca | present | AP BANATUL |  |
| biger | uncontracted |  |  |
| blederijska reka | uncontracted |  |  |
| bostita mare | uncontracted |  |  |
| bostita mica | uncontracted |  |  |
| cerna | present | Direcția Silvică Mehedinți | sweep:hidden:group-shares-course |
| crivita | uncontracted |  |  |
| danube | uncontracted |  |  |
| dunarea | uncontracted |  |  |
| dunav/dunarea | uncontracted |  |  |
| eselinita | uncontracted |  |  |
| garbovat | uncontracted |  |  |
| glaucina | uncontracted |  |  |
| graniceri | uncontracted |  |  |
| ilisova | uncontracted |  |  |
| iutii | uncontracted |  |  |
| jupalnic | uncontracted |  |  |
| kazanski potok | uncontracted |  |  |
| kolican potok | uncontracted |  |  |
| labalon | uncontracted |  |  |
| liubotina | uncontracted |  |  |
| mala | uncontracted |  |  |
| mala recica | uncontracted |  |  |
| mraconia | uncontracted |  |  |
| ogradena | uncontracted |  |  |
| oreva | uncontracted |  |  |
| plavisevita | uncontracted |  |  |
| ponicova | uncontracted |  |  |
| povalina | uncontracted |  |  |
| prigor | uncontracted |  |  |
| pripor | uncontracted |  |  |
| racovat | uncontracted |  |  |
| radu | uncontracted |  |  |
| raul bahna | present | AJVPS BOTOȘANI |  |
| raul bosneagului | uncontracted |  |  |
| raul cerna | present | Direcția Silvică Mehedinți | sweep:hidden:group-shares-course |
| raul eroilor | uncontracted |  |  |
| raul palangei | uncontracted |  |  |
| raul tarziului | uncontracted |  |  |
| raul ursoanei | uncontracted |  |  |
| recita mare | uncontracted |  |  |
| satului | uncontracted |  |  |
| sirina | uncontracted |  |  |
| slatinicul mare | uncontracted |  |  |
| slatinicul mic | uncontracted |  |  |
| stariste | uncontracted |  |  |
| svinita | uncontracted |  |  |
| tarovat | uncontracted |  |  |
| tisovita | uncontracted |  |  |
| topolova | uncontracted |  |  |
| tufari | uncontracted |  |  |
| valea ghergheleului | uncontracted |  |  |
| valea lui stan | uncontracted |  |  |
| valea rosie | uncontracted |  |  |
| valea rudariei | uncontracted |  |  |
| varciorova | uncontracted |  |  |
| velika recica | uncontracted |  |  |
| vizurin | uncontracted |  |  |
| vodita | uncontracted |  |  |
| бледерија | uncontracted |  |  |
| бољетинска река | uncontracted |  |  |
| буљевица | uncontracted |  |  |
| варошки поток | uncontracted |  |  |
| ватин поток | uncontracted |  |  |
| ваља маре | uncontracted |  |  |
| велика близна река | uncontracted |  |  |
| велика градашница | uncontracted |  |  |
| велика пештера | uncontracted |  |  |
| велика равна река | uncontracted |  |  |
| велика река | uncontracted |  |  |
| голубињска река | uncontracted |  |  |
| грабешница | uncontracted |  |  |
| гробљански поток | uncontracted |  |  |
| дунав/dunarea | uncontracted |  |  |
| златица | uncontracted |  |  |
| казански поток | uncontracted |  |  |
| каменичка река | uncontracted |  |  |
| кашајна | uncontracted |  |  |
| корешин поток | uncontracted |  |  |
| косовица | uncontracted |  |  |
| мала близна река | uncontracted |  |  |
| мала градашница | uncontracted |  |  |
| мала пештера | uncontracted |  |  |
| мала равна река | uncontracted |  |  |
| мала река | uncontracted |  |  |
| манастирички поток | uncontracted |  |  |
| мирочки поток | uncontracted |  |  |
| мосна | uncontracted |  |  |
| мртвица | uncontracted |  |  |
| недељковац | uncontracted |  |  |
| папреница | uncontracted |  |  |
| подвршка река | uncontracted |  |  |
| поречка река | uncontracted |  |  |
| равна река | uncontracted |  |  |
| ратарова река | uncontracted |  |  |
| река | uncontracted |  |  |
| слатинска река | uncontracted |  |  |
| суваја | uncontracted |  |  |
| ташуанска река | uncontracted |  |  |
| црквени поток | uncontracted |  |  |
| чеиш | uncontracted |  |  |
| ђеврински поток | uncontracted |  |  |

### Celulă 44.4-44.9N, 22.5-23.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| blahnita | present | AJVPS GORJ |  |
| borovat | uncontracted |  |  |
| carabasita | uncontracted |  |  |
| carbunari | uncontracted |  |  |
| clisevat | uncontracted |  |  |
| cosustea | uncontracted |  |  |
| cosustita | uncontracted |  |  |
| crainici | uncontracted |  |  |
| crihala | uncontracted |  |  |
| danube | uncontracted |  |  |
| drincea 1 | uncontracted |  |  |
| dunarea | uncontracted |  |  |
| dunav/dunarea | uncontracted |  |  |
| gradesnita | uncontracted |  |  |
| grasca | uncontracted |  |  |
| jidostita | uncontracted |  |  |
| linisca | uncontracted |  |  |
| luchita mare | uncontracted |  |  |
| luchita mica | uncontracted |  |  |
| mosu | uncontracted |  |  |
| motru | present | AJVPS GORJ |  |
| neagonea | uncontracted |  |  |
| ogasu sec | uncontracted |  |  |
| padina baii | uncontracted |  |  |
| padina carligului | uncontracted |  |  |
| padina ciresului | uncontracted |  |  |
| padina crucii | uncontracted |  |  |
| padina gardului | uncontracted |  |  |
| padina mica | uncontracted |  |  |
| padina scarpiei | uncontracted |  |  |
| paraul baran | uncontracted |  |  |
| paraul blahnita | present | AJVPS GORJ |  |
| paraul lumasului | uncontracted |  |  |
| paraul orevita | uncontracted |  |  |
| paraul poroinita | uncontracted |  |  |
| paraul valea erghevita | uncontracted |  |  |
| paraul valea larga | uncontracted |  |  |
| plesuva | uncontracted |  |  |
| raul bahna | present | AJVPS BOTOȘANI |  |
| raul dunarea veche | uncontracted |  |  |
| raul husnita | uncontracted |  |  |
| slatinicul mare | uncontracted |  |  |
| slatinicul mic | uncontracted |  |  |
| sovarna | uncontracted |  |  |
| stirbita | uncontracted |  |  |
| stiubei | uncontracted |  |  |
| susita | present | AJVPS GORJ |  |
| topolnita | uncontracted |  |  |
| topolova | uncontracted |  |  |
| ungureanu | uncontracted |  |  |
| valea garanei | uncontracted |  |  |
| valea ghergheleului | uncontracted |  |  |
| valea nevatului | uncontracted |  |  |
| valea popii | uncontracted |  |  |
| valea prihodului | uncontracted |  |  |
| valea rea | uncontracted |  |  |
| virulului | uncontracted |  |  |
| virulului mare | uncontracted |  |  |
| virulului mic | uncontracted |  |  |
| vodita | uncontracted |  |  |
| бузијански поток | uncontracted |  |  |
| ваља маре | uncontracted |  |  |
| ваља морулуј | uncontracted |  |  |
| ваља сатулуј | uncontracted |  |  |
| грабовачки поток | uncontracted |  |  |
| каменичка река | uncontracted |  |  |
| корновац | uncontracted |  |  |
| косовица | uncontracted |  |  |
| манастирички поток | uncontracted |  |  |
| матка | uncontracted |  |  |
| огаш сатулуј | uncontracted |  |  |
| огашу гадувана | uncontracted |  |  |
| подвршка река | uncontracted |  |  |
| речица | uncontracted |  |  |
| јакомир | uncontracted |  |  |

### Celulă 44.4-44.9N, 23.0-23.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| argetoaia | uncontracted |  |  |
| balta | uncontracted |  |  |
| cosustea | uncontracted |  |  |
| danube | uncontracted |  |  |
| drincea 1 | uncontracted |  |  |
| garcotin | uncontracted |  |  |
| jiu | present | AJVPS GORJ |  |
| meretel | uncontracted |  |  |
| motru | present | AJVPS GORJ |  |
| paraul talapan | uncontracted |  |  |
| raul argetoaia | uncontracted |  |  |
| raul cotoroaia | uncontracted |  |  |
| raul gilort | present | AJVPS GORJ |  |
| raul husnita | uncontracted |  |  |
| raul jiu | present | AJVPS GORJ |  |
| raznic | uncontracted |  |  |
| tantar | uncontracted |  |  |
| urdinita | uncontracted |  |  |

### Celulă 44.4-44.9N, 23.5-24.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| amaradia | present | AJVPS GORJ |  |
| cerna | present | AJVPS VÂLCEA |  |
| danube | uncontracted |  |  |
| geamartalui | present | AJVPS OLT |  |
| jiu | present | AJVPS GORJ |  |
| meretel | uncontracted |  |  |
| oltet | present | AJVPS OLT |  |
| paraul horezu | uncontracted |  |  |
| pesteana | uncontracted |  |  |
| plosca | uncontracted |  |  |
| raul argetoaia | uncontracted |  |  |
| raul gilort | present | AJVPS GORJ |  |
| raznic | uncontracted |  |  |
| sasa | present | AJVPS VÂLCEA |  |
| ungureni | uncontracted |  |  |
| valea satului | uncontracted |  |  |

### Celulă 44.4-44.9N, 24.0-24.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| beica | present | AJVPS MUREȘ |  |
| cerna | present | AJVPS VÂLCEA |  |
| cernisoara | present | Direcția Silvică Caraș-Severin | romsilva_map:exact |
| cungra | uncontracted |  |  |
| cungrea mica | uncontracted |  |  |
| dalga | uncontracted |  |  |
| danube | uncontracted |  |  |
| darjov | present | AJVPS OLT |  |
| geamartalui | present | AJVPS OLT |  |
| lunget | uncontracted |  |  |
| marzanu | uncontracted |  |  |
| nisipoasa | uncontracted |  |  |
| olt | present | AJVPS OLT |  |
| oltet | present | AJVPS OLT |  |
| paraul aninoasa | uncontracted |  |  |
| paraul chiara | uncontracted |  |  |
| paraul milcov | uncontracted |  |  |
| paraul oboga | uncontracted |  |  |
| paraul plapcea mare | uncontracted |  |  |
| paraul turia | uncontracted |  |  |
| paraului aninoasa | uncontracted |  |  |
| pesceana | uncontracted |  |  |
| plapcea mare | uncontracted |  |  |
| raul barlui | uncontracted |  |  |
| raul cargrea | uncontracted |  |  |
| raul cungrea | uncontracted |  |  |
| raul darjov | present | AJVPS OLT |  |
| raul lungot | uncontracted |  |  |
| raul oltisor | uncontracted |  |  |
| raul streangul | uncontracted |  |  |
| raul strehareti | uncontracted |  |  |
| raul surdui | uncontracted |  |  |
| sopot | uncontracted |  |  |
| teslui | present | AJVPS DOLJ |  |
| trepteanca | uncontracted |  |  |
| ursanca | uncontracted |  |  |
| valea fatului | uncontracted |  |  |
| vaslui | uncontracted |  |  |

### Celulă 44.4-44.9N, 24.5-25.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| arges | present | AJVPS DÂMBOVIȚA |  |
| bascov | uncontracted |  |  |
| berci | uncontracted |  |  |
| cotmeana | uncontracted |  |  |
| dambovnic | uncontracted |  |  |
| danube | uncontracted |  |  |
| izvorani | uncontracted |  |  |
| neajlov | present | AJVPS DÂMBOVIȚA |  |
| negrisoara | uncontracted |  |  |
| olt | present | AJVPS OLT |  |
| paraul chiara | uncontracted |  |  |
| paraul geamana | present | AJPS Brașov |  |
| paraul mogosesti | uncontracted |  |  |
| paraul plapcea mare | uncontracted |  |  |
| paraul plapcea mica | uncontracted |  |  |
| paraul stufu | uncontracted |  |  |
| paraul teius | uncontracted |  |  |
| plapcea | uncontracted |  |  |
| plapcea mare | uncontracted |  |  |
| plapcea mica | uncontracted |  |  |
| rata | uncontracted |  |  |
| raul cioraca | uncontracted |  |  |
| raul cotmeana | uncontracted |  |  |
| raul dambovnic | uncontracted |  |  |
| raul doamnei | present | AJVPS ARGEȘ | audit_match:prefix |
| raul dorofei | uncontracted |  |  |
| raul iminog | uncontracted |  |  |
| raul mares | uncontracted |  |  |
| raul marghia | uncontracted |  |  |
| raul neajlov | present | AJVPS DÂMBOVIȚA |  |
| raul plapcea | uncontracted |  |  |
| raul teleorman | present | AJVPS TELEORMAN |  |
| raul vedea | present | AJVPS TELEORMAN | multiway_chain |
| raul vedita | uncontracted |  |  |
| scroafele | uncontracted |  |  |
| teleorman | present | AJVPS TELEORMAN |  |
| ulmul mare | uncontracted |  |  |
| valea mare | present | AVPS MIERCUREA-CIUC |  |
| valea zeama rece | uncontracted |  |  |
| valeni | uncontracted |  |  |
| vartej | uncontracted |  |  |
| vedea | present | AJVPS TELEORMAN | multiway_chain |

### Celulă 44.4-44.9N, 25.0-25.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| arges | present | AJVPS DÂMBOVIȚA |  |
| cacova | uncontracted |  |  |
| carcinov | uncontracted |  |  |
| dambovita | present | AVPS ACVILA |  |
| dambovnic | uncontracted |  |  |
| danube | uncontracted |  |  |
| neajlov | present | AJVPS DÂMBOVIȚA |  |
| olt | present | AJVPS OLT |  |
| paraul cainelui | uncontracted |  |  |
| raul dambovnic | uncontracted |  |  |
| raul ilfov | present | AJVPS DÂMBOVIȚA |  |
| raul mozacu | uncontracted |  |  |
| raul neajlov | present | AJVPS DÂMBOVIȚA |  |
| teleorman | present | AJVPS TELEORMAN |  |

### Celulă 44.4-44.9N, 25.5-26.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| arges | present | AJVPS DÂMBOVIȚA |  |
| baranga | uncontracted |  |  |
| ciorogarla | uncontracted |  |  |
| colentina | present | AVPS ACVILA |  |
| crevedia | uncontracted |  |  |
| cricov | present | AJVPS DÂMBOVIȚA |  |
| cricovul dulce | present | AJVPS PRAHOVA |  |
| dambovita | present | AVPS ACVILA |  |
| danube | uncontracted |  |  |
| ialomita | present | AVPS IALOMIȚA |  |
| ilfov | present | AJVPS DÂMBOVIȚA |  |
| ilfovat | uncontracted |  |  |
| neajlov | present | AJVPS DÂMBOVIȚA |  |
| paraul leaota | uncontracted |  |  |
| prahova | present | AJVPS PRAHOVA | audit_match:prefix |
| provita | uncontracted |  |  |
| raul dambovnic | uncontracted |  |  |
| raul ilfov | present | AJVPS DÂMBOVIȚA |  |
| raul racovita | uncontracted |  |  |
| raul slanic | uncontracted |  |  |
| sabar | present | AJVPS DÂMBOVIȚA |  |
| valea ilfovului | uncontracted |  |  |

### Celulă 44.4-44.9N, 26.0-26.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| arges | present | AJVPS DÂMBOVIȚA |  |
| belciugatele | uncontracted |  |  |
| cociovalistea | uncontracted |  |  |
| colceag | uncontracted |  |  |
| colentina | present | AVPS ACVILA |  |
| cricovul sarat | present | AJVPS PRAHOVA |  |
| dambovita | present | AVPS ACVILA |  |
| dambul | uncontracted |  |  |
| ecluza | uncontracted |  |  |
| ghighiul | uncontracted |  |  |
| gruiu | uncontracted |  |  |
| ialomita | present | AVPS IALOMIȚA |  |
| mostistea | uncontracted |  |  |
| pasarea | uncontracted |  |  |
| poenari | uncontracted |  |  |
| poienari | uncontracted |  |  |
| prahova | present | AJVPS PRAHOVA | audit_match:prefix |
| raul cricovul sarat | present | AJVPS PRAHOVA |  |
| raul ghighiu | uncontracted |  |  |
| tanganu | uncontracted |  |  |
| teleajen | present | AJVPS PRAHOVA | audit_match:prefix |
| vlasia | uncontracted |  |  |

### Celulă 44.4-44.9N, 26.5-27.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| argova | uncontracted |  |  |
| belciugatele | uncontracted |  |  |
| colceag | uncontracted |  |  |
| cucuveanu | uncontracted |  |  |
| ghighiul | uncontracted |  |  |
| ghiula | uncontracted |  |  |
| ialomita | present | AVPS IALOMIȚA |  |
| mostistea | uncontracted |  |  |
| profira | uncontracted |  |  |
| raul banciu | uncontracted |  |  |
| raul valea lui ilie | uncontracted |  |  |
| raul vanata | uncontracted |  |  |
| sarata | present | AJVPS BOTOȘANI |  |
| sulimanu | uncontracted |  |  |

### Celulă 44.4-44.9N, 27.0-27.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| ialomita | present | AVPS IALOMIȚA |  |

### Celulă 44.4-44.9N, 27.5-28.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bratul borcea | uncontracted |  |  |
| bratul macin | uncontracted |  |  |
| bratul valciu | uncontracted |  |  |
| danube | uncontracted |  |  |
| dunarea | uncontracted |  |  |
| dunarea bratul alionte | uncontracted |  |  |
| dunarea bratul cracanel | uncontracted |  |  |
| dunarea bratul manusoia | uncontracted |  |  |
| ialomita | present | AVPS IALOMIȚA |  |
| privalul varsaturii | uncontracted |  |  |

### Celulă 44.4-44.9N, 28.0-28.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| agi cabul | uncontracted |  |  |
| bentu | uncontracted |  |  |
| bratul macin | uncontracted |  |  |
| cartal | uncontracted |  |  |
| casimcea | uncontracted |  |  |
| ciucurova | uncontracted |  |  |
| danube | uncontracted |  |  |
| dunarea | uncontracted |  |  |
| dunarea bratul alionte | uncontracted |  |  |
| dunarea bratul baban | uncontracted |  |  |
| hamangia | uncontracted |  |  |
| mahomencea | uncontracted |  |  |
| paraul fantana oilor | uncontracted |  |  |
| paraul ghelengic | uncontracted |  |  |
| topolog | present | AJVPS VÂLCEA |  |
| veriga | present | AJVPS BRĂILA | sweep:hidden:veriga |
| visterna | uncontracted |  |  |

### Celulă 44.4-44.9N, 28.5-29.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| carabalac | uncontracted |  |  |
| casimcea | uncontracted |  |  |
| ceamurlia | uncontracted |  |  |
| ciucurova | uncontracted |  |  |
| giurmes | uncontracted |  |  |
| hagiu | uncontracted |  |  |
| hamangia | uncontracted |  |  |
| pandelea | uncontracted |  |  |
| solojanu | uncontracted |  |  |
| tabana | uncontracted |  |  |
| tasaul | uncontracted |  |  |

### Celulă 44.4-44.9N, 29.5-30.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bratul sfantu gheorghe | uncontracted |  |  |
| danube | uncontracted |  |  |
| dunarea | uncontracted |  |  |

### Celulă 44.9-45.4N, 20.0-20.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bega | present | AJVPS TIMIȘ |  |
| danube | uncontracted |  |  |
| timis | present | AJVPS TIMIȘ |  |
| tisza | uncontracted |  |  |
| балатон | uncontracted |  |  |
| бегеј | uncontracted |  |  |
| будовар | uncontracted |  |  |
| врбица | uncontracted |  |  |
| дунав | uncontracted |  |  |
| комаревац | uncontracted |  |  |
| лочки канал | uncontracted |  |  |
| сава sava | uncontracted |  |  |
| стари бегеј | uncontracted |  |  |
| тамиш | uncontracted |  |  |
| тиса | uncontracted |  |  |
| тукош | uncontracted |  |  |
| јегричка | uncontracted |  |  |

### Celulă 44.9-45.4N, 20.5-21.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| barzava | present | AJVPS TIMIȘ |  |
| birda veche | uncontracted |  |  |
| danube | uncontracted |  |  |
| lanca | uncontracted |  |  |
| lanka | uncontracted |  |  |
| timis | present | AJVPS TIMIȘ |  |
| бирда | uncontracted |  |  |
| ланка | uncontracted |  |  |
| морава | uncontracted |  |  |
| надела | uncontracted |  |  |
| сибница | uncontracted |  |  |
| стара брзава | uncontracted |  |  |
| стари тамиш | uncontracted |  |  |
| тамиш | uncontracted |  |  |
| тукош | uncontracted |  |  |

### Celulă 44.9-45.4N, 21.0-21.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| barzava | present | AJVPS TIMIȘ |  |
| canalul barzava | present | AJVPS TIMIȘ |  |
| caras | uncontracted |  |  |
| danube | uncontracted |  |  |
| karas | uncontracted |  |  |
| lanca | uncontracted |  |  |
| lanka | uncontracted |  |  |
| moravita | present | AJVPS TIMIȘ |  |
| paraul ciclova | uncontracted |  |  |
| semnita | present | AJVPS TIMIȘ |  |
| vicinic | uncontracted |  |  |
| ваља маре | uncontracted |  |  |
| ваља мика | uncontracted |  |  |
| вичиник | uncontracted |  |  |
| врела | uncontracted |  |  |
| гузајна | uncontracted |  |  |
| долина | uncontracted |  |  |
| караш | uncontracted |  |  |
| кевериш | uncontracted |  |  |
| луг | uncontracted |  |  |
| мали караш | uncontracted |  |  |
| месић | uncontracted |  |  |
| моравица | uncontracted |  |  |
| огаш | uncontracted |  |  |
| огаши маћеј | uncontracted |  |  |
| попова бара | uncontracted |  |  |
| рушњачки поток | uncontracted |  |  |
| стара брзава | uncontracted |  |  |
| стари караш | uncontracted |  |  |
| фабијански поток | uncontracted |  |  |
| физеш | uncontracted |  |  |
| јаруга | uncontracted |  |  |

### Celulă 44.9-45.4N, 21.5-22.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| alibeg | uncontracted |  |  |
| barzava | present | AJVPS TIMIȘ |  |
| barzavita | uncontracted |  |  |
| berzovita | uncontracted |  |  |
| beu | uncontracted |  |  |
| bigar | uncontracted |  |  |
| buhui | present | Direcția Silvică Caraș-Severin |  |
| caras | uncontracted |  |  |
| clocotici | uncontracted |  |  |
| crainic | uncontracted |  |  |
| crivaia mare | uncontracted |  |  |
| crivaia mica | uncontracted |  |  |
| danube | uncontracted |  |  |
| dognecea | present | AP BANATUL |  |
| doman | uncontracted |  |  |
| ferendia | uncontracted |  |  |
| fizes | present | AJPS Cluj |  |
| garliste | uncontracted |  |  |
| gelug | uncontracted |  |  |
| karas | uncontracted |  |  |
| lindina | uncontracted |  |  |
| lisava | uncontracted |  |  |
| minis | uncontracted |  |  |
| moravita | present | AJVPS TIMIȘ |  |
| nera | present | AJVPS CARAȘ-SEVERIN | audit_match:prefix |
| nermed | uncontracted |  |  |
| oravita | uncontracted |  |  |
| orese | uncontracted |  |  |
| padina seaca | uncontracted |  |  |
| parau ciornovat | uncontracted |  |  |
| parau garliste | uncontracted |  |  |
| paraul ciclova | uncontracted |  |  |
| paraul fizes | present | AJPS Cluj |  |
| paraul izvorul molidului | uncontracted |  |  |
| paraul toplita | present | AV VIDA SURDUCEL DOBREȘTI |  |
| poganis | present | AJVPS TIMIȘ |  |
| poneasca | uncontracted |  |  |
| ponicova | uncontracted |  |  |
| rachitova | uncontracted |  |  |
| rafnic | uncontracted |  |  |
| raul alb | present | AJVPS CARAȘ-SEVERIN | multiway_chain |
| sareniac | uncontracted |  |  |
| stircovat | uncontracted |  |  |
| stredneg | uncontracted |  |  |
| sumbrac | uncontracted |  |  |
| taria mare | present | Direcția Silvică Caraș-Severin | bbox_fix:lake:Taria Mare |
| tau | present | Direcția Silvică Alba | romsilva_map:exact |
| terova | uncontracted |  |  |
| timis | present | AJVPS TIMIȘ |  |
| valea aron | uncontracted |  |  |
| valea comarnic | uncontracted |  |  |
| valea marcus | uncontracted |  |  |
| valea rea | uncontracted |  |  |
| valea satului | uncontracted |  |  |
| valea simon si iuda | uncontracted |  |  |
| vicinic | uncontracted |  |  |
| vodnic | uncontracted |  |  |
| буканов поток | uncontracted |  |  |
| караш | uncontracted |  |  |
| луг | uncontracted |  |  |
| најдашки поток | uncontracted |  |  |
| шљиварски поток | uncontracted |  |  |

### Celulă 44.9-45.4N, 22.0-22.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| alibeg | uncontracted |  |  |
| barzava | present | AJVPS TIMIȘ |  |
| bedina | uncontracted |  |  |
| belareca | uncontracted |  |  |
| berzovita | uncontracted |  |  |
| boboroaia mare | uncontracted |  |  |
| cerna | present | Direcția Silvică Mehedinți | sweep:hidden:group-shares-course |
| crainic | uncontracted |  |  |
| crivaia mare | uncontracted |  |  |
| crivaia mica | uncontracted |  |  |
| cuntu | uncontracted |  |  |
| danube | uncontracted |  |  |
| gozna | present | Direcția Silvică Caraș-Severin | bbox_fix:lake:Lacul Gozna |
| goznuta | uncontracted |  |  |
| mehadica | uncontracted |  |  |
| minis | uncontracted |  |  |
| nera | present | AJVPS CARAȘ-SEVERIN | audit_match:prefix |
| ogasul negrilovat | uncontracted |  |  |
| olteana | uncontracted |  |  |
| paraul bailor mari | uncontracted |  |  |
| paraul brebu | uncontracted |  |  |
| paraul crivaia | uncontracted |  |  |
| paraul dignacea | uncontracted |  |  |
| paraul gradistei | uncontracted |  |  |
| paraul izvorul molidului | uncontracted |  |  |
| paraul negrana | uncontracted |  |  |
| paraul racovita | uncontracted |  |  |
| paraul rainea | uncontracted |  |  |
| paraul rece | uncontracted |  |  |
| paraul semenic | uncontracted |  |  |
| poganis | present | AJVPS TIMIȘ |  |
| prigor | uncontracted |  |  |
| ranica | uncontracted |  |  |
| raul alb | present | AJVPS CARAȘ-SEVERIN | multiway_chain |
| raul cerna | present | Direcția Silvică Mehedinți | sweep:hidden:group-shares-course |
| raul lung | present | AJVPS CARAȘ-SEVERIN | audit_match:exact |
| scorila | uncontracted |  |  |
| sebes | present | AJVPS ALBA |  |
| sebesel | uncontracted |  |  |
| sfragin | uncontracted |  |  |
| sipu | uncontracted |  |  |
| taria mare | present | Direcția Silvică Caraș-Severin | bbox_fix:lake:Taria Mare |
| tasna | uncontracted |  |  |
| timis | present | AJVPS TIMIȘ |  |
| valea craiului | uncontracted |  |  |
| valea de rugi | uncontracted |  |  |
| valea prisacina | uncontracted |  |  |
| valea rudariei | uncontracted |  |  |
| valsan | present | AJVPS ARGEȘ | audit_match:prefix |
| zlagna | uncontracted |  |  |

### Celulă 44.9-45.4N, 22.5-23.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| barbat | uncontracted |  |  |
| bistra marului | present | Direcția Silvică Caraș-Severin | romsilva_map:prefix |
| bistrita | present | AJVPS GORJ |  |
| boboroaia mare | uncontracted |  |  |
| borascu mare | present | Direcția Silvică Hunedoara | romsilva_map:prefix |
| borascu mic | present | Direcția Silvică Hunedoara | romsilva_map:prefix |
| brebina | uncontracted |  |  |
| bucura | present | Direcția Silvică Hunedoara |  |
| bucurusul mare | uncontracted |  |  |
| carbunele | uncontracted |  |  |
| carligu | uncontracted |  |  |
| cerna | present | Direcția Silvică Mehedinți | sweep:hidden:group-shares-course |
| cernisoara | present | Direcția Silvică Caraș-Severin | romsilva_map:exact |
| cioaca radesului | uncontracted |  |  |
| cosustea | uncontracted |  |  |
| crainici | uncontracted |  |  |
| danube | uncontracted |  |  |
| dobrun | uncontracted |  |  |
| francul | uncontracted |  |  |
| galbena de nord | uncontracted |  |  |
| galbena de sud | uncontracted |  |  |
| galesu | uncontracted |  |  |
| godeanu | uncontracted |  |  |
| iovanu | uncontracted |  |  |
| izvoru | uncontracted |  |  |
| izvorul gugu | uncontracted |  |  |
| izvorul morarului | uncontracted |  |  |
| jdimir | uncontracted |  |  |
| jiul de vest | present | Pro Pescar | bbox_fix:prefix |
| judele | uncontracted |  |  |
| judele mic | uncontracted |  |  |
| lapusnicu mic | uncontracted |  |  |
| lapusnicul mare | present | Direcția Silvică Hunedoara | romsilva_map:exact |
| mihocul | uncontracted |  |  |
| mocirliul | uncontracted |  |  |
| motru | present | AJVPS GORJ |  |
| motru sec | uncontracted |  |  |
| motrusor | uncontracted |  |  |
| obarsia | uncontracted |  |  |
| olanelul | uncontracted |  |  |
| olteana | uncontracted |  |  |
| orlea | present | AJVPS GORJ |  |
| paraul blojului | uncontracted |  |  |
| paraul bontica | uncontracted |  |  |
| paraul carnea | uncontracted |  |  |
| paraul craiova | uncontracted |  |  |
| paraul curmezisa | uncontracted |  |  |
| paraul dalei | uncontracted |  |  |
| paraul galbena | uncontracted |  |  |
| paraul gardomanu | uncontracted |  |  |
| paraul gropita | uncontracted |  |  |
| paraul inelet | uncontracted |  |  |
| paraul maneasa | uncontracted |  |  |
| paraul merila | uncontracted |  |  |
| paraul mitului | uncontracted |  |  |
| paraul morii | uncontracted |  |  |
| paraul naiba | uncontracted |  |  |
| paraul olanu | uncontracted |  |  |
| paraul rece | uncontracted |  |  |
| paraul scurtele | uncontracted |  |  |
| paraul scurtu | uncontracted |  |  |
| paraul ses | present | Direcția Silvică Hunedoara | romsilva_map:sweep:raul ses |
| paraul tapului | uncontracted |  |  |
| peceneaga | uncontracted |  |  |
| peleaga | present | Direcția Silvică Hunedoara | bbox_fix:lake:Peleaga |
| peleguta | uncontracted |  |  |
| pietrele | uncontracted |  |  |
| pocruia | uncontracted |  |  |
| prundu lancitei | uncontracted |  |  |
| radesu mare | uncontracted |  |  |
| radoteasa | uncontracted |  |  |
| raul bahna | present | AJVPS BOTOȘANI |  |
| raul cerna | present | Direcția Silvică Mehedinți | sweep:hidden:group-shares-course |
| raul mare | present | CS HUNEDOARA |  |
| raul ses | present | Direcția Silvică Hunedoara | romsilva_map:sweep:raul ses |
| raul tismana | present | ANPA - Ape Necontractate | bbox_fix:lake:Lacul De Acumulare Tismana |
| rovine | uncontracted |  |  |
| scarisoara | uncontracted |  |  |
| scarita | uncontracted |  |  |
| scheiul | uncontracted |  |  |
| scoaba retezatului | uncontracted |  |  |
| scocul urzicarilor | uncontracted |  |  |
| scorila | uncontracted |  |  |
| ses | present | Direcția Silvică Hunedoara | romsilva_map:sweep:raul ses |
| stana mare | uncontracted |  |  |
| stanisoara | uncontracted |  |  |
| stevia | present | Direcția Silvică Hunedoara | bbox_fix:lake:Ștevia |
| sucu | present | Direcția Silvică Caraș-Severin | romsilva_map:exact |
| suculetu | uncontracted |  |  |
| tasna | uncontracted |  |  |
| topolnita | uncontracted |  |  |
| tucila | uncontracted |  |  |
| valea carmazanului | uncontracted |  |  |
| valea cascadelor | uncontracted |  |  |
| valea gemenele | uncontracted |  |  |
| valea pietrele | uncontracted |  |  |
| valea popii | uncontracted |  |  |
| valea prisacina | uncontracted |  |  |
| valea rea | uncontracted |  |  |
| valereasca | uncontracted |  |  |
| vlasia | uncontracted |  |  |
| vlasia mare | uncontracted |  |  |
| vlasia mica | uncontracted |  |  |
| zanoaga | present | Direcția Silvică Hunedoara | bbox_fix:lake:Lacul Zănoaga Mare |
| zanoguta | uncontracted |  |  |
| zlata | uncontracted |  |  |

### Celulă 44.9-45.4N, 23.0-23.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| amaradia | present | AJVPS GORJ |  |
| baleia | uncontracted |  |  |
| barbat | uncontracted |  |  |
| bistrita | present | AJVPS GORJ |  |
| blahnita | present | AJVPS GORJ |  |
| canele | uncontracted |  |  |
| capriorul | uncontracted |  |  |
| cartiu | uncontracted |  |  |
| danube | uncontracted |  |  |
| gornac | uncontracted |  |  |
| izvor apa potabila | uncontracted |  |  |
| izvorul | present-hidden | AJVPS BISTRIȚA-NĂSĂUD |  |
| jiu | present | AJVPS GORJ |  |
| jiul de est | present | Pro Pescar |  |
| jiul de vest | present | Pro Pescar | bbox_fix:prefix |
| lapuselul | uncontracted |  |  |
| motru | present | AJVPS GORJ |  |
| oproni | uncontracted |  |  |
| paraul alb | present | AJVPS CARAȘ-SEVERIN | multiway_chain |
| paraul argelii | uncontracted |  |  |
| paraul crucii1 | uncontracted |  |  |
| paraul polatiste | present | Pro Pescar | audit_match:override |
| paraul prislopului | uncontracted |  |  |
| paraul salatruc | uncontracted |  |  |
| paraul scurta | uncontracted |  |  |
| pilug | uncontracted |  |  |
| raul jiu | present | AJVPS GORJ |  |
| raul tismana | present | ANPA - Ape Necontractate | bbox_fix:lake:Lacul De Acumulare Tismana |
| sadu | present | FLY FISHING CLUB SIBIU | audit_match:prefix |
| sadu lui san | uncontracted |  |  |
| sohodol | present | A.CERBUL CARPATIN | audit_match:char0.88 |
| stoienita | uncontracted |  |  |
| stoinicioara | uncontracted |  |  |
| stolojoaia | uncontracted |  |  |
| suseni | uncontracted |  |  |
| susita | present | AJVPS GORJ |  |
| valea de brazi | uncontracted |  |  |
| valea fantanii | uncontracted |  |  |
| valea lui miron | uncontracted |  |  |
| zlast | uncontracted |  |  |
| zlasti | uncontracted |  |  |

### Celulă 44.9-45.4N, 23.5-24.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| alunis | uncontracted |  |  |
| amaradia | present | AJVPS GORJ |  |
| bistricioara | present | AJVPS VÂLCEA |  |
| blahnita | present | AJVPS GORJ |  |
| carbunele | uncontracted |  |  |
| carpanoasa | uncontracted |  |  |
| casaria | uncontracted |  |  |
| cerna | present | AJVPS VÂLCEA |  |
| cernisoara | present | Direcția Silvică Caraș-Severin | romsilva_map:exact |
| dalbanul | uncontracted |  |  |
| dancila | uncontracted |  |  |
| danube | uncontracted |  |  |
| galbenu | present | Direcția Silvică Vâlcea |  |
| galbenul | uncontracted |  |  |
| gurgui | uncontracted |  |  |
| iezeru | uncontracted |  |  |
| iezerul | uncontracted |  |  |
| izvorul | present-hidden | AJVPS BISTRIȚA-NĂSĂUD |  |
| izvorul purului | uncontracted |  |  |
| latorita | present | Direcția Silvică Vâlcea | romsilva_map:prefix |
| latorita de jos | present | FLY FISHING CLUB SIBIU |  |
| latorita de mijloc | uncontracted |  |  |
| lotru | present | AJVPS VÂLCEA | audit_match:prefix |
| luncavat | present | AJVPS VÂLCEA |  |
| luncavicioara | uncontracted |  |  |
| malaia | present | AJVPS VÂLCEA | bbox_fix:lake:Lacul Mălaia |
| malaiul | uncontracted |  |  |
| marita | uncontracted |  |  |
| matca | uncontracted |  |  |
| mieru | uncontracted |  |  |
| mija mica | present | Direcția Silvică Hunedoara | bbox_fix:lake:Mija |
| mioarele | uncontracted |  |  |
| mohorul cu apa | uncontracted |  |  |
| musetoaia | uncontracted |  |  |
| oltet | present | AJVPS OLT |  |
| paisul mare | uncontracted |  |  |
| paisul mic | uncontracted |  |  |
| papusa | present | Direcția Silvică Hunedoara | romsilva_map:exact |
| paraul ciocadia | uncontracted |  |  |
| paraul galbenu | present | Direcția Silvică Gorj | romsilva_map:token0.00 |
| paraul lazul | uncontracted |  |  |
| paraul muset | uncontracted |  |  |
| paraul plopilor | uncontracted |  |  |
| paraul polatiste | present | Pro Pescar | audit_match:override |
| paraul repedea | present | AJVPS VÂLCEA |  |
| petreasa | uncontracted |  |  |
| petrimanu | present | Direcția Silvică Vâlcea | bbox_fix:lake:Petrimanu |
| plescoaia | uncontracted |  |  |
| purul | uncontracted |  |  |
| raul cernazoara | uncontracted |  |  |
| raul galben | uncontracted |  |  |
| raul gilort | present | AJVPS GORJ |  |
| raul jiet | present | Direcția Silvică Hunedoara | romsilva_map:exact |
| raul mohoru | uncontracted |  |  |
| raul romanul | uncontracted |  |  |
| repedea | present | AJVPS VÂLCEA |  |
| rudareasa | present | AJVPS VÂLCEA |  |
| sadu | present | FLY FISHING CLUB SIBIU | audit_match:prefix |
| sadu lui san | uncontracted |  |  |
| sasa | present | AJVPS VÂLCEA |  |
| slivetul | uncontracted |  |  |
| stefanu | uncontracted |  |  |
| stoienita | uncontracted |  |  |
| taraia | present | AJVPS VÂLCEA |  |
| tecanul | uncontracted |  |  |
| tiganul | uncontracted |  |  |
| turcinul mare | uncontracted |  |  |
| turcinul mic | uncontracted |  |  |
| ungurelasul | uncontracted |  |  |
| ungurelul | uncontracted |  |  |
| urliesu | uncontracted |  |  |
| ursani | present | AJVPS VÂLCEA |  |
| v dracului | uncontracted |  |  |
| zanoaga | present | Direcția Silvică Hunedoara | bbox_fix:lake:Lacul Zănoaga Mare |

### Celulă 44.9-45.4N, 24.0-24.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| adancioara | uncontracted |  |  |
| armasarul | uncontracted |  |  |
| baias | uncontracted |  |  |
| betel | uncontracted |  |  |
| bistricioara | present | AJVPS VÂLCEA |  |
| bistrita | present | Direcția Silvică Vâlcea | romsilva_map:sweep:bistrita |
| bradisor | present | Direcția Silvică Vâlcea |  |
| bucureasa mare | present | AJVPS VÂLCEA | audit_match:prefix |
| bucureasa mica | present | AJVPS VÂLCEA | audit_match:prefix |
| bunesti | uncontracted |  |  |
| caciulata | uncontracted |  |  |
| cacova | uncontracted |  |  |
| calimanul | uncontracted |  |  |
| calinesti | uncontracted |  |  |
| carpanoasa | uncontracted |  |  |
| cerna | present | AJVPS VÂLCEA |  |
| cernisoara | present | Direcția Silvică Caraș-Severin | romsilva_map:exact |
| cheia | present | AJVPS VÂLCEA |  |
| cheile sterpei | uncontracted |  |  |
| ciutesti | uncontracted |  |  |
| clabuceasa | uncontracted |  |  |
| costesti | uncontracted |  |  |
| cuca | uncontracted |  |  |
| cungra | uncontracted |  |  |
| daneasa | uncontracted |  |  |
| danube | uncontracted |  |  |
| dumbravita | present | AJVPS TIMIȘ |  |
| fagetel | uncontracted |  |  |
| firijba | uncontracted |  |  |
| govora | present | AJVPS VÂLCEA |  |
| gurgui | uncontracted |  |  |
| hinta | uncontracted |  |  |
| iazul morilor | uncontracted |  |  |
| izvorul otasaului | uncontracted |  |  |
| izvourl bulzului | uncontracted |  |  |
| jilistea | uncontracted |  |  |
| latorita | present | Direcția Silvică Vâlcea | romsilva_map:prefix |
| lotrisor | present | AJVPS VÂLCEA |  |
| lotrisorul de cozia | uncontracted |  |  |
| lotru | present | AJVPS VÂLCEA | audit_match:prefix |
| luncavat | present | AJVPS VÂLCEA |  |
| lunget | uncontracted |  |  |
| luntrisoara | uncontracted |  |  |
| malaia | present | AJVPS VÂLCEA | bbox_fix:lake:Lacul Mălaia |
| muereasca | uncontracted |  |  |
| oboadele mari | uncontracted |  |  |
| oboadele mici | uncontracted |  |  |
| olanesti | present | AJVPS VÂLCEA |  |
| olt | present | AJVPS OLT |  |
| otasau | uncontracted |  |  |
| paisul mare | uncontracted |  |  |
| paisul mic | uncontracted |  |  |
| paltinoasa | uncontracted |  |  |
| parau | uncontracted |  |  |
| paraul bacea | uncontracted |  |  |
| paraul bivolari | uncontracted |  |  |
| paraul cainelui | uncontracted |  |  |
| paraul cioambelor | uncontracted |  |  |
| paraul izvorul ursului | uncontracted |  |  |
| paraul lacului | present | AJVPS TIMIȘ |  |
| paraul lui ilie | uncontracted |  |  |
| paraul manastirii | uncontracted |  |  |
| paraul mircii | uncontracted |  |  |
| paraul musetel | uncontracted |  |  |
| paraul nisipu | uncontracted |  |  |
| paraul oii | uncontracted |  |  |
| paraul pietrele lacului | uncontracted |  |  |
| paraul plesului | uncontracted |  |  |
| paraul purcariilor | uncontracted |  |  |
| paraul rau | uncontracted |  |  |
| paraul rosu | present | Direcția Silvică Harghita |  |
| paraul sarat | uncontracted |  |  |
| paraul sarpele | uncontracted |  |  |
| paraul sec | uncontracted |  |  |
| paraul tapului | uncontracted |  |  |
| paraul vatuiu | uncontracted |  |  |
| paraul zmeurat | uncontracted |  |  |
| pascoaia | uncontracted |  |  |
| patesti | uncontracted |  |  |
| pesceana | uncontracted |  |  |
| pietroasa | uncontracted |  |  |
| piua | uncontracted |  |  |
| porcarelu | uncontracted |  |  |
| priboiasa | uncontracted |  |  |
| puturoasa | uncontracted |  |  |
| rausorul | uncontracted |  |  |
| robia | uncontracted |  |  |
| rotunda | present | AJVPS MARAMUREȘ |  |
| rudarul | uncontracted |  |  |
| runcu | present | Direcția Silvică Dâmbovița | romsilva_map:token0.00 |
| salatrucel | uncontracted |  |  |
| samnic | uncontracted |  |  |
| samnicel | uncontracted |  |  |
| sarata | present | AJVPS BOTOȘANI |  |
| sasa | present | AJVPS VÂLCEA |  |
| serbaneasa | uncontracted |  |  |
| slamna | uncontracted |  |  |
| slivei | uncontracted |  |  |
| stanicioiu | uncontracted |  |  |
| stoia | uncontracted |  |  |
| topolog | present | AJVPS VÂLCEA |  |
| trepteanca | uncontracted |  |  |
| turnu | present | AJVPS VÂLCEA |  |
| urloaia | uncontracted |  |  |
| valea adancioara | uncontracted |  |  |
| valea albestenilor | uncontracted |  |  |
| valea albinei | uncontracted |  |  |
| valea ariciului | uncontracted |  |  |
| valea bodii | uncontracted |  |  |
| valea boului | uncontracted |  |  |
| valea bradului | uncontracted |  |  |
| valea buletii | uncontracted |  |  |
| valea bulzului | uncontracted |  |  |
| valea caldarilor | uncontracted |  |  |
| valea campului | uncontracted |  |  |
| valea caprareasa | uncontracted |  |  |
| valea caprei | uncontracted |  |  |
| valea carligul mic | uncontracted |  |  |
| valea cocinilor | uncontracted |  |  |
| valea comanca | uncontracted |  |  |
| valea comarnice | uncontracted |  |  |
| valea cornetului | uncontracted |  |  |
| valea craciunelul | uncontracted |  |  |
| valea cracul tisei | uncontracted |  |  |
| valea cu raci | uncontracted |  |  |
| valea de bradet | uncontracted |  |  |
| valea dosului | uncontracted |  |  |
| valea dracului | uncontracted |  |  |
| valea fantanele | uncontracted |  |  |
| valea ferigile | uncontracted |  |  |
| valea fetele cu brazi | uncontracted |  |  |
| valea frasanei | uncontracted |  |  |
| valea frumusica | uncontracted |  |  |
| valea frumusitei | uncontracted |  |  |
| valea galbina | uncontracted |  |  |
| valea gaurilor | uncontracted |  |  |
| valea glavoci | uncontracted |  |  |
| valea glodului | uncontracted |  |  |
| valea gresiilor | uncontracted |  |  |
| valea helesteului | uncontracted |  |  |
| valea hotarului | uncontracted |  |  |
| valea iezerul | uncontracted |  |  |
| valea ionascu | uncontracted |  |  |
| valea izvoarelor | uncontracted |  |  |
| valea izvorul lotrisor | uncontracted |  |  |
| valea izvorului | uncontracted |  |  |
| valea jangului | uncontracted |  |  |
| valea larga | uncontracted |  |  |
| valea lemnelor | uncontracted |  |  |
| valea lespezilor | uncontracted |  |  |
| valea lui anghel | uncontracted |  |  |
| valea lui bucur | uncontracted |  |  |
| valea lui marin | uncontracted |  |  |
| valea lui negru | uncontracted |  |  |
| valea lui stan | uncontracted |  |  |
| valea lupului | uncontracted |  |  |
| valea mare | present | Direcția Silvică Alba | romsilva_map:group-shares-course |
| valea mesteacanului | uncontracted |  |  |
| valea muntisoru | uncontracted |  |  |
| valea neagra | present | Direcția Silvică Suceava | romsilva_map:group-shares-course |
| valea paraul alb | anpa-missing | AJVPS TIMIȘ | Pârâul Pământ Alb |
| valea perisani | uncontracted |  |  |
| valea pesterii | uncontracted |  |  |
| valea piatra taiata | uncontracted |  |  |
| valea pietranesti | uncontracted |  |  |
| valea pietricelei | uncontracted |  |  |
| valea pietroasa | uncontracted |  |  |
| valea plescioarei | uncontracted |  |  |
| valea plesenestilor | uncontracted |  |  |
| valea postei | uncontracted |  |  |
| valea priborului | uncontracted |  |  |
| valea purcarul | uncontracted |  |  |
| valea puturoasa | uncontracted |  |  |
| valea racilor | uncontracted |  |  |
| valea radacina | uncontracted |  |  |
| valea reaua mare | uncontracted |  |  |
| valea reaua mica | uncontracted |  |  |
| valea rosia | present | AJVPS BIHOR |  |
| valea ruzii | uncontracted |  |  |
| valea sacuienilor | uncontracted |  |  |
| valea sasei | uncontracted |  |  |
| valea satului | uncontracted |  |  |
| valea scheiului | uncontracted |  |  |
| valea scortarului | uncontracted |  |  |
| valea secarelei | uncontracted |  |  |
| valea seciului | uncontracted |  |  |
| valea spranea | uncontracted |  |  |
| valea stupina | uncontracted |  |  |
| valea surlelor | uncontracted |  |  |
| valea talvaci | uncontracted |  |  |
| valea teiului | uncontracted |  |  |
| valea tisei | uncontracted |  |  |
| valea ulmetel | uncontracted |  |  |
| valea viezuini | uncontracted |  |  |
| valea vultureasa | uncontracted |  |  |
| varatica | uncontracted |  |  |
| vasilatu | uncontracted |  |  |

### Celulă 44.9-45.4N, 24.5-25.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| arefu | uncontracted |  |  |
| arges | present | AJVPS DÂMBOVIȚA |  |
| argesel | present | AJVPS ARGEȘ | audit_match:prefix |
| badislava | uncontracted |  |  |
| bascov | uncontracted |  |  |
| bratia | present | Direcția Silvică Argeș | romsilva_map:exact |
| bratioara | uncontracted |  |  |
| bughea | present | APS AQUA CRISIUS |  |
| cacova | uncontracted |  |  |
| cernatu | uncontracted |  |  |
| cotmeana | uncontracted |  |  |
| danube | uncontracted |  |  |
| dobroneagu | uncontracted |  |  |
| limpedea | uncontracted |  |  |
| matau | uncontracted |  |  |
| navrap | uncontracted |  |  |
| pauleasca | uncontracted |  |  |
| ploscaru | uncontracted |  |  |
| priba | uncontracted |  |  |
| priseaca | uncontracted |  |  |
| raul bughea | present | APS AQUA CRISIUS |  |
| raul cotmeana | uncontracted |  |  |
| raul doamnei | present | AJVPS ARGEȘ | audit_match:prefix |
| raul targului | present | AJVPS ARGEȘ | audit_match:prefix |
| rausor | present | Direcția Silvică Argeș | romsilva_map:exact |
| robaia | uncontracted |  |  |
| slanic | uncontracted |  |  |
| soptana | uncontracted |  |  |
| toplita | present | AV VIDA SURDUCEL DOBREȘTI |  |
| topolog | present | AJVPS VÂLCEA |  |
| torent aductiune valea lui stan | uncontracted |  |  |
| tulburea | uncontracted |  |  |
| turburea | uncontracted |  |  |
| tutana | uncontracted |  |  |
| valea ciocanu | uncontracted |  |  |
| valea cu pesti | uncontracted |  |  |
| valea iasului | uncontracted |  |  |
| valea lui stan | uncontracted |  |  |
| valea malului | uncontracted |  |  |
| valea mare | present | AVPS MIERCUREA-CIUC |  |
| valea podeni | uncontracted |  |  |
| valea satului | uncontracted |  |  |
| valsan | present | AJVPS ARGEȘ | audit_match:prefix |

### Celulă 44.9-45.4N, 25.0-25.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| arges | present | AJVPS DÂMBOVIȚA |  |
| argesel | present | AJVPS ARGEȘ | audit_match:prefix |
| barbuletu | uncontracted |  |  |
| bolboci | present | Direcția Silvică Dâmbovița | bbox_fix:lake:Lacul Bolboci |
| bughea | present | APS AQUA CRISIUS |  |
| carcinov | uncontracted |  |  |
| carpenis | uncontracted |  |  |
| comorile branei | uncontracted |  |  |
| comorile de mijloc | uncontracted |  |  |
| cumparata mare | uncontracted |  |  |
| cumparata mica | uncontracted |  |  |
| dambovita | present | AVPS ACVILA |  |
| danube | uncontracted |  |  |
| dichiu | uncontracted |  |  |
| draghiciul | uncontracted |  |  |
| gladaria | uncontracted |  |  |
| ialomicioara | uncontracted |  |  |
| ialomita | present | AJVPS DÂMBOVIȚA |  |
| izvor | uncontracted |  |  |
| izvorul dorului | uncontracted |  |  |
| jugureanu | uncontracted |  |  |
| la poduri | uncontracted |  |  |
| leaota | uncontracted |  |  |
| magherita | uncontracted |  |  |
| mitarca | uncontracted |  |  |
| muschiu | uncontracted |  |  |
| muschiului | uncontracted |  |  |
| olt | present | AJVPS OLT |  |
| paraul badenilor | uncontracted |  |  |
| paraul cabanei | uncontracted |  |  |
| paraul chiliilor | uncontracted |  |  |
| paraul glod | uncontracted |  |  |
| paraul hotarului | uncontracted |  |  |
| paraul raciu | uncontracted |  |  |
| paraul rece | uncontracted |  |  |
| paraul stancioiu | uncontracted |  |  |
| pietricica | uncontracted |  |  |
| piscul curii | uncontracted |  |  |
| poienari | uncontracted |  |  |
| radia | uncontracted |  |  |
| ratei | uncontracted |  |  |
| raul alb | present | AJVPS CARAȘ-SEVERIN | multiway_chain |
| raul bizdidel | uncontracted |  |  |
| raul bughea | present | APS AQUA CRISIUS |  |
| raul grecilor | uncontracted |  |  |
| raul ilfov | present | AJVPS DÂMBOVIȚA |  |
| raul sticlariei | uncontracted |  |  |
| raul targului | present | AJVPS ARGEȘ | audit_match:prefix |
| raul vulcana | uncontracted |  |  |
| rausor | present | Direcția Silvică Argeș | romsilva_map:exact |
| rausorul | uncontracted |  |  |
| rudarita mare | uncontracted |  |  |
| scropoasa | present | Direcția Silvică Dâmbovița | bbox_fix:lake:Lacul Scropoasa |
| secaruia mare | uncontracted |  |  |
| secaruia mica | uncontracted |  |  |
| urlatoarea mare | uncontracted |  |  |
| urlatoarea mica | uncontracted |  |  |
| valcelul clinului | uncontracted |  |  |
| valcelul lucacila | uncontracted |  |  |
| valcelul varful cu dor | uncontracted |  |  |
| valea andolia | uncontracted |  |  |
| valea barbuletu | uncontracted |  |  |
| valea batrana | uncontracted |  |  |
| valea blana | uncontracted |  |  |
| valea bradetului | uncontracted |  |  |
| valea brateiului | uncontracted |  |  |
| valea caselor | present | AJVPS ALBA |  |
| valea cheii | uncontracted |  |  |
| valea chipuriei | uncontracted |  |  |
| valea crovului | uncontracted |  |  |
| valea cu brazi | uncontracted |  |  |
| valea cu genune | uncontracted |  |  |
| valea fiasului | uncontracted |  |  |
| valea frumuselului | uncontracted |  |  |
| valea gainii | uncontracted |  |  |
| valea ghimbav | uncontracted |  |  |
| valea grohotisului | uncontracted |  |  |
| valea horoabei | uncontracted |  |  |
| valea iederii | uncontracted |  |  |
| valea iuda | uncontracted |  |  |
| valea lacului | present | AJVPS TIMIȘ |  |
| valea leaota | uncontracted |  |  |
| valea lucacila | uncontracted |  |  |
| valea lui badescu | uncontracted |  |  |
| valea lui coman | uncontracted |  |  |
| valea lui moise | uncontracted |  |  |
| valea lupului | uncontracted |  |  |
| valea magurii | uncontracted |  |  |
| valea mircii | uncontracted |  |  |
| valea mitarca | uncontracted |  |  |
| valea nucetului | uncontracted |  |  |
| valea obadarului | uncontracted |  |  |
| valea pelesului | uncontracted |  |  |
| valea popii | uncontracted |  |  |
| valea pravalelor | uncontracted |  |  |
| valea prepeleacului | uncontracted |  |  |
| valea raiosul | uncontracted |  |  |
| valea rudaritei | uncontracted |  |  |
| valea runcului | uncontracted |  |  |
| valea tamaiei | uncontracted |  |  |
| valea tancavei | uncontracted |  |  |
| valea tatarului | uncontracted |  |  |
| valea vaca | uncontracted |  |  |
| valea vaja | present | Direcția Silvica Gorj | bbox_fix:lake:Lacul de Acumulare Vâja |
| valea valcea | uncontracted |  |  |

### Celulă 44.9-45.4N, 25.5-26.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| alunis | uncontracted |  |  |
| apa canalizare | uncontracted |  |  |
| baiu mare | uncontracted |  |  |
| baiu mic | uncontracted |  |  |
| bob | uncontracted |  |  |
| bughea | present | APS AQUA CRISIUS |  |
| cacacea | uncontracted |  |  |
| campinita | uncontracted |  |  |
| carpen | uncontracted |  |  |
| carpenis | uncontracted |  |  |
| clabucet | uncontracted |  |  |
| claia cu brazi | uncontracted |  |  |
| comorile branei | uncontracted |  |  |
| comorile claii | uncontracted |  |  |
| comorile de mijloc | uncontracted |  |  |
| cosmina | uncontracted |  |  |
| cotofana | uncontracted |  |  |
| crasna | present | AJVPS VASLUI | anpa_map:sweep:crasna |
| cricov | present | AJVPS DÂMBOVIȚA |  |
| cricovul dulce | present | AJVPS PRAHOVA |  |
| dambul | uncontracted |  |  |
| danube | uncontracted |  |  |
| doftana | uncontracted |  |  |
| doftanet | uncontracted |  |  |
| dracilor | uncontracted |  |  |
| florei | uncontracted |  |  |
| floreiu | uncontracted |  |  |
| franca | uncontracted |  |  |
| glodeasa | uncontracted |  |  |
| grohotis | uncontracted |  |  |
| ialomicioara | uncontracted |  |  |
| ialomita | present | AJVPS DÂMBOVIȚA |  |
| izvorul dorului | uncontracted |  |  |
| izvorul mierlele | uncontracted |  |  |
| luparia | uncontracted |  |  |
| mislea | uncontracted |  |  |
| mislei | uncontracted |  |  |
| negras | uncontracted |  |  |
| orjogoaia | uncontracted |  |  |
| paltinoasa | uncontracted |  |  |
| paraul beliei | uncontracted |  |  |
| paraul jepilor | uncontracted |  |  |
| paraul negru | present | AJVPS COVASNA | audit_match:prefix |
| paraul stanii | uncontracted |  |  |
| paraul talea | uncontracted |  |  |
| paraul ursilor | uncontracted |  |  |
| paraul varsaturile | uncontracted |  |  |
| pietricica | uncontracted |  |  |
| prahova | present | AJVPS PRAHOVA | audit_match:prefix |
| prislop | uncontracted |  |  |
| provita | uncontracted |  |  |
| raul bizdidel | uncontracted |  |  |
| raul ocnita | uncontracted |  |  |
| raul slanic | uncontracted |  |  |
| runc | uncontracted |  |  |
| sacuianca | uncontracted |  |  |
| sarata | present | AJVPS BOTOȘANI |  |
| secaria | uncontracted |  |  |
| slanic | uncontracted |  |  |
| teleajen | present | AJVPS PRAHOVA | audit_match:prefix |
| telejenel | present | Direcția Silvică Prahova | romsilva_map:exact |
| urlatoarea | uncontracted |  |  |
| urlatoarea mare | uncontracted |  |  |
| urlatoarea mica | uncontracted |  |  |
| urzica | uncontracted |  |  |
| valceaua lui marcan | uncontracted |  |  |
| valea alba | uncontracted |  |  |
| valea babei | uncontracted |  |  |
| valea batraioara | uncontracted |  |  |
| valea belia mare | uncontracted |  |  |
| valea belia mica | uncontracted |  |  |
| valea bradetului | uncontracted |  |  |
| valea cainelui | uncontracted |  |  |
| valea caseriei | uncontracted |  |  |
| valea conciului | uncontracted |  |  |
| valea cotofenei | uncontracted |  |  |
| valea cu brazi | uncontracted |  |  |
| valea cu genune | uncontracted |  |  |
| valea dogariei | uncontracted |  |  |
| valea dracului | uncontracted |  |  |
| valea dulce | uncontracted |  |  |
| valea fundul vaii | uncontracted |  |  |
| valea gagautilor | uncontracted |  |  |
| valea izvorului | uncontracted |  |  |
| valea larga | uncontracted |  |  |
| valea lui bogdan | uncontracted |  |  |
| valea magarului | uncontracted |  |  |
| valea mare | present | AVPS MIERCUREA-CIUC |  |
| valea marului | uncontracted |  |  |
| valea neagra | present | Direcția Silvică Suceava | romsilva_map:group-shares-course |
| valea obielei | uncontracted |  |  |
| valea oratii | uncontracted |  |  |
| valea pelesului | uncontracted |  |  |
| valea pelisor | uncontracted |  |  |
| valea pietrii | uncontracted |  |  |
| valea popii | uncontracted |  |  |
| valea rea | uncontracted |  |  |
| valea seaca dintre clai | uncontracted |  |  |
| valea secariei | uncontracted |  |  |
| valea seciului | uncontracted |  |  |
| valea sfanta ana | uncontracted |  |  |
| valea sipa | uncontracted |  |  |
| valea sipotelor | uncontracted |  |  |
| valea soarelui | uncontracted |  |  |
| valea tufa | uncontracted |  |  |
| valea zamora | uncontracted |  |  |
| valea zanoaga | present | Direcția Silvică Hunedoara | bbox_fix:lake:Lacul Zănoaga Mare |
| valea zgarburei | uncontracted |  |  |
| varbilau | present | AJVPS PRAHOVA |  |
| vornicu | uncontracted |  |  |

### Celulă 44.9-45.4N, 26.0-26.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| balaneasa | uncontracted |  |  |
| baltesti | uncontracted |  |  |
| basca chiojd | uncontracted |  |  |
| bucovel | uncontracted |  |  |
| bughea | present | APS AQUA CRISIUS |  |
| buzau | present | AJVPS Brăila |  |
| cacacea | uncontracted |  |  |
| ciuciuneasa | uncontracted |  |  |
| crang | uncontracted |  |  |
| crasna | present | AJVPS VASLUI | anpa_map:sweep:crasna |
| cricovul sarat | present | AJVPS PRAHOVA |  |
| dambul | uncontracted |  |  |
| danube | uncontracted |  |  |
| drajna | uncontracted |  |  |
| frasinet | uncontracted |  |  |
| ghighiul | uncontracted |  |  |
| lopatna | present | AJVPS PRAHOVA |  |
| niscov | uncontracted |  |  |
| ogretineanca | uncontracted |  |  |
| paraul balana | uncontracted |  |  |
| paraul chiojdeanca | uncontracted |  |  |
| paraul iordacheanu | uncontracted |  |  |
| paraul istau | uncontracted |  |  |
| paraul naieanca | uncontracted |  |  |
| paraul prosca | uncontracted |  |  |
| paraul sarata | present | AJVPS BOTOȘANI |  |
| preseaca | uncontracted |  |  |
| raul buzau | present | AJVPS Brăila |  |
| raul cricovul sarat | present | AJVPS PRAHOVA |  |
| raul panatau | uncontracted |  |  |
| rusavat | uncontracted |  |  |
| sacuianca | uncontracted |  |  |
| saratel | uncontracted |  |  |
| saratica | uncontracted |  |  |
| stalpul | uncontracted |  |  |
| stamnic | uncontracted |  |  |
| teleajen | present | AJVPS PRAHOVA | audit_match:prefix |
| telejenel | present | Direcția Silvică Prahova | romsilva_map:exact |
| tohaneanca | uncontracted |  |  |
| valea crangului | uncontracted |  |  |
| valea mare | present | AVPS MIERCUREA-CIUC |  |
| valea razboiului | uncontracted |  |  |
| valea rece | uncontracted |  |  |
| valea schitului | uncontracted |  |  |
| valeanca | uncontracted |  |  |
| varbila | uncontracted |  |  |
| varbilau | present | AJVPS PRAHOVA |  |
| zeletin | uncontracted |  |  |

### Celulă 44.9-45.4N, 26.5-27.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| balaneasa | uncontracted |  |  |
| buzau | present | AJVPS Brăila |  |
| calnau | uncontracted |  |  |
| danube | uncontracted |  |  |
| garla hodorogului | uncontracted |  |  |
| ghighiul | uncontracted |  |  |
| muratoarea | uncontracted |  |  |
| niscov | uncontracted |  |  |
| paraul naieanca | uncontracted |  |  |
| raul buzau | present | AJVPS Brăila |  |
| sarata | present | AJVPS BOTOȘANI |  |
| saratel | uncontracted |  |  |
| slanic | uncontracted |  |  |
| tocileasa | uncontracted |  |  |
| valea rece | uncontracted |  |  |

### Celulă 44.9-45.4N, 27.0-27.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| buzau | present | AJVPS Brăila |  |
| calmatui | present | AJVPS Brăila | sweep:fix-wrong-county-geom |
| danube | uncontracted |  |  |
| ramnicu sarat | present | AJVPS VRANCEA | anpa_map:sweep:ramnicu sarat |

### Celulă 44.9-45.4N, 27.5-28.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bratul calia | uncontracted |  |  |
| bratul macin | uncontracted |  |  |
| bratul pasca | uncontracted |  |  |
| bratul valciu | uncontracted |  |  |
| buzau | present | AJVPS Brăila |  |
| calmatui | present | AJVPS Brăila | sweep:fix-wrong-county-geom |
| danube | uncontracted |  |  |
| dunarea | uncontracted |  |  |
| dunarea bratul arupul | uncontracted |  |  |
| dunarea bratul cracanel | uncontracted |  |  |
| dunarea bratul cravia | uncontracted |  |  |
| dunarea bratul dranovita | uncontracted |  |  |
| paraul moldovencei | uncontracted |  |  |
| poioasa | uncontracted |  |  |
| siret | present | Centrul Regional de Ecologie Bacău |  |

### Celulă 44.9-45.4N, 28.0-28.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bratul macin | uncontracted |  |  |
| canalul saraceni | uncontracted |  |  |
| ciucurova | uncontracted |  |  |
| crapina | uncontracted |  |  |
| danube | uncontracted |  |  |
| dunarea | uncontracted |  |  |
| dunarea дунаи | uncontracted |  |  |
| garla cazacului | uncontracted |  |  |
| hidrichu | uncontracted |  |  |
| islam | uncontracted |  |  |
| paraul airoman | uncontracted |  |  |
| paraul boclugea | uncontracted |  |  |
| paraul calistra | uncontracted |  |  |
| paraul capaclia | uncontracted |  |  |
| paraul carabalu | uncontracted |  |  |
| paraul cerna | present | AJVPS VÂLCEA |  |
| paraul chediu | uncontracted |  |  |
| paraul ditcova | uncontracted |  |  |
| paraul fantana oilor | uncontracted |  |  |
| paraul jijila | uncontracted |  |  |
| paraul lui jug | uncontracted |  |  |
| paraul racova | present | AJVPS VASLUI | audit_match:exact |
| paraul recea | uncontracted |  |  |
| paraul sorniac | uncontracted |  |  |
| paraul telita | uncontracted |  |  |
| parlita | uncontracted |  |  |
| siret | present | Centrul Regional de Ecologie Bacău |  |
| stymbelar | uncontracted |  |  |
| sulucu | uncontracted |  |  |
| taita | uncontracted |  |  |
| valea adanca | uncontracted |  |  |
| valea carada | uncontracted |  |  |
| valea curaturi | uncontracted |  |  |
| valea dautcea | uncontracted |  |  |
| valea drumu de piatra | uncontracted |  |  |
| valea glontului | uncontracted |  |  |
| valea ialia | uncontracted |  |  |
| valea lozova | uncontracted |  |  |
| valea lui asman | uncontracted |  |  |
| valea lui iancu | uncontracted |  |  |
| valea luncavita | uncontracted |  |  |
| valea lupului | uncontracted |  |  |
| valea mangina | uncontracted |  |  |
| valea mesterului | uncontracted |  |  |
| valea mina | uncontracted |  |  |
| valea patru drumuri | uncontracted |  |  |
| valea pricopan | uncontracted |  |  |
| valea recea | uncontracted |  |  |
| valea stanca | present | AJVPS BRĂILA | sweep:hidden:valea stanca |
| valea turiacului | uncontracted |  |  |
| valea ulmului | uncontracted |  |  |
| veche | uncontracted |  |  |
| гирло зарзи | uncontracted |  |  |
| кам яне гирло | uncontracted |  |  |
| картал гирло | uncontracted |  |  |

### Celulă 44.9-45.4N, 28.5-29.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| avram | uncontracted |  |  |
| bratul sfantu gheorghe | uncontracted |  |  |
| bratul sulina | uncontracted |  |  |
| canal papadia veche | uncontracted |  |  |
| canal piscani | uncontracted |  |  |
| ciucurova | uncontracted |  |  |
| danube | uncontracted |  |  |
| dunarea | uncontracted |  |  |
| dunarea bratul tulcea | uncontracted |  |  |
| dunarea дунаи | uncontracted |  |  |
| hagilar | uncontracted |  |  |
| la plop | uncontracted |  |  |
| paraul telita | uncontracted |  |  |
| rapa lui macarie | uncontracted |  |  |
| ripcenca | uncontracted |  |  |
| tabana | uncontracted |  |  |
| taita | uncontracted |  |  |
| telita | uncontracted |  |  |
| valea ac cadan | uncontracted |  |  |
| valea alibeichioi | uncontracted |  |  |
| valea chiosdarlac | uncontracted |  |  |
| valea hotaru | uncontracted |  |  |
| картал гирло | uncontracted |  |  |
| кислицькии рукав | uncontracted |  |  |
| клушинська балка | uncontracted |  |  |
| кіліиське гирло | uncontracted |  |  |
| кіліиське гирло bratul chilia | uncontracted |  |  |
| протока скунда | uncontracted |  |  |
| ретка гирло | uncontracted |  |  |
| рукав іванешть bratul ivanesti | uncontracted |  |  |
| табачелло | uncontracted |  |  |
| тельхія | uncontracted |  |  |
| єрик перекат | uncontracted |  |  |

### Celulă 44.9-45.4N, 29.0-29.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bratul cernovca | uncontracted |  |  |
| bratul sfantu gheorghe | uncontracted |  |  |
| bratul sulina | uncontracted |  |  |
| bratul tataru | uncontracted |  |  |
| canal papadia veche | uncontracted |  |  |
| danube | uncontracted |  |  |
| dunarea | uncontracted |  |  |
| кислицькии рукав | uncontracted |  |  |
| кіліиське гирло | uncontracted |  |  |
| кіліиське гирло bratul chilia | uncontracted |  |  |
| протока даллер | uncontracted |  |  |
| протока прірва | uncontracted |  |  |
| рукав іванешть bratul ivanesti | uncontracted |  |  |

### Celulă 44.9-45.4N, 29.5-30.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bratul cernovca | uncontracted |  |  |
| bratul sfantu gheorghe | uncontracted |  |  |
| bratul sulina | uncontracted |  |  |
| danube | uncontracted |  |  |
| dunarea | uncontracted |  |  |
| romania украіна | uncontracted |  |  |
| анакіна | uncontracted |  |  |
| анкудінове гирло | uncontracted |  |  |
| бистре гирло | uncontracted |  |  |
| відніжне гирло | uncontracted |  |  |
| гирло мусура bratul musura | uncontracted |  |  |
| зуіва | uncontracted |  |  |
| казеикін жолобок | uncontracted |  |  |
| кіліиське гирло bratul chilia | uncontracted |  |  |
| матвеево гирло | uncontracted |  |  |
| очаківське гирло | uncontracted |  |  |
| простін | uncontracted |  |  |
| піщане гирло | uncontracted |  |  |
| романове | uncontracted |  |  |
| середнє | uncontracted |  |  |
| середніи рукав | uncontracted |  |  |
| серіан | uncontracted |  |  |
| старостамбульське гирло | uncontracted |  |  |
| старостамбульське гирло bratul stambulul vechi | uncontracted |  |  |
| східне гирло | uncontracted |  |  |
| циганське гирло | uncontracted |  |  |

### Celulă 45.4-45.9N, 20.0-20.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bega | present | AJVPS TIMIȘ |  |
| bega veche | present | AJVPS TIMIȘ |  |
| danube | uncontracted |  |  |
| tisza | uncontracted |  |  |
| бегеј | uncontracted |  |  |
| златица | uncontracted |  |  |
| стари бегеј | uncontracted |  |  |
| тиса | uncontracted |  |  |
| јегричка | uncontracted |  |  |

### Celulă 45.4-45.9N, 20.5-21.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| apa mare | present | AJVPS TIMIȘ |  |
| bega | present | AJVPS TIMIȘ |  |
| bega veche | present | AJVPS TIMIȘ |  |
| beregsau | uncontracted |  |  |
| birda veche | uncontracted |  |  |
| canalul timisat | present | AJVPS TIMIȘ | audit_match:override |
| danube | uncontracted |  |  |
| pamant alb | present | AJVPS TIMIȘ |  |
| timis | present | AJVPS TIMIȘ |  |
| бирда | uncontracted |  |  |
| стари бегеј | uncontracted |  |  |
| тамиш | uncontracted |  |  |

### Celulă 45.4-45.9N, 21.0-21.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| apa mare | present | AJVPS TIMIȘ |  |
| bacin | uncontracted |  |  |
| barzava | present | AJVPS TIMIȘ |  |
| bega | present | AJVPS TIMIȘ |  |
| bega veche | present | AJVPS TIMIȘ |  |
| behela | present | AJVPS TIMIȘ |  |
| beregsau | uncontracted |  |  |
| birda veche | uncontracted |  |  |
| canalul barzava | present | AJVPS TIMIȘ |  |
| canalul gavojdia | uncontracted |  |  |
| caran | present | AJVPS TIMIȘ |  |
| danube | uncontracted |  |  |
| gherteamos | present | AJVPS TIMIȘ |  |
| iercicu | uncontracted |  |  |
| lanca | uncontracted |  |  |
| lanka | uncontracted |  |  |
| magherus | present | AJVPS TIMIȘ |  |
| paraul lacului | present | AJVPS TIMIȘ |  |
| poganis | present | AJVPS TIMIȘ |  |
| potoc | uncontracted |  |  |
| surduc | present | ANPA - Ape Necontractate | bbox_fix:lake:Lacul Surduc |
| surgani | present | AJVPS TIMIȘ |  |
| timis | present | AJVPS TIMIȘ |  |
| timisul mort | uncontracted |  |  |
| unu | uncontracted |  |  |
| valea dosului | uncontracted |  |  |
| vana | uncontracted |  |  |
| бирда | uncontracted |  |  |

### Celulă 45.4-45.9N, 21.5-22.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bacin | uncontracted |  |  |
| barzava | present | AJVPS TIMIȘ |  |
| bega | present | AJVPS TIMIȘ |  |
| binis | uncontracted |  |  |
| cinca | uncontracted |  |  |
| danube | uncontracted |  |  |
| gherteamos | present | AJVPS TIMIȘ |  |
| glavita | present | AJVPS TIMIȘ |  |
| glavita bega | uncontracted |  |  |
| paraul fizes | present | AJPS Cluj |  |
| paraul stiuca | uncontracted |  |  |
| poganis | present | AJVPS TIMIȘ |  |
| salcia | uncontracted |  |  |
| silagiu | uncontracted |  |  |
| stiuca | uncontracted |  |  |
| surgani | present | AJVPS TIMIȘ |  |
| tau | present | Direcția Silvică Alba | romsilva_map:exact |
| timis | present | AJVPS TIMIȘ |  |
| timisana | present | AJVPS TIMIȘ |  |

### Celulă 45.4-45.9N, 22.0-22.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bega | present | AJVPS TIMIȘ |  |
| bega luncani | present | Direcția Silvică Timiș | sweep:hidden:bega luncani |
| bega poieni | present | Direcția Silvică Timiș | romsilva_map:exact |
| bistra | present | Direcția Silvică Sibiu | romsilva_map:exact |
| bratoane | uncontracted |  |  |
| danube | uncontracted |  |  |
| gladna | uncontracted |  |  |
| glavita | present | AJVPS TIMIȘ |  |
| hauzesti | uncontracted |  |  |
| izvodia | uncontracted |  |  |
| loznisoara | uncontracted |  |  |
| macnicel | uncontracted |  |  |
| munisel | uncontracted |  |  |
| nadrag | present | AJVPS TIMIȘ | audit_match:exact |
| nadragel | uncontracted |  |  |
| ohaba | uncontracted |  |  |
| paraul lapugiu | uncontracted |  |  |
| paraul vadana | uncontracted |  |  |
| pete | uncontracted |  |  |
| poganis | present | AJVPS TIMIȘ |  |
| potoc | uncontracted |  |  |
| raul beghei | uncontracted |  |  |
| rozalia | uncontracted |  |  |
| rusca | uncontracted |  |  |
| saraz | uncontracted |  |  |
| sasa | present | AJVPS VÂLCEA |  |
| sebes | present | AJVPS ALBA |  |
| soimu | present | D.S. Cluj | bbox_fix:lake:Lacul Șoimu |
| sudrias | uncontracted |  |  |
| surduc | present | ANPA - Ape Necontractate | bbox_fix:lake:Lacul Surduc |
| timis | present | AJVPS TIMIȘ |  |
| timisul mort | uncontracted |  |  |
| toplita | present | AV VIDA SURDUCEL DOBREȘTI |  |
| valea cornetului | uncontracted |  |  |
| valea lui liman | uncontracted |  |  |
| valea mare | present | CS HUNEDOARA |  |
| valea padesului | uncontracted |  |  |
| valea potocului | uncontracted |  |  |
| valea stalpului | uncontracted |  |  |
| valisor | uncontracted |  |  |
| vana mare | uncontracted |  |  |
| vana rovina | uncontracted |  |  |
| zlagna | uncontracted |  |  |
| zoldiana | uncontracted |  |  |

### Celulă 45.4-45.9N, 22.5-23.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| barbat | uncontracted |  |  |
| bargau | uncontracted |  |  |
| bilea | uncontracted |  |  |
| bistra | present | Direcția Silvică Sibiu | romsilva_map:exact |
| bistra marului | present | Direcția Silvică Caraș-Severin | romsilva_map:prefix |
| bordul | uncontracted |  |  |
| breazova | present | Direcția Silvică Caraș-Severin | bbox_fix:lake:Lacul Breazova (Văliug) |
| cerna | present | Direcția Silvică Mehedinți | sweep:hidden:group-shares-course |
| danube | uncontracted |  |  |
| dobra | present | FLY FISHING CLUB SIBIU |  |
| galbena | uncontracted |  |  |
| galesu | uncontracted |  |  |
| govajdia | present | Pro Pescar |  |
| hasdatel | uncontracted |  |  |
| lapusnic | uncontracted |  |  |
| mures | present | AJVPS TIMIȘ |  |
| nadrab | uncontracted |  |  |
| nucsoara | uncontracted |  |  |
| ohaba | uncontracted |  |  |
| paros | uncontracted |  |  |
| peceneaga | uncontracted |  |  |
| pietrele | uncontracted |  |  |
| racastie | uncontracted |  |  |
| raul mare | present | CS HUNEDOARA |  |
| raul mures | present | AJVPS ALBA |  |
| raul strei | present | AJVPS HUNEDOARA |  |
| rausor | present | Direcția Silvică Argeș | romsilva_map:exact |
| retisoara | uncontracted |  |  |
| runc | uncontracted |  |  |
| sacamas | uncontracted |  |  |
| salas | uncontracted |  |  |
| scorila | uncontracted |  |  |
| sibisel | present | Direcția Silvică Hunedoara | romsilva_map:exact |
| sohodol | present | A.CERBUL CARPATIN | audit_match:char0.88 |
| stanisoara | uncontracted |  |  |
| stevia | present | Direcția Silvică Hunedoara | bbox_fix:lake:Ștevia |
| strei | present | AJVPS HUNEDOARA |  |
| sucu | present | Direcția Silvică Caraș-Severin | romsilva_map:exact |
| valea mare | present | Direcția Silvică Alba | romsilva_map:group-shares-course |
| valea rachitelii | uncontracted |  |  |
| valea rea | uncontracted |  |  |
| valea sturu | uncontracted |  |  |
| valea ursului | uncontracted |  |  |
| valereasca | uncontracted |  |  |
| valerita | uncontracted |  |  |
| varmaga | uncontracted |  |  |
| zlasti | uncontracted |  |  |

### Celulă 45.4-45.9N, 23.0-23.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| alun | uncontracted |  |  |
| anines | uncontracted |  |  |
| ausel | uncontracted |  |  |
| baleia | uncontracted |  |  |
| banita | present | AJVPS HUNEDOARA |  |
| barbat | uncontracted |  |  |
| barusoru | uncontracted |  |  |
| bobaia | uncontracted |  |  |
| boiu | uncontracted |  |  |
| bosorogul | uncontracted |  |  |
| canal de aductune raul strei | uncontracted |  |  |
| canal moara | uncontracted |  |  |
| canalul moara | uncontracted |  |  |
| cioara | uncontracted |  |  |
| cucuis | uncontracted |  |  |
| cugir | present | AJVPS ALBA |  |
| dreptul | uncontracted |  |  |
| feredau | uncontracted |  |  |
| gantaga | uncontracted |  |  |
| garbava | uncontracted |  |  |
| glivii | uncontracted |  |  |
| grid | uncontracted |  |  |
| gropsoara | uncontracted |  |  |
| iuba | uncontracted |  |  |
| jarosul | uncontracted |  |  |
| jiul de est | present | Pro Pescar |  |
| jupaneasa | uncontracted |  |  |
| lazu | uncontracted |  |  |
| luncani | uncontracted |  |  |
| morii | uncontracted |  |  |
| muncelu | uncontracted |  |  |
| mures | present | AJVPS TIMIȘ |  |
| ocolis | present | AJVPS ALBA |  |
| ohaba | uncontracted |  |  |
| orastie | uncontracted |  |  |
| paraul alb | present | AJVPS CARAȘ-SEVERIN | multiway_chain |
| paraul maleia | uncontracted |  |  |
| paraul vanatorului | uncontracted |  |  |
| parvei | uncontracted |  |  |
| pianu | uncontracted |  |  |
| porcaret | uncontracted |  |  |
| pustiosu | uncontracted |  |  |
| raul alb | present | AJVPS CARAȘ-SEVERIN | multiway_chain |
| raul jiet | present | Direcția Silvică Hunedoara | romsilva_map:exact |
| raul mare | present | Direcția Silvică Alba | romsilva_map:group-shares-course |
| raul mare cugir | uncontracted |  |  |
| raul mic | present | Direcția Silvică Alba | romsilva_map:exact |
| raul mures | present | AJVPS ALBA |  |
| raul romosului | uncontracted |  |  |
| raul strei | present | AJVPS HUNEDOARA |  |
| raul vaidei | uncontracted |  |  |
| rausor | present | Direcția Silvică Argeș | romsilva_map:exact |
| romos | uncontracted |  |  |
| rosia | present | AJVPS BIHOR |  |
| rusor | uncontracted |  |  |
| sibisel | present | Direcția Silvică Hunedoara | romsilva_map:exact |
| stramtosu | uncontracted |  |  |
| strei | present | AJVPS HUNEDOARA |  |
| taia | uncontracted |  |  |
| turdas | uncontracted |  |  |
| vaidei | uncontracted |  |  |
| valea cascadelor | uncontracted |  |  |
| valea frasanului | uncontracted |  |  |
| valea larga | uncontracted |  |  |
| valea luntrii | uncontracted |  |  |
| valea manarii | uncontracted |  |  |
| valea mare | present | Direcția Silvică Alba | romsilva_map:group-shares-course |
| valea mica | uncontracted |  |  |
| valea morii | uncontracted |  |  |
| valea popii | uncontracted |  |  |
| valea prihodistei | uncontracted |  |  |
| valea rea | uncontracted |  |  |
| valea sipcii | uncontracted |  |  |
| valea streicicea | uncontracted |  |  |
| valea untului | uncontracted |  |  |
| varatec | uncontracted |  |  |
| varmaga | uncontracted |  |  |

### Celulă 45.4-45.9N, 23.5-24.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| amnas | uncontracted |  |  |
| apold | uncontracted |  |  |
| arsura | uncontracted |  |  |
| balindru | present | Direcția Silvică Vâlcea |  |
| balu | uncontracted |  |  |
| chipesii | uncontracted |  |  |
| cugir | present | AJVPS ALBA |  |
| dancila | uncontracted |  |  |
| daneasa | uncontracted |  |  |
| diudiul | uncontracted |  |  |
| dobra | present | FLY FISHING CLUB SIBIU |  |
| flotea | uncontracted |  |  |
| frumoasa | present | AVPS MIERCUREA-CIUC |  |
| furnica | uncontracted |  |  |
| garbova | uncontracted |  |  |
| groapa seaca | uncontracted |  |  |
| halangioasa | uncontracted |  |  |
| hanes | uncontracted |  |  |
| hoteag | uncontracted |  |  |
| iezerul mare | present | FLY FISHING CLUB SIBIU | bbox_fix:lake:Iezerul Mare |
| iezerul mic | present | FLY FISHING CLUB SIBIU |  |
| izvorul contului | uncontracted |  |  |
| izvorul goatelor | uncontracted |  |  |
| izvorul gropii | uncontracted |  |  |
| jidoaia | uncontracted |  |  |
| jiul de est | present | Pro Pescar |  |
| lotru | present | AJVPS VÂLCEA | audit_match:prefix |
| mag | uncontracted |  |  |
| manaileasa | uncontracted |  |  |
| mieru | uncontracted |  |  |
| mija mica | present | Direcția Silvică Hunedoara | bbox_fix:lake:Mija |
| nedeiu | uncontracted |  |  |
| paraul barbesului | uncontracted |  |  |
| paraul bumbii | uncontracted |  |  |
| paraul calnic | uncontracted |  |  |
| paraul cetatii | uncontracted |  |  |
| paraul cocaraciu | uncontracted |  |  |
| paraul comorii | uncontracted |  |  |
| paraul foltea | uncontracted |  |  |
| paraul jogarenii | uncontracted |  |  |
| paraul lui burlacoaie | uncontracted |  |  |
| paraul lui stan | uncontracted |  |  |
| paraul mare | present | Direcția Silvică Alba | romsilva_map:group-shares-course |
| paraul negru | present | AJVPS COVASNA | audit_match:prefix |
| paraul neniului | uncontracted |  |  |
| paraul pestilor | uncontracted |  |  |
| paraul ruscai | uncontracted |  |  |
| paraul sibiel | uncontracted |  |  |
| paraul sibielas | uncontracted |  |  |
| paraul vale | uncontracted |  |  |
| paraul valea | present | ANPA - Ape Necontractate | bbox_fix:lake:Lacul Valea Mare |
| paraul valea garbovii | uncontracted |  |  |
| paraul valea mare | present | ANPA - Ape Necontractate | bbox_fix:lake:Lacul Valea Mare |
| paraul valea mica | uncontracted |  |  |
| paraul valea popii | uncontracted |  |  |
| paraul valea vlasinului | uncontracted |  |  |
| pianu | uncontracted |  |  |
| poieni | uncontracted |  |  |
| pravatul | uncontracted |  |  |
| prigoana | uncontracted |  |  |
| purul | uncontracted |  |  |
| ranjeu | uncontracted |  |  |
| ranjeul mare | uncontracted |  |  |
| rau negru | present | AJVPS COVASNA | audit_match:prefix |
| raul cibin | present | APS AQUA CRISIUS | multiway_chain |
| raul jiet | present | Direcția Silvică Hunedoara | romsilva_map:exact |
| raul mare | present | Direcția Silvică Alba | romsilva_map:group-shares-course |
| raul mare cugir | uncontracted |  |  |
| raul mic | present | Direcția Silvică Alba | romsilva_map:exact |
| raul negru | present | AJVPS COVASNA | audit_match:prefix |
| riu negru | uncontracted |  |  |
| rudareasa | present | AJVPS VÂLCEA |  |
| sadu | present | FLY FISHING CLUB SIBIU | audit_match:prefix |
| salanele | uncontracted |  |  |
| sangatin | uncontracted |  |  |
| saracinul mare | uncontracted |  |  |
| sebes | present | AJVPS ALBA |  |
| secas | present | AJVPS ALBA |  |
| sibiel | uncontracted |  |  |
| slivetul | uncontracted |  |  |
| smidelor | uncontracted |  |  |
| steaza | uncontracted |  |  |
| stefanu | uncontracted |  |  |
| sterminos | uncontracted |  |  |
| sugag | uncontracted |  |  |
| tartarau | uncontracted |  |  |
| tigana | uncontracted |  |  |
| tiganul | uncontracted |  |  |
| tilisca | uncontracted |  |  |
| tiliscuta | uncontracted |  |  |
| turnisoara | uncontracted |  |  |
| valea bobesului | uncontracted |  |  |
| valea canciului | uncontracted |  |  |
| valea contului | uncontracted |  |  |
| valea dalmelor | uncontracted |  |  |
| valea doamnei | present | AJVPS ARGEȘ | audit_match:prefix |
| valea drojdiei | uncontracted |  |  |
| valea granitei | uncontracted |  |  |
| valea mare | present | Direcția Silvică Alba | romsilva_map:group-shares-course |
| valea muierii | uncontracted |  |  |
| valea steaja | uncontracted |  |  |
| valea tampei | uncontracted |  |  |
| valea urliesu | uncontracted |  |  |
| valea ursului | uncontracted |  |  |
| valea utea | uncontracted |  |  |
| vatafu | uncontracted |  |  |
| vidruta | uncontracted |  |  |
| voinesita | uncontracted |  |  |
| w | uncontracted |  |  |
| zavoaia | uncontracted |  |  |

### Celulă 45.4-45.9N, 24.0-24.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| avrig | uncontracted |  |  |
| barbu | uncontracted |  |  |
| boia | present | AJVPS VÂLCEA |  |
| boia mare | present | AJVPS VÂLCEA |  |
| boia mica | present | AJVPS VÂLCEA |  |
| boisoara | uncontracted |  |  |
| calinesti | uncontracted |  |  |
| cibin | present | APS AQUA CRISIUS | multiway_chain |
| cisnadie | uncontracted |  |  |
| clabuceasa | uncontracted |  |  |
| curpanu | uncontracted |  |  |
| daescu | uncontracted |  |  |
| dobra | present | FLY FISHING CLUB SIBIU |  |
| dosul mlacii | uncontracted |  |  |
| fratelui | uncontracted |  |  |
| gaujani | uncontracted |  |  |
| grohotisul | uncontracted |  |  |
| gusatu | uncontracted |  |  |
| halangioasa | uncontracted |  |  |
| hartibaciu | present | AJVPS SIBIU |  |
| ivanus | uncontracted |  |  |
| izvorul budislavului | uncontracted |  |  |
| izvorul curpanului | uncontracted |  |  |
| izvorul frumos | uncontracted |  |  |
| izvorul gruiul lung | uncontracted |  |  |
| izvorul muntelui | uncontracted |  |  |
| izvorul rudarilor | uncontracted |  |  |
| izvorul surului | uncontracted |  |  |
| izvorul trandafirilor | uncontracted |  |  |
| izvorul uria | present | AJVPS VÂLCEA |  |
| lotrioara | present | FLY FISHING CLUB SIBIU |  |
| lotrisor | present | AJVPS VÂLCEA |  |
| lotru | present | AJVPS VÂLCEA | audit_match:prefix |
| lungsoara | uncontracted |  |  |
| mandra | uncontracted |  |  |
| marsa | uncontracted |  |  |
| meghis | uncontracted |  |  |
| melita | uncontracted |  |  |
| murgasul mare | uncontracted |  |  |
| neteda | uncontracted |  |  |
| olt | present | AJVPS OLT |  |
| paraul calului | uncontracted |  |  |
| paraul cu lespezi | uncontracted |  |  |
| paraul cu rugi | uncontracted |  |  |
| paraul jaristea mare | uncontracted |  |  |
| paraul lupul | uncontracted |  |  |
| paraul pacatoasa | uncontracted |  |  |
| paraul socilor | uncontracted |  |  |
| paraul stanii | uncontracted |  |  |
| paraul trinkbach | uncontracted |  |  |
| paraul ursului | uncontracted |  |  |
| parcalabul | uncontracted |  |  |
| pascoaia | uncontracted |  |  |
| pietroasa | uncontracted |  |  |
| pietrosul | uncontracted |  |  |
| plesoaia | uncontracted |  |  |
| pociovalistea | uncontracted |  |  |
| porumbacel | uncontracted |  |  |
| porumbacu | uncontracted |  |  |
| priboaia | uncontracted |  |  |
| priboiasa | uncontracted |  |  |
| priporul | uncontracted |  |  |
| randibou | uncontracted |  |  |
| raul cibin | present | APS AQUA CRISIUS | multiway_chain |
| raul racovita | uncontracted |  |  |
| raul scorei | uncontracted |  |  |
| raul sec | uncontracted |  |  |
| raul valea sapunului | uncontracted |  |  |
| rausor | present | Direcția Silvică Argeș | romsilva_map:exact |
| reussbach | uncontracted |  |  |
| robesti | present | AJVPS VÂLCEA |  |
| rosbav | uncontracted |  |  |
| rosia | present | AJVPS BIHOR |  |
| rudarul | uncontracted |  |  |
| rusciori | uncontracted |  |  |
| sadu | present | FLY FISHING CLUB SIBIU | audit_match:prefix |
| saracinul | uncontracted |  |  |
| sarata | present | AJVPS BOTOȘANI |  |
| sasa mandrei | uncontracted |  |  |
| sebes | present | AJVPS ALBA |  |
| sevis | uncontracted |  |  |
| sibisel | present | Direcția Silvică Hunedoara | romsilva_map:exact |
| silistea | uncontracted |  |  |
| sipotul | uncontracted |  |  |
| stanisoara | uncontracted |  |  |
| steaza | uncontracted |  |  |
| stramba | present | AJPS Brașov |  |
| streaurile | uncontracted |  |  |
| talmacut | present | FLY FISHING CLUB SIBIU |  |
| tatarul | uncontracted |  |  |
| tocile | uncontracted |  |  |
| topolog | present | AJVPS VÂLCEA |  |
| topologel | uncontracted |  |  |
| trestia | uncontracted |  |  |
| uria | present | AJVPS VÂLCEA |  |
| valea bagau | uncontracted |  |  |
| valea bobocea | uncontracted |  |  |
| valea bradului | uncontracted |  |  |
| valea bulzului | uncontracted |  |  |
| valea calului | uncontracted |  |  |
| valea campului | uncontracted |  |  |
| valea caselor | present | AJVPS ALBA |  |
| valea cerbesti | uncontracted |  |  |
| valea ciortea | uncontracted |  |  |
| valea ciurtea | uncontracted |  |  |
| valea coconciu | uncontracted |  |  |
| valea cotilor | uncontracted |  |  |
| valea cu rapi | uncontracted |  |  |
| valea de jos | present | FLY FISHING CLUB SIBIU |  |
| valea de sub robu | uncontracted |  |  |
| valea fagului | uncontracted |  |  |
| valea fata curpenului | uncontracted |  |  |
| valea florii | uncontracted |  |  |
| valea frasinului | uncontracted |  |  |
| valea fratelui | uncontracted |  |  |
| valea galbena | uncontracted |  |  |
| valea gaurei | uncontracted |  |  |
| valea jaristea mare | uncontracted |  |  |
| valea leului | uncontracted |  |  |
| valea lotrisor | present | AJVPS VÂLCEA |  |
| valea lui fanica | uncontracted |  |  |
| valea lui fatul | uncontracted |  |  |
| valea lui iacob | uncontracted |  |  |
| valea lui ionelu | uncontracted |  |  |
| valea lui vlad | uncontracted |  |  |
| valea lunga | uncontracted |  |  |
| valea lupului | uncontracted |  |  |
| valea mesteacanului | uncontracted |  |  |
| valea miclaus | uncontracted |  |  |
| valea murgaciu | uncontracted |  |  |
| valea negoeasca | uncontracted |  |  |
| valea negrului | uncontracted |  |  |
| valea paltinului | uncontracted |  |  |
| valea pesterii | uncontracted |  |  |
| valea pietricelelor | uncontracted |  |  |
| valea plaiului | uncontracted |  |  |
| valea priboioasei | uncontracted |  |  |
| valea repezoi | uncontracted |  |  |
| valea robului | uncontracted |  |  |
| valea satului | uncontracted |  |  |
| valea scaunelelor | uncontracted |  |  |
| valea scursurii | uncontracted |  |  |
| valea smida mare | uncontracted |  |  |
| valea smida mica | uncontracted |  |  |
| valea socilor | uncontracted |  |  |
| valea sparta | uncontracted |  |  |
| valea spranea | uncontracted |  |  |
| valea sterminoasa | uncontracted |  |  |
| valea strambanului | uncontracted |  |  |
| valea sturii mari | uncontracted |  |  |
| valea teleleu | uncontracted |  |  |
| valea vladimirului | uncontracted |  |  |
| vasilatu | uncontracted |  |  |
| vatafu | uncontracted |  |  |
| visa | uncontracted |  |  |
| voinesita | uncontracted |  |  |

### Celulă 45.4-45.9N, 24.5-25.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| arges | present | AJVPS DÂMBOVIȚA |  |
| arpas | present | Direcția Silvică Sibiu | romsilva_map:exact |
| arpasel | uncontracted |  |  |
| arpaselul | uncontracted |  |  |
| arpasu mare | uncontracted |  |  |
| balea | present | Direcția Silvică Sibiu |  |
| bandea | uncontracted |  |  |
| batrana | uncontracted |  |  |
| berivoi | present | AVPS FĂGĂRAȘ |  |
| boarcas | uncontracted |  |  |
| bratia | present | Direcția Silvică Argeș | romsilva_map:exact |
| bratila | uncontracted |  |  |
| brescioara | uncontracted |  |  |
| buda | present | Direcția Silvică Argeș | romsilva_map:exact |
| capra | present | Direcția Silvică Argeș | romsilva_map:exact |
| carligele | uncontracted |  |  |
| cartisoara | uncontracted |  |  |
| cernatu | uncontracted |  |  |
| cincu | uncontracted |  |  |
| coltii lui andrei mari | uncontracted |  |  |
| corbul ucii | uncontracted |  |  |
| corbul vistei | uncontracted |  |  |
| cornea | uncontracted |  |  |
| dambovita | present | AJVPS DÂMBOVIȚA |  |
| dejani | present | AVPS FĂGĂRAȘ | audit_match:exact |
| dobroneagu | uncontracted |  |  |
| draghina | uncontracted |  |  |
| dragus | uncontracted |  |  |
| dridif | uncontracted |  |  |
| galasescu mare | uncontracted |  |  |
| galasescu mic | uncontracted |  |  |
| gostaia | uncontracted |  |  |
| hartibaciu | present | AJVPS SIBIU |  |
| iezerul mare | present | FLY FISHING CLUB SIBIU | bbox_fix:lake:Iezerul Mare |
| izorul groapele | uncontracted |  |  |
| izvorul caprei | uncontracted |  |  |
| izvorul cremenei | uncontracted |  |  |
| izvorul huluba | uncontracted |  |  |
| izvorul ludisorului | uncontracted |  |  |
| izvorul moldoveanu | uncontracted |  |  |
| izvorul negoiului | uncontracted |  |  |
| izvorul parsului | uncontracted |  |  |
| izvorul podeanului | uncontracted |  |  |
| izvorul podu giurgiului | uncontracted |  |  |
| izvorul rausorului | uncontracted |  |  |
| izvorul rosu | present | Direcția Silvică Harghita |  |
| izvorul scarii | uncontracted |  |  |
| laita | present | Direcția Silvică Sibiu | romsilva_map:exact |
| lisa | uncontracted |  |  |
| manastirii lake | uncontracted |  |  |
| mircea | uncontracted |  |  |
| netot | uncontracted |  |  |
| olt | present | AJVPS OLT |  |
| oltet | present | AJVPS VÂLCEA |  |
| opatu | uncontracted |  |  |
| paltinu | present | A.PENEȘ CURCANUL | bbox_fix:lake:Lacul Paltinu |
| paraul caltun | uncontracted |  |  |
| paraul calului | uncontracted |  |  |
| paraul crintei | uncontracted |  |  |
| paraul doamnei | present | AJVPS ARGEȘ | audit_match:prefix |
| paraul ferastraul | uncontracted |  |  |
| paraul izvorul | present-hidden | AJVPS BISTRIȚA-NĂSĂUD |  |
| paraul jneapanului | uncontracted |  |  |
| paraul larg | uncontracted |  |  |
| paraul lespezi | uncontracted |  |  |
| paraul mircea | uncontracted |  |  |
| paraul orzaneaua mare | uncontracted |  |  |
| paraul orzaneaua mica | uncontracted |  |  |
| paraul piatra caprei | uncontracted |  |  |
| paraul politei | uncontracted |  |  |
| paraul racorelelor | uncontracted |  |  |
| paraul raiosu | uncontracted |  |  |
| paraul vartejelor | uncontracted |  |  |
| paraul vartejurilor | uncontracted |  |  |
| paraul vladului | uncontracted |  |  |
| piscanu | uncontracted |  |  |
| piscul | uncontracted |  |  |
| podragu | present | Direcția Silvică Sibiu | bbox_fix:lake:Lacul Podragu |
| pojorta | uncontracted |  |  |
| porumbacel | uncontracted |  |  |
| porumbacu | uncontracted |  |  |
| racovita | uncontracted |  |  |
| raul copaceoasa | uncontracted |  |  |
| raul doamnei | present | AJVPS ARGEȘ | audit_match:prefix |
| raul racovita | uncontracted |  |  |
| raul scorei | uncontracted |  |  |
| raul sebes | present | AJVPS MUREȘ | anpa_map:sweep:sebes |
| rausorul | uncontracted |  |  |
| resch bach | uncontracted |  |  |
| sambata | uncontracted |  |  |
| sarata | present | AJVPS BOTOȘANI |  |
| savastreni | uncontracted |  |  |
| seaca | uncontracted |  |  |
| topolog | present | AJVPS VÂLCEA |  |
| ucea | present | AVPS FĂGĂRAȘ | audit_match:prefix |
| ucisoara | uncontracted |  |  |
| urlea | present | APS AQUA CRISIUS | bbox_fix:lake:Lacul Urlea |
| valea cu pesti | uncontracted |  |  |
| valea izvorul sec | uncontracted |  |  |
| valea leaota | uncontracted |  |  |
| valea lutele | uncontracted |  |  |
| valea mazgavul | uncontracted |  |  |
| valea museteica | uncontracted |  |  |
| valea pisica | uncontracted |  |  |
| valea rea | uncontracted |  |  |
| valea stancoasa | uncontracted |  |  |
| valea voievodeni | uncontracted |  |  |
| valea zarna | uncontracted |  |  |
| valsan | present | AJVPS ARGEȘ | audit_match:prefix |
| vasalatu | uncontracted |  |  |
| vistea | present | AVPS FĂGĂRAȘ |  |
| vistea mare | present | AVPS FĂGĂRAȘ |  |
| vistisoara | uncontracted |  |  |
| voila | uncontracted |  |  |
| zanoguta | uncontracted |  |  |
| zarna | uncontracted |  |  |
| zbuciumatul | uncontracted |  |  |

### Celulă 45.4-45.9N, 25.0-25.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| albisoara branei | uncontracted |  |  |
| albisoara crucii | uncontracted |  |  |
| albisoara gemenelor | uncontracted |  |  |
| aninoasa | uncontracted |  |  |
| argesel | present | AJVPS ARGEȘ | audit_match:prefix |
| bangaleasa | uncontracted |  |  |
| baratu | uncontracted |  |  |
| barsa | present | AJPS BRAȘOV |  |
| barsa fierului | uncontracted |  |  |
| barsa grosetului | uncontracted |  |  |
| barsa lui bucur | uncontracted |  |  |
| barsa tamasului | uncontracted |  |  |
| batrana | uncontracted |  |  |
| bidul | uncontracted |  |  |
| biserica | uncontracted |  |  |
| blidul uriasilor | uncontracted |  |  |
| bozii | uncontracted |  |  |
| calul | uncontracted |  |  |
| canionul cioringa mare | uncontracted |  |  |
| canionul pietrelor | uncontracted |  |  |
| carligatea | uncontracted |  |  |
| cheia | present | AJVPS VÂLCEA |  |
| ciocracu | uncontracted |  |  |
| coltii lui andrei mari | uncontracted |  |  |
| coltii lui andrei mici | uncontracted |  |  |
| comana | present | Direcția Silvică Brașov | romsilva_map:exact |
| cretu | uncontracted |  |  |
| crizbav | uncontracted |  |  |
| cuca | uncontracted |  |  |
| dambovicioara | present | Direcția Silvică Argeș | romsilva_map:exact |
| dambovita | present | AJVPS DÂMBOVIȚA |  |
| felmer | uncontracted |  |  |
| fracea | uncontracted |  |  |
| galbinele fir secundar | uncontracted |  |  |
| geamana | present | AJPS Brașov |  |
| ghimbasel | uncontracted |  |  |
| gradistea | present | AJVPS HUNEDOARA | audit_match:override |
| grid | uncontracted |  |  |
| homorod | present | AJPS Brașov |  |
| hornul coamei | uncontracted |  |  |
| hornul din valea pietrelor | uncontracted |  |  |
| hornul mic | uncontracted |  |  |
| hornul nisipos | uncontracted |  |  |
| hornul pamantos | uncontracted |  |  |
| hornurile costilei | uncontracted |  |  |
| hornurile vaii seci | uncontracted |  |  |
| hotarul | uncontracted |  |  |
| iadul vaii albe | uncontracted |  |  |
| ialomita | present | AJVPS DÂMBOVIȚA |  |
| izvorul hotarului | uncontracted |  |  |
| izvorul huluba | uncontracted |  |  |
| izvorul lespezi | uncontracted |  |  |
| lupul | uncontracted |  |  |
| maierus | present | AJPS Brașov |  |
| malaiesti | uncontracted |  |  |
| mandra | uncontracted |  |  |
| merezu | uncontracted |  |  |
| moieciul rece | uncontracted |  |  |
| musuroaiele | uncontracted |  |  |
| olt | present | AJVPS OLT |  |
| p coltului scris | uncontracted |  |  |
| padina lancii | uncontracted |  |  |
| padina lui calinet | uncontracted |  |  |
| padina priporului | uncontracted |  |  |
| panicel | uncontracted |  |  |
| panicelul | uncontracted |  |  |
| parau | uncontracted |  |  |
| paraul bogata | present | Direcția Silvică Brașov | romsilva_map:exact |
| paraul caldarilor | uncontracted |  |  |
| paraul calul balan | uncontracted |  |  |
| paraul mare | present | AVPS MIERCUREA-CIUC |  |
| paraul mataoana | uncontracted |  |  |
| paraul mic | present | AVPS MIERCUREA-CIUC |  |
| paraul noaghiei | uncontracted |  |  |
| paraul noghia | uncontracted |  |  |
| paraul pesterii | uncontracted |  |  |
| paraul stancioiu | uncontracted |  |  |
| paraul stevioara | uncontracted |  |  |
| paraul tisei | uncontracted |  |  |
| paraul vulturul | uncontracted |  |  |
| pietrele albe | uncontracted |  |  |
| plopoasa | uncontracted |  |  |
| poarta | uncontracted |  |  |
| purcaru | uncontracted |  |  |
| rapa crucii | uncontracted |  |  |
| rapa mare | uncontracted |  |  |
| rapa zapezii | uncontracted |  |  |
| raul copaceoasa | uncontracted |  |  |
| raul sebes | present | AJVPS MUREȘ | anpa_map:sweep:sebes |
| raul targului | present | AJVPS ARGEȘ | audit_match:prefix |
| raul venetia | present | AVPS FĂGĂRAȘ |  |
| raul zarnestilor | uncontracted |  |  |
| rausor | present | Direcția Silvică Argeș | romsilva_map:exact |
| rausorul | uncontracted |  |  |
| rudarita mare | uncontracted |  |  |
| rudarita mica | uncontracted |  |  |
| scurta | uncontracted |  |  |
| seciu | uncontracted |  |  |
| sercaitei | uncontracted |  |  |
| simon | uncontracted |  |  |
| sinca | uncontracted |  |  |
| sipotul | uncontracted |  |  |
| sistoaca bucurei | uncontracted |  |  |
| sistoaca dracilor | uncontracted |  |  |
| sistoaca obarsiei | uncontracted |  |  |
| sistoaca rosie | uncontracted |  |  |
| sohodol | present | A.CERBUL CARPATIN | audit_match:char0.88 |
| spalatura vaii seci | uncontracted |  |  |
| spintecatura vaii seci | uncontracted |  |  |
| stramba | present | AJPS Brașov |  |
| stramsoara | uncontracted |  |  |
| sughina | uncontracted |  |  |
| tambura | uncontracted |  |  |
| tiganesti | uncontracted |  |  |
| tohanita | uncontracted |  |  |
| turcu | uncontracted |  |  |
| urlatoarea clincei | uncontracted |  |  |
| v hornului | uncontracted |  |  |
| vacarea | uncontracted |  |  |
| vadul rosu | uncontracted |  |  |
| valc policandrului | uncontracted |  |  |
| valc rapei mici | uncontracted |  |  |
| valcelul bujorului | uncontracted |  |  |
| valcelul de sub perete | uncontracted |  |  |
| valcelul de sub varf | uncontracted |  |  |
| valcelul grohotisului | uncontracted |  |  |
| valcelul gutanului | uncontracted |  |  |
| valcelul indracit | uncontracted |  |  |
| valcelul lespezilor | uncontracted |  |  |
| valcelul mortului | uncontracted |  |  |
| valcelul obraznic | uncontracted |  |  |
| valcelul portitelor | uncontracted |  |  |
| valea adanca | uncontracted |  |  |
| valea alba | uncontracted |  |  |
| valea ancului | uncontracted |  |  |
| valea barbuletu | uncontracted |  |  |
| valea barbului | uncontracted |  |  |
| valea barnei | uncontracted |  |  |
| valea batrana | uncontracted |  |  |
| valea boteanu | uncontracted |  |  |
| valea boului | uncontracted |  |  |
| valea bratoaia | uncontracted |  |  |
| valea brustuletului | uncontracted |  |  |
| valea bucsoiului | uncontracted |  |  |
| valea bugheanului | uncontracted |  |  |
| valea calului | uncontracted |  |  |
| valea caprelor | uncontracted |  |  |
| valea carbunelui | uncontracted |  |  |
| valea caselor | present | AJVPS ALBA |  |
| valea catunului | uncontracted |  |  |
| valea cerbului | uncontracted |  |  |
| valea cetatii | uncontracted |  |  |
| valea cheii | uncontracted |  |  |
| valea ciocanului | uncontracted |  |  |
| valea coacazei | uncontracted |  |  |
| valea coltilor | uncontracted |  |  |
| valea comisului | uncontracted |  |  |
| valea comorilor | uncontracted |  |  |
| valea costilei | uncontracted |  |  |
| valea crapaturii | uncontracted |  |  |
| valea crovului | uncontracted |  |  |
| valea cu apa | uncontracted |  |  |
| valea cu cale | uncontracted |  |  |
| valea cu calii | uncontracted |  |  |
| valea curmaturii | uncontracted |  |  |
| valea curugii | uncontracted |  |  |
| valea doamnele | uncontracted |  |  |
| valea fundatica | uncontracted |  |  |
| valea galbenele | uncontracted |  |  |
| valea gangului | uncontracted |  |  |
| valea ganii | uncontracted |  |  |
| valea gaunaoasa | uncontracted |  |  |
| valea gaura | uncontracted |  |  |
| valea giuvala | uncontracted |  |  |
| valea gradistei | uncontracted |  |  |
| valea grohotisului | uncontracted |  |  |
| valea gutanu | uncontracted |  |  |
| valea holbav | uncontracted |  |  |
| valea iezilor | uncontracted |  |  |
| valea izvorul sec | uncontracted |  |  |
| valea jepilor | uncontracted |  |  |
| valea lacului | present | AJVPS TIMIȘ |  |
| valea larga | uncontracted |  |  |
| valea lespezi | uncontracted |  |  |
| valea lui anton | uncontracted |  |  |
| valea lui dobre | uncontracted |  |  |
| valea lui geanta | uncontracted |  |  |
| valea lui ivan | uncontracted |  |  |
| valea lui lamba | uncontracted |  |  |
| valea lui nan | uncontracted |  |  |
| valea lui smit | uncontracted |  |  |
| valea lui stinghie | uncontracted |  |  |
| valea lunga | uncontracted |  |  |
| valea lutele | uncontracted |  |  |
| valea magurii | uncontracted |  |  |
| valea malaiesti | uncontracted |  |  |
| valea malinului | uncontracted |  |  |
| valea mara | present | AJVPS MARAMUREȘ |  |
| valea martoiu | uncontracted |  |  |
| valea morarului | uncontracted |  |  |
| valea muierii | uncontracted |  |  |
| valea nisipu | uncontracted |  |  |
| valea pietrelor | uncontracted |  |  |
| valea pietrelor principal | uncontracted |  |  |
| valea pietrelor secundar | uncontracted |  |  |
| valea podurilor | uncontracted |  |  |
| valea poienii | uncontracted |  |  |
| valea popii | uncontracted |  |  |
| valea prapastiilor | uncontracted |  |  |
| valea pravalelor | uncontracted |  |  |
| valea prepeleacului | uncontracted |  |  |
| valea priponului | uncontracted |  |  |
| valea rea | uncontracted |  |  |
| valea rece | uncontracted |  |  |
| valea rogoazei | uncontracted |  |  |
| valea rogozului | uncontracted |  |  |
| valea rudaritei | uncontracted |  |  |
| valea sariturii | uncontracted |  |  |
| valea sasului | uncontracted |  |  |
| valea sasului mic | uncontracted |  |  |
| valea scorusilor | uncontracted |  |  |
| valea seaca | uncontracted |  |  |
| valea seaca a costilei | uncontracted |  |  |
| valea seaca a pietrelor | uncontracted |  |  |
| valea spinarii | uncontracted |  |  |
| valea spirla | uncontracted |  |  |
| valea spumoasa | uncontracted |  |  |
| valea stamboru | uncontracted |  |  |
| valea staneui | uncontracted |  |  |
| valea stanii | uncontracted |  |  |
| valea tapului | uncontracted |  |  |
| valea targului | present | AJVPS ARGEȘ | audit_match:prefix |
| valea tigai | uncontracted |  |  |
| valea tiganesti | uncontracted |  |  |
| valea tiganului | uncontracted |  |  |
| valea tudoresti | uncontracted |  |  |
| valea turnul | uncontracted |  |  |
| valea urdei | uncontracted |  |  |
| valea ursului | uncontracted |  |  |
| valea urzici | uncontracted |  |  |
| valea urzicii | uncontracted |  |  |
| valea velicanu | uncontracted |  |  |
| valea verde | uncontracted |  |  |
| valea viteilor | uncontracted |  |  |
| valea vladusca | uncontracted |  |  |
| valea vulcanita | uncontracted |  |  |
| valea zbarcioarei | uncontracted |  |  |
| vilcelul poienitei | uncontracted |  |  |
| vladusca | uncontracted |  |  |
| vulcanita | uncontracted |  |  |

### Celulă 45.4-45.9N, 25.5-26.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| albisoara hornurilor | uncontracted |  |  |
| albisoara strungii | uncontracted |  |  |
| albisoara turnurilor | uncontracted |  |  |
| arcus | uncontracted |  |  |
| azuga | uncontracted |  |  |
| babarunca | uncontracted |  |  |
| babes | uncontracted |  |  |
| baiu mic | uncontracted |  |  |
| barsa | present | AJPS BRAȘOV |  |
| bradatelul | uncontracted |  |  |
| bratocea | uncontracted |  |  |
| buzau | present | AJVPS Brăila |  |
| canal drenaj | uncontracted |  |  |
| canalul timis | present | AJVPS TIMIȘ |  |
| capra | present | Direcția Silvică Argeș | romsilva_map:exact |
| capra mare | present | Direcția Silvică Argeș | romsilva_map:exact |
| capra mica | present | Direcția Silvică Argeș | romsilva_map:exact |
| casaria | uncontracted |  |  |
| cazacul | uncontracted |  |  |
| cenuseroaia | uncontracted |  |  |
| cernatul | uncontracted |  |  |
| cheita | uncontracted |  |  |
| chirusca seaca | uncontracted |  |  |
| ciclau | uncontracted |  |  |
| ciudion | uncontracted |  |  |
| covasna | present | AJVPS COVASNA |  |
| cracul stang | uncontracted |  |  |
| crizbav | uncontracted |  |  |
| cusurus | uncontracted |  |  |
| dalghiu | uncontracted |  |  |
| danube | uncontracted |  |  |
| debren | uncontracted |  |  |
| dobarlau | uncontracted |  |  |
| doftana | uncontracted |  |  |
| doftana ardeleana | uncontracted |  |  |
| doftanita | uncontracted |  |  |
| dracul | uncontracted |  |  |
| durbav | uncontracted |  |  |
| dutca | uncontracted |  |  |
| fotos | uncontracted |  |  |
| franca | uncontracted |  |  |
| garcin | uncontracted |  |  |
| garcinul mare | uncontracted |  |  |
| garcinul mic | uncontracted |  |  |
| geamana | present | AJPS Brașov |  |
| ghebanului | uncontracted |  |  |
| ghimbasel | uncontracted |  |  |
| glodeasa | uncontracted |  |  |
| glodul | uncontracted |  |  |
| graft | uncontracted |  |  |
| groapa cu var | uncontracted |  |  |
| groapa de aur | uncontracted |  |  |
| groapa lui simion | uncontracted |  |  |
| haghig | uncontracted |  |  |
| hoagele urzicii | uncontracted |  |  |
| homorod | present | AJPS Brașov |  |
| hornurile vaii seci | uncontracted |  |  |
| hotarul | uncontracted |  |  |
| izvorul lui carstocea | uncontracted |  |  |
| izvorul mioarelor | uncontracted |  |  |
| kokenyes | uncontracted |  |  |
| lamba mare | uncontracted |  |  |
| larga mare | uncontracted |  |  |
| larga mica | uncontracted |  |  |
| limbaselul | uncontracted |  |  |
| limbaselul mare | uncontracted |  |  |
| limbaselul mic | uncontracted |  |  |
| lisnau | uncontracted |  |  |
| maierus | present | AJPS Brașov |  |
| mogos | uncontracted |  |  |
| musita | uncontracted |  |  |
| nanu | uncontracted |  |  |
| oaban | uncontracted |  |  |
| oabanul de jos | present | FLY FISHING CLUB SIBIU |  |
| oabanul de sus | present | FLY FISHING CLUB SIBIU |  |
| ograda frasinului | uncontracted |  |  |
| olareasa | uncontracted |  |  |
| olt | present | AJPS Brașov |  |
| orjogoaia | uncontracted |  |  |
| paraie | uncontracted |  |  |
| parau | uncontracted |  |  |
| paraul alb | present | AJVPS CARAȘ-SEVERIN | multiway_chain |
| paraul berii | uncontracted |  |  |
| paraul hotilor | uncontracted |  |  |
| paraul laptelui | uncontracted |  |  |
| paraul lui balan | uncontracted |  |  |
| paraul lui chelemec | uncontracted |  |  |
| paraul lui isac | uncontracted |  |  |
| paraul mic | present | AVPS MIERCUREA-CIUC |  |
| paraul padureni | present | AJVPS COVASNA | audit_match:exact |
| paraul polistoaca | uncontracted |  |  |
| paraul porcului | uncontracted |  |  |
| paraul rosu | present | Direcția Silvică Harghita |  |
| paraul stanii | uncontracted |  |  |
| paraul sterp | uncontracted |  |  |
| paraul tok | uncontracted |  |  |
| paraul valea joitei | uncontracted |  |  |
| piscul cu apa | uncontracted |  |  |
| porumbele | uncontracted |  |  |
| prahova | present | AJVPS PRAHOVA | audit_match:prefix |
| ramura mica | uncontracted |  |  |
| raul negru | present | AJVPS COVASNA | audit_match:prefix |
| raul plopilor | uncontracted |  |  |
| raul tarlung | uncontracted |  |  |
| retevoiu | uncontracted |  |  |
| richieiul | uncontracted |  |  |
| rusu | uncontracted |  |  |
| sapte scari | uncontracted |  |  |
| satului | uncontracted |  |  |
| semeria | uncontracted |  |  |
| simeria | uncontracted |  |  |
| sipoaia | uncontracted |  |  |
| sipot | uncontracted |  |  |
| spalatura vaii seci | uncontracted |  |  |
| spintecatura vaii seci | uncontracted |  |  |
| strambu | uncontracted |  |  |
| sugas | uncontracted |  |  |
| susai | uncontracted |  |  |
| tampa | uncontracted |  |  |
| tarlung | uncontracted |  |  |
| teleajen | present | AJVPS PRAHOVA | audit_match:prefix |
| telejenel | present | Direcția Silvică Prahova | romsilva_map:exact |
| teliu | uncontracted |  |  |
| timis | present | AJVPS TIMIȘ |  |
| timisul sec de sus | uncontracted |  |  |
| timisul sec mic | uncontracted |  |  |
| unghia mica | uncontracted |  |  |
| urlatelul | uncontracted |  |  |
| urlatoarea | uncontracted |  |  |
| urlatoarea mare | uncontracted |  |  |
| urlatoarea mica | uncontracted |  |  |
| urlatul mare | uncontracted |  |  |
| urlatul mic | uncontracted |  |  |
| ursilor | uncontracted |  |  |
| ursoaia mare | uncontracted |  |  |
| ursoaia mica | uncontracted |  |  |
| vadul rosu | uncontracted |  |  |
| valc pietros | uncontracted |  |  |
| valc policandrului | uncontracted |  |  |
| valcelul lui schmauz | uncontracted |  |  |
| valcelul mortului | uncontracted |  |  |
| valcelul picaturii | uncontracted |  |  |
| valcelul spanzurat | uncontracted |  |  |
| valea alba | uncontracted |  |  |
| valea boului | uncontracted |  |  |
| valea bradetului | uncontracted |  |  |
| valea cailor | uncontracted |  |  |
| valea calda | uncontracted |  |  |
| valea calului | uncontracted |  |  |
| valea canelor | uncontracted |  |  |
| valea catepu | uncontracted |  |  |
| valea ceausoaiei | uncontracted |  |  |
| valea cerbului | uncontracted |  |  |
| valea cetatii | uncontracted |  |  |
| valea cheii | uncontracted |  |  |
| valea chilera | uncontracted |  |  |
| valea costilei | uncontracted |  |  |
| valea cu apa | uncontracted |  |  |
| valea de aur | uncontracted |  |  |
| valea dracului | uncontracted |  |  |
| valea draga | uncontracted |  |  |
| valea fabricii | uncontracted |  |  |
| valea fanetii | uncontracted |  |  |
| valea feriga | uncontracted |  |  |
| valea fetei | uncontracted |  |  |
| valea galbenele | uncontracted |  |  |
| valea galmei | uncontracted |  |  |
| valea gorita | uncontracted |  |  |
| valea grecului | uncontracted |  |  |
| valea groapa lunga | uncontracted |  |  |
| valea hotilor | uncontracted |  |  |
| valea iadului | present-hidden | Direcția Silvică Bihor | romsilva_map |
| valea jepilor | uncontracted |  |  |
| valea jilip | uncontracted |  |  |
| valea lacul rosu | uncontracted |  |  |
| valea leucii | uncontracted |  |  |
| valea lui dumitru | uncontracted |  |  |
| valea lui manole | uncontracted |  |  |
| valea lui stere | uncontracted |  |  |
| valea lui zangur | uncontracted |  |  |
| valea lunga | uncontracted |  |  |
| valea mare | present | AVPS MIERCUREA-CIUC |  |
| valea marului | uncontracted |  |  |
| valea maturarului | uncontracted |  |  |
| valea mocarlicea | uncontracted |  |  |
| valea morarului | uncontracted |  |  |
| valea neagra | present | Direcția Silvică Suceava | romsilva_map:group-shares-course |
| valea neamtului | uncontracted |  |  |
| valea nisipului | uncontracted |  |  |
| valea ograda | uncontracted |  |  |
| valea paraul miklos | uncontracted |  |  |
| valea pietrei mici | uncontracted |  |  |
| valea poienii | uncontracted |  |  |
| valea popii | uncontracted |  |  |
| valea postavaru | uncontracted |  |  |
| valea prundului | uncontracted |  |  |
| valea putreda | uncontracted |  |  |
| valea racadau | uncontracted |  |  |
| valea rasnoavei | uncontracted |  |  |
| valea rece | uncontracted |  |  |
| valea rece de jos | present | FLY FISHING CLUB SIBIU |  |
| valea rosie | uncontracted |  |  |
| valea satului | uncontracted |  |  |
| valea seaca | uncontracted |  |  |
| valea seaca a caraimanului | uncontracted |  |  |
| valea seaca dintre clai | uncontracted |  |  |
| valea secuianca | uncontracted |  |  |
| valea sindilei | uncontracted |  |  |
| valea sitei | uncontracted |  |  |
| valea spumoasa | uncontracted |  |  |
| valea stanei | uncontracted |  |  |
| valea stanei mari | uncontracted |  |  |
| valea stanei mici | uncontracted |  |  |
| valea steviei | uncontracted |  |  |
| valea sticlariei | uncontracted |  |  |
| valea surdic | uncontracted |  |  |
| valea tei | uncontracted |  |  |
| valea teslei | uncontracted |  |  |
| valea tigailor | uncontracted |  |  |
| valea tocilita | uncontracted |  |  |
| valea turcului | uncontracted |  |  |
| valea unghia mare | uncontracted |  |  |
| valea urechii | uncontracted |  |  |
| vama mare | uncontracted |  |  |
| vama mica | uncontracted |  |  |
| vanga mare | uncontracted |  |  |
| vanga mica | uncontracted |  |  |
| varna mare | uncontracted |  |  |
| varna mica | uncontracted |  |  |
| vilcelul poienitei | uncontracted |  |  |
| vladet | uncontracted |  |  |
| vulcanita | uncontracted |  |  |
| zaganu | uncontracted |  |  |
| zanoaga | present | Direcția Silvică Hunedoara | bbox_fix:lake:Lacul Zănoaga Mare |
| zizin | uncontracted |  |  |

### Celulă 45.4-45.9N, 26.0-26.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| balaneasa | uncontracted |  |  |
| basca chiojd | uncontracted |  |  |
| basca mare | present | Direcția Silvică Buzău | romsilva_sector_split |
| basca mica | present | Direcția Silvică Buzău | romsilva_sector_split |
| basca rosiliei | uncontracted |  |  |
| boncuta | uncontracted |  |  |
| buzaiel | uncontracted |  |  |
| buzau | present | AJVPS Brăila |  |
| cernatul | uncontracted |  |  |
| chiojdu | uncontracted |  |  |
| ciclau | uncontracted |  |  |
| covasna | present | AJVPS COVASNA |  |
| crasna | present | AJVPS VASLUI | anpa_map:sweep:crasna |
| danube | uncontracted |  |  |
| floroita | uncontracted |  |  |
| fundul paraului | uncontracted |  |  |
| galmeica | uncontracted |  |  |
| gorul | uncontracted |  |  |
| horgasz | uncontracted |  |  |
| mardanu | uncontracted |  |  |
| meszpatak | uncontracted |  |  |
| nehoiu sec | uncontracted |  |  |
| papauti | uncontracted |  |  |
| parau mare | present | AVPS MIERCUREA-CIUC |  |
| paraul alb | present | AJVPS CARAȘ-SEVERIN | multiway_chain |
| paraul cetatii | uncontracted |  |  |
| paraul fetei | uncontracted |  |  |
| paraul mreaja | uncontracted |  |  |
| paraul plostina | uncontracted |  |  |
| pastareata | uncontracted |  |  |
| pava | uncontracted |  |  |
| piriul cupanelului | uncontracted |  |  |
| piriul stana lui rusu | uncontracted |  |  |
| preseaca | uncontracted |  |  |
| putna | present | AJVPS VRANCEA |  |
| rastoaca | uncontracted |  |  |
| raul buzau | present | AJVPS Brăila |  |
| raul cernat | uncontracted |  |  |
| raul negru | present | AJVPS COVASNA | audit_match:prefix |
| siriu | uncontracted |  |  |
| siriul mic | present | AJVPS BUZĂU | siriul_mic_attach (t_8c4b2d08) |
| strambu | uncontracted |  |  |
| telciu | uncontracted |  |  |
| telejenel | present | Direcția Silvică Prahova | romsilva_map:exact |
| tisita aurie | uncontracted |  |  |
| tisita mare | present | Direcția Silvică Vrancea | romsilva_map:exact |
| urlatoarea | uncontracted |  |  |
| urlatoarea mare | uncontracted |  |  |
| valea milea | uncontracted |  |  |
| valea stanei | uncontracted |  |  |
| zabala | present | AJVPS VRANCEA | audit_match:prefix |
| zagon | uncontracted |  |  |
| zagonul mare | uncontracted |  |  |
| zagonul mic | uncontracted |  |  |
| zavoarele | uncontracted |  |  |

### Celulă 45.4-45.9N, 26.5-27.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bahna zaganului | uncontracted |  |  |
| balaneasa | uncontracted |  |  |
| barbinti | uncontracted |  |  |
| basca mica | present | Direcția Silvică Buzău | romsilva_sector_split |
| bozu | uncontracted |  |  |
| calnau | uncontracted |  |  |
| cristianu mic | uncontracted |  |  |
| danube | uncontracted |  |  |
| gradina | uncontracted |  |  |
| izvorul furului | uncontracted |  |  |
| izvorul malu rosu | uncontracted |  |  |
| izvorul oprii | uncontracted |  |  |
| izvorul pietrelor | uncontracted |  |  |
| izvorul rau | uncontracted |  |  |
| izvorul sarat | uncontracted |  |  |
| jghiab | uncontracted |  |  |
| meledic | uncontracted |  |  |
| milcov | uncontracted |  |  |
| motnau | uncontracted |  |  |
| motocina | uncontracted |  |  |
| naruja | present | AJVPS VRANCEA | multiway_chain |
| paraul bahna tisei | uncontracted |  |  |
| paraul brebu | uncontracted |  |  |
| paraul clajna | uncontracted |  |  |
| paraul cociu zaganului | uncontracted |  |  |
| paraul fantanitei | uncontracted |  |  |
| paraul gradina | uncontracted |  |  |
| paraul jaristei | uncontracted |  |  |
| paraul lespezii | uncontracted |  |  |
| paraul lui baraboi | uncontracted |  |  |
| paraul lui ilie | uncontracted |  |  |
| paraul lui nastase | uncontracted |  |  |
| paraul lunii | uncontracted |  |  |
| paraul macesu | uncontracted |  |  |
| paraul niculesii | uncontracted |  |  |
| paraul plostina | uncontracted |  |  |
| paraul poienii greului | uncontracted |  |  |
| paraul puscariei | uncontracted |  |  |
| paraul puturosu | uncontracted |  |  |
| paraul rabojului | uncontracted |  |  |
| paraul runcuri | uncontracted |  |  |
| paraul sarat | uncontracted |  |  |
| paraul saratel | uncontracted |  |  |
| paraul sarcea | uncontracted |  |  |
| paraul seciului | uncontracted |  |  |
| paraul secu lacatusi | uncontracted |  |  |
| paraul slanic | uncontracted |  |  |
| paraul smoleanului | uncontracted |  |  |
| paraul stepilor | uncontracted |  |  |
| paraul tescanari | uncontracted |  |  |
| paraul tisa | present | AJVPS MARAMUREȘ |  |
| paraul varteju | uncontracted |  |  |
| paraul vizuinii | uncontracted |  |  |
| paraul zaganului | uncontracted |  |  |
| putna | present | AJVPS VRANCEA |  |
| ramna | uncontracted |  |  |
| ramnicu sarat | present | AJVPS VRANCEA | anpa_map:sweep:ramnicu sarat |
| sarata | present | AJVPS BOTOȘANI |  |
| saratel | uncontracted |  |  |
| slanic | uncontracted |  |  |
| tichiris | uncontracted |  |  |
| tisita mare | present | Direcția Silvică Vrancea | romsilva_map:exact |
| valea sarii | uncontracted |  |  |
| zabala | present | AJVPS VRANCEA | audit_match:prefix |

### Celulă 45.4-45.9N, 27.0-27.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| balan | uncontracted |  |  |
| barlad | present | AJVPS VASLUI |  |
| beciu | uncontracted |  |  |
| cires | uncontracted |  |  |
| cotatcul | uncontracted |  |  |
| danube | uncontracted |  |  |
| leica | uncontracted |  |  |
| milcov | uncontracted |  |  |
| pietroasa | uncontracted |  |  |
| putna | present | AJVPS VRANCEA |  |
| ramna | uncontracted |  |  |
| ramnicu sarat | present | AJVPS VRANCEA | anpa_map:sweep:ramnicu sarat |
| siret | present | Centrul Regional de Ecologie Bacău |  |
| slimnic | uncontracted |  |  |
| susita | present | AJVPS VRANCEA | anpa_map:sweep:susita |
| tecucel | uncontracted |  |  |

### Celulă 45.4-45.9N, 27.5-28.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bujoru | uncontracted |  |  |
| buzau | present | AJVPS Brăila |  |
| caina | uncontracted |  |  |
| chineja | uncontracted |  |  |
| danube | uncontracted |  |  |
| geru | uncontracted |  |  |
| leica | uncontracted |  |  |
| lozova | uncontracted |  |  |
| ramnicu sarat | present | AJVPS VRANCEA | anpa_map:sweep:ramnicu sarat |
| siret | present | Centrul Regional de Ecologie Bacău |  |
| suhu | uncontracted |  |  |
| suhurlui | uncontracted |  |  |
| valea lui odobescu | uncontracted |  |  |

### Celulă 45.4-45.9N, 28.0-28.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| cahul | uncontracted |  |  |
| chineja | uncontracted |  |  |
| danube | uncontracted |  |  |
| dunarea | uncontracted |  |  |
| dunarea дунаи | uncontracted |  |  |
| frumoasa | present | AVPS MIERCUREA-CIUC |  |
| prut | present | AVPS IAȘI |  |
| prut / прут | uncontracted |  |  |
| raul mic | present | AVPS MIERCUREA-CIUC |  |
| salcia mare | uncontracted |  |  |
| siret | present | Centrul Regional de Ecologie Bacău |  |
| tiglina | uncontracted |  |  |
| ursoaia | uncontracted |  |  |
| балка баланешть | uncontracted |  |  |
| балка баланєшть | uncontracted |  |  |
| балка бужорка | uncontracted |  |  |
| балка каптаманулуи | uncontracted |  |  |
| балка поштова | uncontracted |  |  |
| балка хаджи гоичу | uncontracted |  |  |
| рукав лат | uncontracted |  |  |
| рукав інгуст | uncontracted |  |  |

### Celulă 45.4-45.9N, 28.5-29.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| danube | uncontracted |  |  |
| ialpug | uncontracted |  |  |
| lunga | uncontracted |  |  |
| salcia mare | uncontracted |  |  |
| балка бирнова | uncontracted |  |  |
| балка дальбонуто | uncontracted |  |  |
| балка каинак кулак | uncontracted |  |  |
| балка недео | uncontracted |  |  |
| балка сариярлик | uncontracted |  |  |
| болбока | uncontracted |  |  |
| великии катлабуг | uncontracted |  |  |
| дандарська долина | uncontracted |  |  |
| долина маринівка | uncontracted |  |  |
| каираклія | uncontracted |  |  |
| караклія | uncontracted |  |  |
| карасулак | uncontracted |  |  |
| лунга | uncontracted |  |  |
| малии катлабуг | uncontracted |  |  |
| мостова балка | uncontracted |  |  |
| пандакліиська балка | uncontracted |  |  |
| ташбунар | uncontracted |  |  |
| черкеська балка | uncontracted |  |  |
| ялпуг | uncontracted |  |  |

### Celulă 45.4-45.9N, 29.0-29.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bratul babina | uncontracted |  |  |
| bratul cernovca | uncontracted |  |  |
| bratul tataru | uncontracted |  |  |
| danube | uncontracted |  |  |
| аліяга | uncontracted |  |  |
| балка каназір | uncontracted |  |  |
| гирло мурза | uncontracted |  |  |
| гонча балка | uncontracted |  |  |
| гірло лаптіш | uncontracted |  |  |
| долина маринеи | uncontracted |  |  |
| дракуля | uncontracted |  |  |
| дунаєць | uncontracted |  |  |
| каменка | uncontracted |  |  |
| канал лаптиш | uncontracted |  |  |
| киргиж китаи | uncontracted |  |  |
| киргіж | uncontracted |  |  |
| киргіж китаи | uncontracted |  |  |
| кислицькии рукав | uncontracted |  |  |
| кріушія | uncontracted |  |  |
| кіліиське гирло | uncontracted |  |  |
| кіліиське гирло bratul chilia | uncontracted |  |  |
| малии катлабуг | uncontracted |  |  |
| нерушаи | uncontracted |  |  |
| прямии рукав | uncontracted |  |  |
| рукав катенька | uncontracted |  |  |
| рукав машенька | uncontracted |  |  |
| соломонів рукав | uncontracted |  |  |
| ташлик | uncontracted |  |  |
| чамашир | uncontracted |  |  |
| єника | uncontracted |  |  |
| єнікіои | uncontracted |  |  |

### Celulă 45.4-45.9N, 29.5-30.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bratul cernovca | uncontracted |  |  |
| cogalnic | uncontracted |  |  |
| danube | uncontracted |  |  |
| анкудінове гирло | uncontracted |  |  |
| білгородське гирло | uncontracted |  |  |
| гирло мурза | uncontracted |  |  |
| гирло прірва | uncontracted |  |  |
| гнєушеве гирло | uncontracted |  |  |
| гірло лаптіш | uncontracted |  |  |
| дракуля | uncontracted |  |  |
| з єднувальнии канал | uncontracted |  |  |
| кагач | uncontracted |  |  |
| казеикін жолобок | uncontracted |  |  |
| когильник | uncontracted |  |  |
| кіліиське гирло bratul chilia | uncontracted |  |  |
| нерушаи | uncontracted |  |  |
| очаківське гирло | uncontracted |  |  |
| полуденне гирло | uncontracted |  |  |
| потапів канал | uncontracted |  |  |
| прямии рукав | uncontracted |  |  |
| північне гирло | uncontracted |  |  |
| ракове гирло | uncontracted |  |  |
| сарата | uncontracted |  |  |
| соломонів рукав | uncontracted |  |  |
| чернякове гирло | uncontracted |  |  |

### Celulă 45.9-46.4N, 20.0-20.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| aranca | present | AJVPS TIMIȘ | audit_match:exact |
| aranca / златица | uncontracted |  |  |
| danube | uncontracted |  |  |
| k 3 csatorna | uncontracted |  |  |
| maros | uncontracted |  |  |
| mures | present | AJVPS TIMIȘ |  |
| nagyer csatorna | uncontracted |  |  |
| tisza | uncontracted |  |  |
| златица | uncontracted |  |  |
| млака | uncontracted |  |  |
| ђукошин канал | uncontracted |  |  |

### Celulă 45.9-46.4N, 20.5-21.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| apa mare | present | AJVPS TIMIȘ |  |
| aranca | present | AJVPS TIMIȘ | audit_match:exact |
| ciganyka er | uncontracted |  |  |
| danube | uncontracted |  |  |
| kutas eri csatorna | uncontracted |  |  |
| maros | uncontracted |  |  |
| mures | present | AJVPS TIMIȘ |  |
| pamant alb | present | AJVPS TIMIȘ |  |
| valea apei | uncontracted |  |  |
| златица | uncontracted |  |  |
| млака | uncontracted |  |  |

### Celulă 45.9-46.4N, 21.0-21.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| apa mare | present | AJVPS TIMIȘ |  |
| aranca | present | AJVPS TIMIȘ | audit_match:exact |
| ardeleni | uncontracted |  |  |
| bacin | uncontracted |  |  |
| battonyai nagy csatorna | uncontracted |  |  |
| beregsau | uncontracted |  |  |
| caran | present | AJVPS TIMIȘ |  |
| ciganyka er | uncontracted |  |  |
| danube | uncontracted |  |  |
| fibis | uncontracted |  |  |
| hamos | uncontracted |  |  |
| honos | uncontracted |  |  |
| iercicu | uncontracted |  |  |
| luda bara | uncontracted |  |  |
| magherus | present | AJVPS TIMIȘ |  |
| mures | present | AJVPS TIMIȘ |  |
| muresel | uncontracted |  |  |
| muresul mort | uncontracted |  |  |
| pamant alb | present | AJVPS TIMIȘ |  |
| paraul lacului | present | AJVPS TIMIȘ |  |
| sicsa | present | AJVPS TIMIȘ |  |
| slatina | uncontracted |  |  |
| sumanda | uncontracted |  |  |
| valea cruceni | uncontracted |  |  |
| valea dosului | uncontracted |  |  |
| valea zorilor | uncontracted |  |  |
| златица | uncontracted |  |  |

### Celulă 45.9-46.4N, 21.5-22.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bacin | uncontracted |  |  |
| barzava | present | AJVPS TIMIȘ |  |
| beregsau | uncontracted |  |  |
| buzad | uncontracted |  |  |
| cigher | uncontracted |  |  |
| conop | uncontracted |  |  |
| crisul alb | present | AJVPS ARAD |  |
| gherteamos | present | AJVPS TIMIȘ |  |
| hamos | uncontracted |  |  |
| magherus | present | AJVPS TIMIȘ |  |
| milova | uncontracted |  |  |
| milovita | uncontracted |  |  |
| mures | present | AJVPS TIMIȘ |  |
| nadas | present | AJPS Cluj |  |
| paraul cladova | uncontracted |  |  |
| paraul cladovita | uncontracted |  |  |
| paraul mare | present | CS HUNEDOARA |  |
| paraul milova | uncontracted |  |  |
| paraul radna | uncontracted |  |  |
| paraul soimos | uncontracted |  |  |
| sfinsca | uncontracted |  |  |
| sintar | uncontracted |  |  |
| valea chilodia | uncontracted |  |  |

### Celulă 45.9-46.4N, 22.0-22.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| almas | uncontracted |  |  |
| barzava | present | AJVPS TIMIȘ |  |
| bulza | uncontracted |  |  |
| burdijeni | uncontracted |  |  |
| caprioara | uncontracted |  |  |
| crisul alb | present | AJVPS ARAD |  |
| feher koros | uncontracted |  |  |
| grosul | uncontracted |  |  |
| monorostia | uncontracted |  |  |
| mures | present | AJVPS TIMIȘ |  |
| ohaba | uncontracted |  |  |
| paraul glodghilesti | uncontracted |  |  |
| paraul julita | present | Direcția Silvică Arad | romsilva_map:exact |
| pestis | uncontracted |  |  |
| petris | present | Direcția Silvică Arad | romsilva_map:exact |
| plisca | uncontracted |  |  |
| salciva | uncontracted |  |  |
| saratura | uncontracted |  |  |
| sebis | uncontracted |  |  |
| somonita | uncontracted |  |  |
| sulinis | uncontracted |  |  |
| troas | present | Direcția Silvică Arad | romsilva_map:exact |
| valea almasului | present | AJVPS SĂLAJ |  |
| valea chilodia | uncontracted |  |  |
| valea dulcelui | uncontracted |  |  |
| valea monesei | uncontracted |  |  |
| valea satului | uncontracted |  |  |
| valea tacaselelor | uncontracted |  |  |
| vinesti | uncontracted |  |  |

### Celulă 45.9-46.4N, 22.5-23.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| abucea | uncontracted |  |  |
| ariesul mare | present | Direcția Silvică Alba | romsilva_map:group-shares-course |
| ariesul mic | present | Direcția Silvică Alba | romsilva_map:exact |
| bacisoara | uncontracted |  |  |
| barasti | uncontracted |  |  |
| blejoaia | uncontracted |  |  |
| boholt | uncontracted |  |  |
| boz | uncontracted |  |  |
| certej | uncontracted |  |  |
| crisul alb | present | AJVPS ARAD |  |
| dobra | present | FLY FISHING CLUB SIBIU |  |
| dumesti | uncontracted |  |  |
| feher koros | uncontracted |  |  |
| furcsoara | uncontracted |  |  |
| gurasada | uncontracted |  |  |
| halmagel | uncontracted |  |  |
| homorod | present | AJPS Brașov |  |
| lapusnic | uncontracted |  |  |
| mures | present | AJVPS TIMIȘ |  |
| nojag | uncontracted |  |  |
| ohaba | uncontracted |  |  |
| paraul lui sarpe | uncontracted |  |  |
| paraul luncoi | uncontracted |  |  |
| raul halmagel | uncontracted |  |  |
| raul mures | present | AJVPS ALBA |  |
| ribita | uncontracted |  |  |
| sacamas | uncontracted |  |  |
| sarbi | uncontracted |  |  |
| sohodol | present | A.CERBUL CARPATIN | audit_match:char0.88 |
| toplita | present | AV VIDA SURDUCEL DOBREȘTI |  |
| uibaresti | uncontracted |  |  |
| valea catinii | uncontracted |  |  |
| valea dibartului | uncontracted |  |  |
| valea dracoita | uncontracted |  |  |
| valea dragostei | uncontracted |  |  |
| valea farnicioarei | uncontracted |  |  |
| valea gheghesului | uncontracted |  |  |
| valea leucii | uncontracted |  |  |
| valea lunga | uncontracted |  |  |
| valea lupului | uncontracted |  |  |
| valea maraseasca | uncontracted |  |  |
| valea mare | present | Direcția Silvică Alba | romsilva_map:group-shares-course |
| valea tacaselelor | uncontracted |  |  |
| valea titisorului | uncontracted |  |  |
| valea vacii | uncontracted |  |  |
| valea zlatinei | uncontracted |  |  |
| valisoara | present | AJVPS ALBA |  |

### Celulă 45.9-46.4N, 23.0-23.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| abrud | uncontracted |  |  |
| abrudel | uncontracted |  |  |
| abruzel | uncontracted |  |  |
| acmariu | uncontracted |  |  |
| almasel | uncontracted |  |  |
| ampoi | present | AJVPS ALBA |  |
| ampoita | present | Direcția Silvică Alba | romsilva_map:exact |
| ardeu | uncontracted |  |  |
| aries | present | AJVPS CLUJ |  |
| ariesul mare | present | Direcția Silvică Alba | romsilva_map:group-shares-course |
| ariesul mic | present | Direcția Silvică Alba | romsilva_map:exact |
| bacainti | uncontracted |  |  |
| balsa | uncontracted |  |  |
| blandiana | uncontracted |  |  |
| calineasa | uncontracted |  |  |
| cernita | uncontracted |  |  |
| cetea | uncontracted |  |  |
| cheii | uncontracted |  |  |
| cib | uncontracted |  |  |
| cioara | uncontracted |  |  |
| cricau | uncontracted |  |  |
| cugir | present | AJVPS ALBA |  |
| danube | uncontracted |  |  |
| fenes | uncontracted |  |  |
| galda | uncontracted |  |  |
| galdita | uncontracted |  |  |
| geoagiu | present | AJVPS ALBA | audit_match:prefix |
| gura voii | uncontracted |  |  |
| hermaneasa | uncontracted |  |  |
| iezer | present | Direcția Silvică Harghita |  |
| iezeru mic | uncontracted |  |  |
| ighiel | present | Direcția Silvică Alba | romsilva_map:exact |
| ighiu | uncontracted |  |  |
| lunca metesului | uncontracted |  |  |
| mlaca | uncontracted |  |  |
| mures | present | AJVPS TIMIȘ |  |
| nojag | uncontracted |  |  |
| oand | uncontracted |  |  |
| parau | uncontracted |  |  |
| paraul brazi | uncontracted |  |  |
| paraul foiesu | uncontracted |  |  |
| paraul vartopu | uncontracted |  |  |
| pianu | uncontracted |  |  |
| ramet | uncontracted |  |  |
| raul mures | present | AJVPS ALBA |  |
| raul muscanilor | uncontracted |  |  |
| salistea | uncontracted |  |  |
| sartas | uncontracted |  |  |
| sohodol | present | A.CERBUL CARPATIN | audit_match:char0.88 |
| stauini | uncontracted |  |  |
| stremt | uncontracted |  |  |
| techereu | uncontracted |  |  |
| telna | uncontracted |  |  |
| tocan | uncontracted |  |  |
| valea barnii | uncontracted |  |  |
| valea bradestilor | uncontracted |  |  |
| valea caselor | present | AJVPS ALBA |  |
| valea catinii | uncontracted |  |  |
| valea geoagiului | uncontracted |  |  |
| valea goblii | uncontracted |  |  |
| valea ivascanilor | uncontracted |  |  |
| valea larga | uncontracted |  |  |
| valea lui bibart | uncontracted |  |  |
| valea mogosului | uncontracted |  |  |
| valea porcului | uncontracted |  |  |
| valea seaca | uncontracted |  |  |
| valtori | uncontracted |  |  |
| varmaga | uncontracted |  |  |
| vint | uncontracted |  |  |

### Celulă 45.9-46.4N, 23.5-24.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| aiud | uncontracted |  |  |
| ampoi | present | AJVPS ALBA |  |
| aries | present | AJVPS CLUJ |  |
| boz | uncontracted |  |  |
| carpen | uncontracted |  |  |
| cetea | uncontracted |  |  |
| ciugud | uncontracted |  |  |
| ciunga | uncontracted |  |  |
| craiva | uncontracted |  |  |
| cricau | uncontracted |  |  |
| danube | uncontracted |  |  |
| enyed patakja | uncontracted |  |  |
| farau | uncontracted |  |  |
| galda | uncontracted |  |  |
| garbova | uncontracted |  |  |
| gergelyfajai patak | uncontracted |  |  |
| grindu | uncontracted |  |  |
| hapria | uncontracted |  |  |
| herepe | uncontracted |  |  |
| ighiu | uncontracted |  |  |
| inze | uncontracted |  |  |
| iruga | uncontracted |  |  |
| lopadea | uncontracted |  |  |
| miraslau | uncontracted |  |  |
| mures | present | AJVPS TIMIȘ |  |
| neau | uncontracted |  |  |
| ormenis | uncontracted |  |  |
| paraul calnic | uncontracted |  |  |
| paraul caselor | present | AJVPS ALBA |  |
| paraul cel mare | uncontracted |  |  |
| paraul cetea | uncontracted |  |  |
| paraul iovului | uncontracted |  |  |
| paraul seusa | uncontracted |  |  |
| paraul turzii | uncontracted |  |  |
| paraul valea garbovii | uncontracted |  |  |
| raul mures | present | AJVPS ALBA |  |
| raul obrezanului | uncontracted |  |  |
| sangatin | uncontracted |  |  |
| sebes | present | AJVPS ALBA |  |
| secas | present | AJVPS ALBA |  |
| secasul mic | uncontracted |  |  |
| silivas | uncontracted |  |  |
| slatina | uncontracted |  |  |
| spatac | uncontracted |  |  |
| spring | uncontracted |  |  |
| stauini | uncontracted |  |  |
| stremt | uncontracted |  |  |
| tarnava | present | AJVPS ALBA |  |
| tarnava mare | present | AJVPS MUREȘ |  |
| tarnava mica | present | AJVPS MUREȘ | anpa_map:bistrita-basin |
| telna | uncontracted |  |  |
| tibru | uncontracted |  |  |
| unirea | uncontracted |  |  |
| valea aiudului | uncontracted |  |  |
| valea babei | uncontracted |  |  |
| valea bozului | uncontracted |  |  |
| valea castelului | uncontracted |  |  |
| valea panazii | uncontracted |  |  |
| valea ratului | uncontracted |  |  |
| valea seaca | uncontracted |  |  |
| veza | uncontracted |  |  |
| vingard | uncontracted |  |  |

### Celulă 45.9-46.4N, 24.0-24.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| alma | uncontracted |  |  |
| almen | uncontracted |  |  |
| bedeu | uncontracted |  |  |
| biertan | uncontracted |  |  |
| buzd | uncontracted |  |  |
| curciu | uncontracted |  |  |
| danube | uncontracted |  |  |
| farau | uncontracted |  |  |
| graben | uncontracted |  |  |
| hartibaciu | present | AJVPS SIBIU |  |
| ighis | uncontracted |  |  |
| jidvei | uncontracted |  |  |
| mosna | uncontracted |  |  |
| paraul mistea | uncontracted |  |  |
| paraul mosna | uncontracted |  |  |
| paucea | uncontracted |  |  |
| smig | uncontracted |  |  |
| tarnava mare | present | AJVPS MUREȘ |  |
| tarnava mica | present | AJVPS MUREȘ | anpa_map:bistrita-basin |
| tarnava seaca | uncontracted |  |  |
| visa | uncontracted |  |  |

### Celulă 45.9-46.4N, 24.5-25.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| biertan | uncontracted |  |  |
| cincu | uncontracted |  |  |
| danube | uncontracted |  |  |
| domald | uncontracted |  |  |
| eliseni | uncontracted |  |  |
| felmer | uncontracted |  |  |
| hartibaciu | present | AJVPS SIBIU |  |
| laslea | uncontracted |  |  |
| lovnic | uncontracted |  |  |
| malancrav | uncontracted |  |  |
| movile | uncontracted |  |  |
| parau | uncontracted |  |  |
| paraul archita | uncontracted |  |  |
| paraul cainelui | uncontracted |  |  |
| paraul nades | present | AJVPS MUREȘ |  |
| paraul roates | uncontracted |  |  |
| paraul roua | uncontracted |  |  |
| paraul scroafei | uncontracted |  |  |
| paraul valea carbunarilor | uncontracted |  |  |
| raul infundaturii | uncontracted |  |  |
| raul robului | uncontracted |  |  |
| ruja | uncontracted |  |  |
| saes | uncontracted |  |  |
| sapartoc | uncontracted |  |  |
| schaaser bach | uncontracted |  |  |
| soimusul mare | uncontracted |  |  |
| soimusul mic | uncontracted |  |  |
| tarnava mare | present | AJVPS MUREȘ |  |
| tarnava mica | present | AJVPS MUREȘ | anpa_map:bistrita-basin |
| tunelul cainelui | uncontracted |  |  |
| uilac | uncontracted |  |  |
| valea cainelui | uncontracted |  |  |
| valea dracului | uncontracted |  |  |
| valea mare | present | AVPS MIERCUREA-CIUC |  |
| valea saesului | uncontracted |  |  |

### Celulă 45.9-46.4N, 25.0-25.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bethlenfalvi patak | uncontracted |  |  |
| bosnyak patak | uncontracted |  |  |
| bozom | uncontracted |  |  |
| bradesti | uncontracted |  |  |
| budvar | uncontracted |  |  |
| comana | present | Direcția Silvică Brașov | romsilva_map:exact |
| danube | uncontracted |  |  |
| feernic | uncontracted |  |  |
| feheres patak | uncontracted |  |  |
| felmer | uncontracted |  |  |
| femesul | uncontracted |  |  |
| fiser | uncontracted |  |  |
| gada | uncontracted |  |  |
| garan patak | uncontracted |  |  |
| ghipes | uncontracted |  |  |
| homorodul carbunos | uncontracted |  |  |
| homorodul mare | present | AVPS TÂRNAVA MARE |  |
| homorodul mic | uncontracted |  |  |
| kurt erdo patak | uncontracted |  |  |
| lokod patak | uncontracted |  |  |
| lupsa | uncontracted |  |  |
| maierus | present | AJPS Brașov |  |
| malnas | uncontracted |  |  |
| muller | uncontracted |  |  |
| nadas patak | uncontracted |  |  |
| nadas patak sos kut | uncontracted |  |  |
| nadas patak soskut | uncontracted |  |  |
| olt | present | AJVPS OLT |  |
| parau | uncontracted |  |  |
| paraue mare | uncontracted |  |  |
| paraul archita | uncontracted |  |  |
| paraul bailor | uncontracted |  |  |
| paraul bogata | present | Direcția Silvică Brașov | romsilva_map:exact |
| paraul fiser | uncontracted |  |  |
| paraul goagiu | present | AVPS HUBERTUS | audit_match:exact |
| paraul homorod | present | AJPS Brașov |  |
| paraul sarat | uncontracted |  |  |
| paraul scroafei | uncontracted |  |  |
| remetea | uncontracted |  |  |
| rezarka | uncontracted |  |  |
| salon | uncontracted |  |  |
| scroafa | uncontracted |  |  |
| sos patak | uncontracted |  |  |
| suko patak | uncontracted |  |  |
| suko pataka | uncontracted |  |  |
| szent gyorgy patak | uncontracted |  |  |
| tarnava mare | present | AJVPS MUREȘ |  |
| telecsag | uncontracted |  |  |
| vagasi patak | uncontracted |  |  |
| valea arpad | uncontracted |  |  |
| valea cetati | uncontracted |  |  |
| valea lunga | uncontracted |  |  |
| valea mare | present | AVPS MIERCUREA-CIUC |  |
| valea morii | uncontracted |  |  |
| valea tipiei | uncontracted |  |  |
| valea vaidnei | uncontracted |  |  |
| varga patak | uncontracted |  |  |

### Celulă 45.9-46.4N, 25.5-26.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| aita | present | Direcția Silvică Covasna | romsilva_map:exact |
| arcus | uncontracted |  |  |
| bajoz pataka | uncontracted |  |  |
| baraolt | present | AJVPS COVASNA | audit_match:prefix |
| batanii | uncontracted |  |  |
| belinul mare | uncontracted |  |  |
| beta | uncontracted |  |  |
| boloka | uncontracted |  |  |
| borviz patak | uncontracted |  |  |
| bozom | uncontracted |  |  |
| calnic | uncontracted |  |  |
| capolnas | uncontracted |  |  |
| chebes | uncontracted |  |  |
| ched | uncontracted |  |  |
| ciucani | uncontracted |  |  |
| ciuclion | uncontracted |  |  |
| cormos | present | AJVPS COVASNA |  |
| csere patak | uncontracted |  |  |
| danube | uncontracted |  |  |
| fitak pataka | uncontracted |  |  |
| fitod | uncontracted |  |  |
| fotos | uncontracted |  |  |
| hollok patak | uncontracted |  |  |
| homorodul carbunos | uncontracted |  |  |
| homorodul mic | uncontracted |  |  |
| komlos arok | uncontracted |  |  |
| kurta patak | uncontracted |  |  |
| magyaros pataka | uncontracted |  |  |
| maierus | present | AJPS Brașov |  |
| malnas | uncontracted |  |  |
| malnoves | uncontracted |  |  |
| malom arok | uncontracted |  |  |
| meggyes pataka | uncontracted |  |  |
| nadas patak sos kut | uncontracted |  |  |
| nyerges | uncontracted |  |  |
| olt | present | AJPS Brașov |  |
| oroci | uncontracted |  |  |
| orsovaj pataka | uncontracted |  |  |
| p rosu | uncontracted |  |  |
| paraul alb | present | AJVPS CARAȘ-SEVERIN | multiway_chain |
| paraul albastru | uncontracted |  |  |
| paraul altarului | uncontracted |  |  |
| paraul angyos | uncontracted |  |  |
| paraul asau | present | AJVPS BACĂU |  |
| paraul ascuns | uncontracted |  |  |
| paraul bailor | uncontracted |  |  |
| paraul balogsas | uncontracted |  |  |
| paraul balvanyos | uncontracted |  |  |
| paraul banatus | uncontracted |  |  |
| paraul batatura cailor | uncontracted |  |  |
| paraul batca | uncontracted |  |  |
| paraul beta | uncontracted |  |  |
| paraul bisericii | uncontracted |  |  |
| paraul bogat | uncontracted |  |  |
| paraul borviz | uncontracted |  |  |
| paraul capelei | uncontracted |  |  |
| paraul carpinisulului | uncontracted |  |  |
| paraul cet | uncontracted |  |  |
| paraul chirui | uncontracted |  |  |
| paraul cioma | uncontracted |  |  |
| paraul craca mica | uncontracted |  |  |
| paraul csiszar | uncontracted |  |  |
| paraul curt | uncontracted |  |  |
| paraul de jos | present | FLY FISHING CLUB SIBIU |  |
| paraul de sus | present | FLY FISHING CLUB SIBIU |  |
| paraul dealul mare | uncontracted |  |  |
| paraul dekany | uncontracted |  |  |
| paraul delnita | uncontracted |  |  |
| paraul feiso | uncontracted |  |  |
| paraul fenioved | uncontracted |  |  |
| paraul ferestrau | uncontracted |  |  |
| paraul fierarului | uncontracted |  |  |
| paraul ghepiu | uncontracted |  |  |
| paraul gherend | uncontracted |  |  |
| paraul halasag | uncontracted |  |  |
| paraul holosag | uncontracted |  |  |
| paraul iadului | present-hidden | Direcția Silvică Bihor | romsilva_map |
| paraul ikres | uncontracted |  |  |
| paraul jegy | uncontracted |  |  |
| paraul jombor | uncontracted |  |  |
| paraul kolos | uncontracted |  |  |
| paraul lacului | present | AJVPS TIMIȘ |  |
| paraul lugos | uncontracted |  |  |
| paraul lui ionea | uncontracted |  |  |
| paraul mare alb | uncontracted |  |  |
| paraul merilor | uncontracted |  |  |
| paraul mes | uncontracted |  |  |
| paraul mic | present | AVPS MIERCUREA-CIUC |  |
| paraul mic alb | uncontracted |  |  |
| paraul minei | present | AVPS MIERCUREA-CIUC |  |
| paraul minei rosii | uncontracted |  |  |
| paraul mitaci | uncontracted |  |  |
| paraul mitaciul mic | uncontracted |  |  |
| paraul monyasd | uncontracted |  |  |
| paraul nagyos | uncontracted |  |  |
| paraul negru | present | AJVPS COVASNA | audit_match:prefix |
| paraul nemeres | uncontracted |  |  |
| paraul nilves | uncontracted |  |  |
| paraul padureni | present | AJVPS COVASNA | audit_match:exact |
| paraul pauleni | uncontracted |  |  |
| paraul piatra soimilor | uncontracted |  |  |
| paraul pietros | uncontracted |  |  |
| paraul ploii | uncontracted |  |  |
| paraul puturos | uncontracted |  |  |
| paraul puturosu | uncontracted |  |  |
| paraul ravasz | uncontracted |  |  |
| paraul rece | uncontracted |  |  |
| paraul repad | uncontracted |  |  |
| paraul rosu | present | Direcția Silvică Harghita |  |
| paraul saldobos | uncontracted |  |  |
| paraul sandru | uncontracted |  |  |
| paraul sanmartin | uncontracted |  |  |
| paraul saracilor | uncontracted |  |  |
| paraul sarmani | uncontracted |  |  |
| paraul sas | uncontracted |  |  |
| paraul seceni | uncontracted |  |  |
| paraul silos | uncontracted |  |  |
| paraul stairul mare | uncontracted |  |  |
| paraul sugo | present | Direcția Silvică Covasna | romsilva_map:exact |
| paraul sumuleu | uncontracted |  |  |
| paraul surpat | uncontracted |  |  |
| paraul szenegeto | uncontracted |  |  |
| paraul talharului | uncontracted |  |  |
| paraul tiganului | uncontracted |  |  |
| paraul tompad | uncontracted |  |  |
| paraul toplita | present | AV VIDA SURDUCEL DOBREȘTI |  |
| paraul trestiei | uncontracted |  |  |
| paraul tusnad | uncontracted |  |  |
| paraul ulies | uncontracted |  |  |
| paraul uscat | uncontracted |  |  |
| paraul varghis | present | AJVPS COVASNA | audit_match:exact |
| paraul vasond | uncontracted |  |  |
| paraul vermed | uncontracted |  |  |
| paraul vinului | uncontracted |  |  |
| paraul zalan | uncontracted |  |  |
| poiana pietrii | uncontracted |  |  |
| pustnicul | uncontracted |  |  |
| rakottyas patak | uncontracted |  |  |
| raul cernat | uncontracted |  |  |
| raul fisag | present | AVPS GHEORGHIENI | multiway_chain |
| raul turia | uncontracted |  |  |
| rege | uncontracted |  |  |
| remetea | uncontracted |  |  |
| sotetpatak | uncontracted |  |  |
| stiuca | uncontracted |  |  |
| sugasau | uncontracted |  |  |
| szentegyhaz pataka | uncontracted |  |  |
| szentegyhaza patak | uncontracted |  |  |
| techera | uncontracted |  |  |
| telec | uncontracted |  |  |
| telekasza pataka | uncontracted |  |  |
| tiva | uncontracted |  |  |
| to patak | uncontracted |  |  |
| turia | uncontracted |  |  |
| ulo patak | uncontracted |  |  |
| valea crisului | uncontracted |  |  |
| valea lunga | uncontracted |  |  |
| valea morii | uncontracted |  |  |
| valea neagra | present | Direcția Silvică Suceava | romsilva_map:group-shares-course |
| valea ursilor | uncontracted |  |  |
| valea zalanului | uncontracted |  |  |
| varghis | present | AJVPS COVASNA | audit_match:exact |
| zalan patak | uncontracted |  |  |

### Celulă 45.9-46.4N, 26.0-26.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bajoz pataka | uncontracted |  |  |
| banko vogye | uncontracted |  |  |
| barzauta | present | Direcția Silvică Covasna | romsilva_map:group-shares-course |
| basca | present | Direcția Silvică Covasna | romsilva_sector_split |
| bogas patak | uncontracted |  |  |
| bretcu | uncontracted |  |  |
| carpenul | uncontracted |  |  |
| carpenul mare | uncontracted |  |  |
| carpenul mic | uncontracted |  |  |
| casin | present | AJVPS COVASNA | audit_match:exact |
| ciobanus | present | AJVPS BACĂU |  |
| csobanyos patak | uncontracted |  |  |
| danube | uncontracted |  |  |
| dobru | uncontracted |  |  |
| dofteana | present | Direcția Silvică Bacău | romsilva_map:exact |
| doftenita | uncontracted |  |  |
| dumbrava | uncontracted |  |  |
| dеbrеce pataka | uncontracted |  |  |
| eghersec | uncontracted |  |  |
| estelnic | uncontracted |  |  |
| ghelinta | present | AJVPS COVASNA | audit_match:exact |
| gherghitan | uncontracted |  |  |
| gresul | uncontracted |  |  |
| groza | uncontracted |  |  |
| gubas | uncontracted |  |  |
| hados | uncontracted |  |  |
| halal pataka | uncontracted |  |  |
| harapetke pataka | uncontracted |  |  |
| hosszu patak | uncontracted |  |  |
| hotarul | uncontracted |  |  |
| imper | uncontracted |  |  |
| izvorul alb | present | AJVPS CARAȘ-SEVERIN | multiway_chain |
| janos pataka | uncontracted |  |  |
| kecskes patak | uncontracted |  |  |
| kicsi vesz sarok patak | uncontracted |  |  |
| kis bukk patak | uncontracted |  |  |
| kupus pataka | uncontracted |  |  |
| kurta patak | uncontracted |  |  |
| lemnia | uncontracted |  |  |
| margarata | uncontracted |  |  |
| meggyes pataka | uncontracted |  |  |
| meghes | uncontracted |  |  |
| nadaska pataka | uncontracted |  |  |
| nagy vesz sarok | uncontracted |  |  |
| nyerges | uncontracted |  |  |
| oboiul | uncontracted |  |  |
| oituz | present | AJVPS COVASNA |  |
| ojdula | present | AJVPS COVASNA |  |
| paraul alunis | uncontracted |  |  |
| paraul apa lina | uncontracted |  |  |
| paraul basca | present | Direcția Silvică Covasna | romsilva_sector_split |
| paraul capelei | uncontracted |  |  |
| paraul cinod | uncontracted |  |  |
| paraul cristin | uncontracted |  |  |
| paraul diszno sarok | uncontracted |  |  |
| paraul eghersec | uncontracted |  |  |
| paraul iadului | present-hidden | Direcția Silvică Bihor | romsilva_map |
| paraul intortochiat | uncontracted |  |  |
| paraul laposului | uncontracted |  |  |
| paraul mara | present | AJVPS MARAMUREȘ |  |
| paraul muerus | uncontracted |  |  |
| paraul piatra alba | uncontracted |  |  |
| paraul secuiului | uncontracted |  |  |
| paraul toplita | present | AV VIDA SURDUCEL DOBREȘTI |  |
| paraul trestiilor | uncontracted |  |  |
| paraul valos | uncontracted |  |  |
| putna | present | AJVPS VRANCEA |  |
| rac pataka | uncontracted |  |  |
| raul barzauta | present | Direcția Silvică Bacău | romsilva_map:sector-bacau |
| raul cernat | uncontracted |  |  |
| raul chilisca | uncontracted |  |  |
| raul ciobanus | present | AJVPS BACĂU |  |
| raul fisag | present | AVPS GHEORGHIENI | multiway_chain |
| raul negru | present | AJVPS COVASNA | audit_match:prefix |
| raul soveto | uncontracted |  |  |
| raul trotus | present | AJVPS BACĂU |  |
| raul turia | uncontracted |  |  |
| raul uz | uncontracted |  |  |
| repatu | uncontracted |  |  |
| repatu mare | uncontracted |  |  |
| repatu mic | uncontracted |  |  |
| sas pataka | uncontracted |  |  |
| slanic | uncontracted |  |  |
| soveto patak | uncontracted |  |  |
| stogu | uncontracted |  |  |
| szakada j pataka | uncontracted |  |  |
| szaraz patak | uncontracted |  |  |
| telekasza pataka | uncontracted |  |  |
| tiganca | uncontracted |  |  |
| tisa | present | AJVPS MARAMUREȘ |  |
| tobukke patak | uncontracted |  |  |
| trotus | present | AJVPS BACĂU |  |
| turia | uncontracted |  |  |
| ulo patak | uncontracted |  |  |
| uz | uncontracted |  |  |
| valea mare | present | AVPS MIERCUREA-CIUC |  |
| valea stramba | present | AJPS Brașov |  |
| valea uzului | uncontracted |  |  |
| veresvesz pataka | uncontracted |  |  |
| vinul | uncontracted |  |  |

### Celulă 45.9-46.4N, 26.5-27.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| alba | uncontracted |  |  |
| casin | present | AJVPS COVASNA | audit_match:exact |
| chilug | uncontracted |  |  |
| chiua | uncontracted |  |  |
| cremenet | uncontracted |  |  |
| cucuieti | uncontracted |  |  |
| danube | uncontracted |  |  |
| dofteana | present | Direcția Silvică Bacău | romsilva_map:exact |
| doftenita | uncontracted |  |  |
| dragomira | present-hidden | AJVPS BOTOȘANI |  |
| larguta | uncontracted |  |  |
| lepsa | present | Direcția Silvică Vrancea | romsilva_map:exact |
| oituz | present | AJVPS COVASNA |  |
| putna | present | AJVPS VRANCEA |  |
| racaciuni | present | AJVPS BACĂU | bbox_fix:lake:Lacul Răcăciuni |
| raul tazlau | present | AJVPS BACĂU |  |
| raul trotus | present | AJVPS BACĂU |  |
| siret | present | Centrul Regional de Ecologie Bacău |  |
| slanic | uncontracted |  |  |
| susita | present | AJVPS VRANCEA | anpa_map:sweep:susita |
| tazlau | present | AJVPS BACĂU |  |
| tichiris | uncontracted |  |  |
| tisita | present | Direcția Silvică Vrancea | romsilva_map:exact |
| tisita mare | present | Direcția Silvică Vrancea | romsilva_map:exact |
| tisita mica | present | Direcția Silvică Vrancea | romsilva_map:exact |
| trotus | present | AJVPS BACĂU |  |
| uz | uncontracted |  |  |
| vidra | present | Direcția Silvică Vâlcea | bbox_fix:lake:Lacul Vidra |
| vizauti | uncontracted |  |  |

### Celulă 45.9-46.4N, 27.0-27.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| apa neagra | uncontracted |  |  |
| barlad | present | AJVPS VASLUI |  |
| blaneasa | uncontracted |  |  |
| cabesti | uncontracted |  |  |
| carecna | uncontracted |  |  |
| danube | uncontracted |  |  |
| domosita | uncontracted |  |  |
| pereschiv | uncontracted |  |  |
| pereschivul mic | uncontracted |  |  |
| putna | present | AJVPS VRANCEA |  |
| racaciuni | present | AJVPS BACĂU | bbox_fix:lake:Lacul Răcăciuni |
| raul trotus | present | AJVPS BACĂU |  |
| raul zeletin | uncontracted |  |  |
| repedea | present | AJVPS VÂLCEA |  |
| siret | present | Centrul Regional de Ecologie Bacău |  |
| susita | present | AJVPS VRANCEA | anpa_map:sweep:susita |
| trotus | present | AJVPS BACĂU |  |
| zabrauti | uncontracted |  |  |
| zabrautul mic | uncontracted |  |  |
| zeletin | uncontracted |  |  |

### Celulă 45.9-46.4N, 27.5-28.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| barlad | present | AJVPS VASLUI |  |
| barzota | uncontracted |  |  |
| barzotel | uncontracted |  |  |
| blaneasa | uncontracted |  |  |
| canal dejectii sc rulment | uncontracted |  |  |
| hobana | uncontracted |  |  |
| paraul valea seaca | uncontracted |  |  |
| pereschiv | uncontracted |  |  |
| raul barlad | present | AJVPS VASLUI |  |
| siret | present | Centrul Regional de Ecologie Bacău |  |
| tutova | present | AJVPS VASLUI |  |

### Celulă 45.9-46.4N, 28.0-28.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| frumoasa | present | AVPS MIERCUREA-CIUC |  |
| horincea | uncontracted |  |  |
| oancea | uncontracted |  |  |
| paraul borzesti | uncontracted |  |  |
| prut | present | AVPS IAȘI |  |
| prut / прут | uncontracted |  |  |
| salcia mare | uncontracted |  |  |
| sarata | present | AJVPS BOTOȘANI |  |
| tigheci | uncontracted |  |  |
| valea galmaja | uncontracted |  |  |
| valea sasaghiol | uncontracted |  |  |

### Celulă 45.9-46.4N, 28.5-29.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| avdarma | uncontracted |  |  |
| chirghis chitai | uncontracted |  |  |
| cogalnic | uncontracted |  |  |
| ialpug | uncontracted |  |  |
| ialpugel | uncontracted |  |  |
| lunga | uncontracted |  |  |
| lunguta | uncontracted |  |  |
| raul avdarma | uncontracted |  |  |
| raul chirghis chitai | uncontracted |  |  |
| raul ialpugel | uncontracted |  |  |
| valeperja | uncontracted |  |  |
| валепержа | uncontracted |  |  |
| великии катлабуг | uncontracted |  |  |
| киргиж китаи | uncontracted |  |  |
| когильник | uncontracted |  |  |
| малии катлабуг | uncontracted |  |  |
| скіноса | uncontracted |  |  |
| ісерлія | uncontracted |  |  |

### Celulă 45.9-46.4N, 29.0-29.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| ceaga | uncontracted |  |  |
| cogalnic | uncontracted |  |  |
| аліяга | uncontracted |  |  |
| арса | uncontracted |  |  |
| балка делень | uncontracted |  |  |
| бахмутка | uncontracted |  |  |
| валепержа | uncontracted |  |  |
| долина попи | uncontracted |  |  |
| дракуля | uncontracted |  |  |
| киргиж китаи | uncontracted |  |  |
| киргіж | uncontracted |  |  |
| когильник | uncontracted |  |  |
| мутаву | uncontracted |  |  |
| нерушаи | uncontracted |  |  |
| новоселівка | uncontracted |  |  |
| сака | uncontracted |  |  |
| скіноса | uncontracted |  |  |
| ташлик | uncontracted |  |  |
| чага | uncontracted |  |  |
| чибану | uncontracted |  |  |
| чилігідер | uncontracted |  |  |
| ісерлія | uncontracted |  |  |

### Celulă 45.9-46.4N, 29.5-30.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| babei | uncontracted |  |  |
| cogalnic | uncontracted |  |  |
| бабеи | uncontracted |  |  |
| кагач | uncontracted |  |  |
| когельник | uncontracted |  |  |
| когильник | uncontracted |  |  |
| сарата | uncontracted |  |  |
| чилігідер | uncontracted |  |  |

### Celulă 46.4-46.9N, 20.0-20.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| danube | uncontracted |  |  |
| harmas koros | uncontracted |  |  |
| kenyere er | uncontracted |  |  |
| korogy er | uncontracted |  |  |
| kutvolgy kakasszeki csatorna | uncontracted |  |  |
| ludas er | uncontracted |  |  |
| magocs er | uncontracted |  |  |
| tisza | uncontracted |  |  |
| toke er | uncontracted |  |  |
| veker er | uncontracted |  |  |

### Celulă 46.4-46.9N, 20.5-21.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| danube | uncontracted |  |  |
| harmas koros | uncontracted |  |  |
| kutas eri csatorna | uncontracted |  |  |
| magocs er | uncontracted |  |  |

### Celulă 46.4-46.9N, 21.0-21.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bungosdi focsatorna | uncontracted |  |  |
| crisul alb | present | AJVPS ARAD |  |
| crisul alb / feher koros | uncontracted |  |  |
| crisul negru | present | AJVPS ARAD |  |
| danube | uncontracted |  |  |
| feher koros | uncontracted |  |  |
| fekete koros | uncontracted |  |  |
| gyula ketegyhazi felfogo csatorna | uncontracted |  |  |
| ketegyhazi csatorna | uncontracted |  |  |
| kettos koros | uncontracted |  |  |

### Celulă 46.4-46.9N, 21.5-22.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| cicer | uncontracted |  |  |
| cigher | uncontracted |  |  |
| corhana | present | AJVPS BIHOR |  |
| crisul alb | present | AJVPS ARAD |  |
| crisul negru | present | AJVPS ARAD |  |
| csicser | uncontracted |  |  |
| danube | uncontracted |  |  |
| feher koros | uncontracted |  |  |
| fekete koros | uncontracted |  |  |
| koles er | uncontracted |  |  |
| teuz | uncontracted |  |  |
| valea grosilor | uncontracted |  |  |

### Celulă 46.4-46.9N, 22.0-22.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| corbu | uncontracted |  |  |
| craiasa | uncontracted |  |  |
| crisul alb | present | AJVPS ARAD |  |
| crisul baita | present | AJVPS BIHOR |  |
| crisul baitei | uncontracted |  |  |
| crisul negru | present | AJVPS BIHOR |  |
| crisul pietros | present | Direcția Silvică Bihor | romsilva_map:exact |
| danube | uncontracted |  |  |
| feher koros | uncontracted |  |  |
| fekete koros | uncontracted |  |  |
| finis | uncontracted |  |  |
| godinoasa | uncontracted |  |  |
| goila | uncontracted |  |  |
| lazuri | uncontracted |  |  |
| mizies | uncontracted |  |  |
| nimaiesti | uncontracted |  |  |
| paraul barc | uncontracted |  |  |
| paraul boiu | uncontracted |  |  |
| paraul iacoboaia | uncontracted |  |  |
| paraul osoiului | uncontracted |  |  |
| paraul stramtura | uncontracted |  |  |
| paraul strugoriu | uncontracted |  |  |
| paraul vida | present | AJVPS BIHOR |  |
| paraul viduta | uncontracted |  |  |
| rosia | present | AJVPS BIHOR |  |
| sanmartin de beius | uncontracted |  |  |
| sighistel | uncontracted |  |  |
| sohodol | present | A.CERBUL CARPATIN | audit_match:char0.88 |
| soimus | uncontracted |  |  |
| toplicioara | uncontracted |  |  |
| valea grosilor | uncontracted |  |  |
| valea haigasului | uncontracted |  |  |
| valea meziad | uncontracted |  |  |
| valea monesei | uncontracted |  |  |
| valea nimaiestilor | uncontracted |  |  |
| valea pacaului | uncontracted |  |  |
| valea rosia | present | AJVPS BIHOR |  |
| valea seaca | uncontracted |  |  |
| valea topa | uncontracted |  |  |
| valea vida | present | AJVPS BIHOR |  |

### Celulă 46.4-46.9N, 22.5-23.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| aleu | uncontracted |  |  |
| aluni | uncontracted |  |  |
| alunis | uncontracted |  |  |
| alunisu | uncontracted |  |  |
| alunu mare | uncontracted |  |  |
| alunu mic | uncontracted |  |  |
| apa calda | present | AJVPS CONSTANȚA | audit_match:override |
| apa rapii | uncontracted |  |  |
| aria vulturilor | uncontracted |  |  |
| ariesul mare | present | Direcția Silvică Alba | romsilva_map:group-shares-course |
| ariesul mic | present | Direcția Silvică Alba | romsilva_map:exact |
| batrana | uncontracted |  |  |
| boga | uncontracted |  |  |
| bohodei | uncontracted |  |  |
| bulbuci | uncontracted |  |  |
| bulz | uncontracted |  |  |
| calineasa | uncontracted |  |  |
| captalan | uncontracted |  |  |
| carligate | uncontracted |  |  |
| carligoi | uncontracted |  |  |
| cioroes | uncontracted |  |  |
| cobles | uncontracted |  |  |
| corbu | uncontracted |  |  |
| craiasa | uncontracted |  |  |
| crisul baitei | uncontracted |  |  |
| crisul negru | present | AJVPS BIHOR |  |
| crisul pietros | present | Direcția Silvică Bihor | romsilva_map:exact |
| crisul repede | present | AJVPS BIHOR |  |
| culdesti | uncontracted |  |  |
| danube | uncontracted |  |  |
| daria | uncontracted |  |  |
| demberke | uncontracted |  |  |
| dizdit | uncontracted |  |  |
| dobrus | uncontracted |  |  |
| dragan | present | Direcția Silvică Bihor | romsilva_map:exact |
| dragateanu | uncontracted |  |  |
| fantana rece | uncontracted |  |  |
| fantanele | uncontracted |  |  |
| fekete koros | uncontracted |  |  |
| firza | uncontracted |  |  |
| galbena | uncontracted |  |  |
| garda seaca | uncontracted |  |  |
| gardisoara | uncontracted |  |  |
| garjoaba | uncontracted |  |  |
| ghiobu | uncontracted |  |  |
| gingineasa | uncontracted |  |  |
| giurcuta | uncontracted |  |  |
| guga | uncontracted |  |  |
| hodrancusa mica | uncontracted |  |  |
| hodrangusa | uncontracted |  |  |
| hotaran | uncontracted |  |  |
| iada | uncontracted |  |  |
| iadolina | uncontracted |  |  |
| iedutul | uncontracted |  |  |
| izbucul mic | uncontracted |  |  |
| lesu | present | Direcția Silvică Bihor | romsilva_map:exact |
| luncsoara | uncontracted |  |  |
| magura rosianului | uncontracted |  |  |
| margauta | uncontracted |  |  |
| micusa ghiortoi | uncontracted |  |  |
| mieraganul | uncontracted |  |  |
| miteagul | uncontracted |  |  |
| muncelas | uncontracted |  |  |
| muncelu | uncontracted |  |  |
| niesu | uncontracted |  |  |
| nimaiasa | uncontracted |  |  |
| nimaiesti | uncontracted |  |  |
| onceasa | uncontracted |  |  |
| ordancusa | uncontracted |  |  |
| oselu | uncontracted |  |  |
| parau cristioru | uncontracted |  |  |
| parau iclejii | uncontracted |  |  |
| paraul belis | uncontracted |  |  |
| paraul bortigului | uncontracted |  |  |
| paraul bratcuta | uncontracted |  |  |
| paraul carambului | uncontracted |  |  |
| paraul cerbului | uncontracted |  |  |
| paraul corbului | present | AVPS MIERCUREA-CIUC |  |
| paraul de margine | uncontracted |  |  |
| paraul feredeului | uncontracted |  |  |
| paraul firei | uncontracted |  |  |
| paraul glavoaie | uncontracted |  |  |
| paraul mic | present | Direcția Silvică Alba | romsilva_map:exact |
| paraul misid | uncontracted |  |  |
| paraul morii | uncontracted |  |  |
| paraul mutuleanca | uncontracted |  |  |
| paraul pietroasa | uncontracted |  |  |
| paraul plaiului | uncontracted |  |  |
| paraul podului | uncontracted |  |  |
| paraul prislopului | uncontracted |  |  |
| paraul radeasa | uncontracted |  |  |
| paraul rosu | present | Direcția Silvică Harghita |  |
| paraul seniului | uncontracted |  |  |
| pauleasa | uncontracted |  |  |
| pietroasa | uncontracted |  |  |
| pojaru | uncontracted |  |  |
| polita | uncontracted |  |  |
| ponor | uncontracted |  |  |
| ponorasu | uncontracted |  |  |
| racad | uncontracted |  |  |
| raul budeasa | uncontracted |  |  |
| raul calata | uncontracted |  |  |
| runcu | present | AJVPS MARAMUREȘ |  |
| sacuieu | uncontracted |  |  |
| salatruc | uncontracted |  |  |
| saracelu | uncontracted |  |  |
| scroafa | uncontracted |  |  |
| sebesel | uncontracted |  |  |
| sebisel | uncontracted |  |  |
| servinoasa | uncontracted |  |  |
| sighistel | uncontracted |  |  |
| sohodol | present | A.CERBUL CARPATIN | audit_match:char0.88 |
| soimus | uncontracted |  |  |
| somesul cald | present | D.S. Cluj | bbox_fix:lake:Lacul de acumulare Someșul Cald |
| spurcatu | uncontracted |  |  |
| stana de izvor | uncontracted |  |  |
| storhasu | uncontracted |  |  |
| ticlau | uncontracted |  |  |
| valea agastau | uncontracted |  |  |
| valea arsa | uncontracted |  |  |
| valea bisericii | uncontracted |  |  |
| valea boceasa | uncontracted |  |  |
| valea boii | uncontracted |  |  |
| valea boiului | uncontracted |  |  |
| valea bolandu | uncontracted |  |  |
| valea botii | uncontracted |  |  |
| valea britei | uncontracted |  |  |
| valea brusturi | uncontracted |  |  |
| valea bucura | present | Direcția Silvică Hunedoara |  |
| valea caprioara | uncontracted |  |  |
| valea cerbului | uncontracted |  |  |
| valea cetatii | uncontracted |  |  |
| valea ciripa | uncontracted |  |  |
| valea ciunganu | uncontracted |  |  |
| valea corlatului | uncontracted |  |  |
| valea craciunului | uncontracted |  |  |
| valea crisanului | uncontracted |  |  |
| valea cu cale | uncontracted |  |  |
| valea custurii | uncontracted |  |  |
| valea dibartului | uncontracted |  |  |
| valea fagetilor | uncontracted |  |  |
| valea fagului | uncontracted |  |  |
| valea firei | uncontracted |  |  |
| valea flescuta | uncontracted |  |  |
| valea galbenele | uncontracted |  |  |
| valea gheghesului | uncontracted |  |  |
| valea gojii | uncontracted |  |  |
| valea grupoiu | uncontracted |  |  |
| valea hoanca motului | uncontracted |  |  |
| valea izvorului | uncontracted |  |  |
| valea jighil | uncontracted |  |  |
| valea la stana | uncontracted |  |  |
| valea lui andras | uncontracted |  |  |
| valea lui ilie | uncontracted |  |  |
| valea luncilor | uncontracted |  |  |
| valea lungsorului | uncontracted |  |  |
| valea lupului | uncontracted |  |  |
| valea maguricii | uncontracted |  |  |
| valea mare | present | Direcția Silvică Alba | romsilva_map:group-shares-course |
| valea meziad | uncontracted |  |  |
| valea moara dracului | uncontracted |  |  |
| valea nucsoara | uncontracted |  |  |
| valea paltinisului | uncontracted |  |  |
| valea pastravariei | uncontracted |  |  |
| valea pietrele rosii | uncontracted |  |  |
| valea plaiului | uncontracted |  |  |
| valea podului | uncontracted |  |  |
| valea poienii | uncontracted |  |  |
| valea ponorului | uncontracted |  |  |
| valea rea | uncontracted |  |  |
| valea seaca | uncontracted |  |  |
| valea serpilor | uncontracted |  |  |
| valea sibisoara | uncontracted |  |  |
| valea stanciului | uncontracted |  |  |
| valea stearpa | uncontracted |  |  |
| valea sutanu | uncontracted |  |  |
| valea talharului | uncontracted |  |  |
| valea tiganului | uncontracted |  |  |
| valea titisorului | uncontracted |  |  |
| valea ursului | uncontracted |  |  |
| valea vaiosu | uncontracted |  |  |
| valea varfurasu | uncontracted |  |  |
| valea visagului | uncontracted |  |  |
| varciorog | uncontracted |  |  |
| visag | uncontracted |  |  |
| vulturu | uncontracted |  |  |
| zanda | uncontracted |  |  |
| zanoaga | present | Direcția Silvică Hunedoara | bbox_fix:lake:Lacul Zănoaga Mare |
| zarna | uncontracted |  |  |

### Celulă 46.4-46.9N, 23.0-23.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| agarbiciu | uncontracted |  |  |
| aries | present | AJVPS CLUJ |  |
| bence patak | uncontracted |  |  |
| budulau | uncontracted |  |  |
| chistelec | uncontracted |  |  |
| cioroes | uncontracted |  |  |
| crisul repede | present | AJVPS BIHOR |  |
| danube | uncontracted |  |  |
| demberke | uncontracted |  |  |
| dobrus | uncontracted |  |  |
| dumbrava | uncontracted |  |  |
| dumitreasa | uncontracted |  |  |
| fenes | uncontracted |  |  |
| hasdate | uncontracted |  |  |
| highiesee | uncontracted |  |  |
| hosuveghi | uncontracted |  |  |
| huza | uncontracted |  |  |
| iara | uncontracted |  |  |
| ierta | uncontracted |  |  |
| inuc | uncontracted |  |  |
| irisoara | uncontracted |  |  |
| jebuc | uncontracted |  |  |
| leghia | uncontracted |  |  |
| lesu | present | Direcția Silvică Bihor | romsilva_map:exact |
| macau | uncontracted |  |  |
| marton | uncontracted |  |  |
| mera | uncontracted |  |  |
| nadas | present | AJPS Cluj |  |
| ocolis | present | AJVPS ALBA |  |
| ocolisel | uncontracted |  |  |
| parau tisa | present | AJVPS MARAMUREȘ |  |
| paraul belis | uncontracted |  |  |
| paraul bongar | uncontracted |  |  |
| paraul chinteni | uncontracted |  |  |
| paraul domos | uncontracted |  |  |
| paraul fenesu | uncontracted |  |  |
| paraul hosnos | uncontracted |  |  |
| paraul mastii | uncontracted |  |  |
| paraul negru | present | AJVPS COVASNA | audit_match:prefix |
| paraul notelec | uncontracted |  |  |
| paraul pastravului | uncontracted |  |  |
| paraul tare | uncontracted |  |  |
| piriu filea | uncontracted |  |  |
| pociovalistea | uncontracted |  |  |
| popesti | uncontracted |  |  |
| posaga | present | AJVPS ALBA |  |
| racatau | uncontracted |  |  |
| racos | uncontracted |  |  |
| rantestiolor | uncontracted |  |  |
| rasca | uncontracted |  |  |
| rasca mare | uncontracted |  |  |
| raul calata | uncontracted |  |  |
| raul capus | present | AJPS Cluj |  |
| raul nadas | present | AJPS Cluj |  |
| saliste | present | FLY FISHING CLUB SIBIU |  |
| sardu | uncontracted |  |  |
| soimu | present | D.S. Cluj | bbox_fix:lake:Lacul Șoimu |
| somesu rece | present | D.S. Cluj |  |
| somesul cald | present | D.S. Cluj | bbox_fix:lake:Lacul de acumulare Someșul Cald |
| somesul mic | present | AJVPS CLUJ |  |
| somesul rece | present | D.S. Cluj |  |
| somtelec | uncontracted |  |  |
| stolna | uncontracted |  |  |
| suceag | uncontracted |  |  |
| valea almasului | present | AJVPS SĂLAJ |  |
| valea bradeana | uncontracted |  |  |
| valea ciorgaului | uncontracted |  |  |
| valea costesii | uncontracted |  |  |
| valea fanatii | uncontracted |  |  |
| valea fetii | uncontracted |  |  |
| valea hagaului | uncontracted |  |  |
| valea mare | present | Direcția Silvică Alba | romsilva_map:group-shares-course |
| valea morii | uncontracted |  |  |
| valea nedeii | uncontracted |  |  |
| valea noghieiului | uncontracted |  |  |
| valea plescutei | uncontracted |  |  |
| valea saratii | uncontracted |  |  |
| valea valcaului | uncontracted |  |  |
| valea zapodii | uncontracted |  |  |
| valea zborului | uncontracted |  |  |
| valisoara | present | AJVPS ALBA |  |

### Celulă 46.4-46.9N, 23.5-24.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| agris | uncontracted |  |  |
| aiud | uncontracted |  |  |
| alszegi patak | uncontracted |  |  |
| arany patak | uncontracted |  |  |
| aries | present | AJVPS CLUJ |  |
| barai | uncontracted |  |  |
| becas | uncontracted |  |  |
| berteleag | uncontracted |  |  |
| boju | uncontracted |  |  |
| borsa | uncontracted |  |  |
| borzac | uncontracted |  |  |
| calvaria | uncontracted |  |  |
| chiris | uncontracted |  |  |
| ciepega | uncontracted |  |  |
| ciugud | uncontracted |  |  |
| ciurila | uncontracted |  |  |
| cojocna | uncontracted |  |  |
| danube | uncontracted |  |  |
| enyed patakja | uncontracted |  |  |
| faneata vacilor | uncontracted |  |  |
| fantanita | uncontracted |  |  |
| farau | uncontracted |  |  |
| faureni | uncontracted |  |  |
| feiurdeni | uncontracted |  |  |
| felso patak | uncontracted |  |  |
| gadalin | uncontracted |  |  |
| garbau | uncontracted |  |  |
| gesztenyes patak | uncontracted |  |  |
| giula | uncontracted |  |  |
| grindu | uncontracted |  |  |
| groapa feldioara | uncontracted |  |  |
| gyorgy patak | uncontracted |  |  |
| hasdate | uncontracted |  |  |
| hosuveghi | uncontracted |  |  |
| iara | uncontracted |  |  |
| imbuz | uncontracted |  |  |
| izvoarele | uncontracted |  |  |
| kis patak | uncontracted |  |  |
| korengetegi patak | uncontracted |  |  |
| kovar patak | uncontracted |  |  |
| mahaceni | uncontracted |  |  |
| maraloiu | uncontracted |  |  |
| micus | uncontracted |  |  |
| muratori | uncontracted |  |  |
| mures | present | AJVPS ALBA |  |
| nadas | present | AJPS Cluj |  |
| negoteasa | uncontracted |  |  |
| noroios | uncontracted |  |  |
| ocolisel | uncontracted |  |  |
| odaii beteag | uncontracted |  |  |
| ormenis | uncontracted |  |  |
| paraul becas | uncontracted |  |  |
| paraul bongar | uncontracted |  |  |
| paraul bosor | uncontracted |  |  |
| paraul cesalor | uncontracted |  |  |
| paraul chinteni | uncontracted |  |  |
| paraul garbau | uncontracted |  |  |
| paraul grindeni | uncontracted |  |  |
| paraul muratori | uncontracted |  |  |
| paraul plesca | uncontracted |  |  |
| paraul popii | uncontracted |  |  |
| paraul popiiparaul popii | uncontracted |  |  |
| paraul rimetea | uncontracted |  |  |
| paraul satului | uncontracted |  |  |
| paraul tiganilor | uncontracted |  |  |
| paraul valeni | uncontracted |  |  |
| paraul varaticelor | uncontracted |  |  |
| paraul zapodie | uncontracted |  |  |
| pe vale | uncontracted |  |  |
| piriu filea | uncontracted |  |  |
| popesti | uncontracted |  |  |
| prodae | uncontracted |  |  |
| prunis | uncontracted |  |  |
| puskas patak | uncontracted |  |  |
| racos | uncontracted |  |  |
| raul nadas | present | AJPS Cluj |  |
| salicea | uncontracted |  |  |
| saliste | present | FLY FISHING CLUB SIBIU |  |
| sicu | uncontracted |  |  |
| silas | uncontracted |  |  |
| somesul mic | present | AJVPS CLUJ |  |
| somesul mort | uncontracted |  |  |
| stejeris | uncontracted |  |  |
| suat | uncontracted |  |  |
| tocbesti | uncontracted |  |  |
| tritul | uncontracted |  |  |
| unirea | uncontracted |  |  |
| vaida camaras | uncontracted |  |  |
| valea agrisului | uncontracted |  |  |
| valea aiudului | uncontracted |  |  |
| valea calda | uncontracted |  |  |
| valea calda mare | uncontracted |  |  |
| valea caprioarei | uncontracted |  |  |
| valea comorii | uncontracted |  |  |
| valea fanetii | uncontracted |  |  |
| valea larga | uncontracted |  |  |
| valea merilor | uncontracted |  |  |
| valea morii | uncontracted |  |  |
| valea popesti | uncontracted |  |  |
| valea pordei | uncontracted |  |  |
| valea racilor | uncontracted |  |  |
| valea sandulesti | uncontracted |  |  |
| valea seaca | uncontracted |  |  |
| valea seusei | uncontracted |  |  |
| valea teleacului | uncontracted |  |  |
| valeni | uncontracted |  |  |
| varpatak | uncontracted |  |  |
| verok patakja | uncontracted |  |  |
| visea | uncontracted |  |  |
| zab patak | uncontracted |  |  |
| zapodie | uncontracted |  |  |

### Celulă 46.4-46.9N, 24.0-24.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| apatiu | uncontracted |  |  |
| archiud | uncontracted |  |  |
| atantis | uncontracted |  |  |
| brateni | uncontracted |  |  |
| catina | uncontracted |  |  |
| chiris | uncontracted |  |  |
| ciortus | uncontracted |  |  |
| cuiesd | uncontracted |  |  |
| danube | uncontracted |  |  |
| dipsa | uncontracted |  |  |
| ercea | uncontracted |  |  |
| fantanita | uncontracted |  |  |
| fata comorii | uncontracted |  |  |
| ghemes | uncontracted |  |  |
| imbuz | uncontracted |  |  |
| lechinta | present | AJVPS BISTRIȚA-NĂSĂUD |  |
| matca | uncontracted |  |  |
| mociu | uncontracted |  |  |
| mures | present | AJVPS ALBA |  |
| niraj | present | AJVPS MUREȘ |  |
| paraul cocos | uncontracted |  |  |
| paraul de campie | present | AJVPS MUREȘ |  |
| paraul grindeni | uncontracted |  |  |
| ratul morii | uncontracted |  |  |
| raul fizes | present | AJPS Cluj |  |
| samboleni | uncontracted |  |  |
| sar | present | AJVPS MUREȘ | audit_match:exact |
| sarchii | uncontracted |  |  |
| sincai | uncontracted |  |  |
| suat | uncontracted |  |  |
| tritul | uncontracted |  |  |
| ulies | uncontracted |  |  |
| valea botei mari | uncontracted |  |  |
| valea cucerdea | uncontracted |  |  |
| valea morii | uncontracted |  |  |
| voiniceni | uncontracted |  |  |

### Celulă 46.4-46.9N, 24.5-25.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| agris | uncontracted |  |  |
| baia | uncontracted |  |  |
| baita | uncontracted |  |  |
| beica | present | AJVPS MUREȘ |  |
| canalul gurghiu | uncontracted |  |  |
| canalul morii | uncontracted |  |  |
| casva | uncontracted |  |  |
| cotus | uncontracted |  |  |
| cusmed | present | AJVPS MUREȘ |  |
| danube | uncontracted |  |  |
| deleni | uncontracted |  |  |
| dipsa | uncontracted |  |  |
| ercea | uncontracted |  |  |
| flet | uncontracted |  |  |
| gheghes | uncontracted |  |  |
| gurghiu | uncontracted |  |  |
| iara | uncontracted |  |  |
| idicel | present | AJVPS MUREȘ |  |
| isticeu | present | Direcția Silvică Mureș | romsilva_map:exact |
| lut | present | AJVPS MUREȘ | audit_match:exact |
| mures | present | AJVPS MUREȘ |  |
| nadasa | uncontracted |  |  |
| neaua | uncontracted |  |  |
| niaros | uncontracted |  |  |
| niraj | present | AJVPS MUREȘ |  |
| nirajul mic | present | AJVPS MUREȘ |  |
| orsova | present | AJVPS MUREȘ |  |
| paraul besa | uncontracted |  |  |
| paraul budiu | uncontracted |  |  |
| paraul cocos | uncontracted |  |  |
| paraul iodul | uncontracted |  |  |
| paraul lut | present | AJVPS MUREȘ | audit_match:exact |
| paraul nades | present | AJVPS MUREȘ |  |
| paraul poclos | uncontracted |  |  |
| paraul roka | uncontracted |  |  |
| paraul roua | uncontracted |  |  |
| paraul saivari | uncontracted |  |  |
| paraul trandafirilor | uncontracted |  |  |
| paraul vatman | uncontracted |  |  |
| patul cald | uncontracted |  |  |
| pauloaia | uncontracted |  |  |
| petrilaca | uncontracted |  |  |
| poclos | uncontracted |  |  |
| rapa | uncontracted |  |  |
| rastoaca | uncontracted |  |  |
| sacal | uncontracted |  |  |
| sar | present | AJVPS MUREȘ | audit_match:exact |
| tarnava mica | present | AJVPS MUREȘ | anpa_map:bistrita-basin |
| terebici | uncontracted |  |  |
| tireu | uncontracted |  |  |
| uila | uncontracted |  |  |
| urisiu | uncontracted |  |  |
| vaja pataka | uncontracted |  |  |
| valea pustie | uncontracted |  |  |
| valeni | uncontracted |  |  |
| voiniceni | uncontracted |  |  |

### Celulă 46.4-46.9N, 25.0-25.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| apele nordului | uncontracted |  |  |
| asaul lung | uncontracted |  |  |
| asaul rece | uncontracted |  |  |
| bacta | uncontracted |  |  |
| belchin | uncontracted |  |  |
| belcina | uncontracted |  |  |
| borzont | uncontracted |  |  |
| borzontul mic | uncontracted |  |  |
| bradesti | uncontracted |  |  |
| corund | uncontracted |  |  |
| csorgo patak | uncontracted |  |  |
| cusmed | present | AJVPS MUREȘ |  |
| eszak vize | uncontracted |  |  |
| eszenyo pataka | uncontracted |  |  |
| fagul inalt | uncontracted |  |  |
| fancel | present | Direcția Silvică Mureș | romsilva_map:exact |
| feernic | uncontracted |  |  |
| femesul | uncontracted |  |  |
| filipea | uncontracted |  |  |
| gada | uncontracted |  |  |
| gurghiu | uncontracted |  |  |
| hideg patak | uncontracted |  |  |
| homorodul mare | present | AVPS TÂRNAVA MARE |  |
| isticeu | present | Direcția Silvică Mureș | romsilva_map:exact |
| isuica | uncontracted |  |  |
| iuhod | present | AJVPS MUREȘ |  |
| iuhodul cald | uncontracted |  |  |
| izvoare | uncontracted |  |  |
| kebeled | uncontracted |  |  |
| kecskepatak | uncontracted |  |  |
| lapusna | uncontracted |  |  |
| lucaci | uncontracted |  |  |
| lukacsvesze pataka | uncontracted |  |  |
| magherus | present | AVPS TOPLIȚA |  |
| malomarok | uncontracted |  |  |
| martonca | uncontracted |  |  |
| mures | present | AJVPS MUREȘ |  |
| niraj | present | AJVPS MUREȘ |  |
| nirajul mic | present | AJVPS MUREȘ |  |
| paraul bahancea | uncontracted |  |  |
| paraul benedek | uncontracted |  |  |
| paraul cerbului | uncontracted |  |  |
| paraul corbu | uncontracted |  |  |
| paraul cujbei | uncontracted |  |  |
| paraul daniel | uncontracted |  |  |
| paraul delut | uncontracted |  |  |
| paraul ditrau | uncontracted |  |  |
| paraul dreapta sestinii | uncontracted |  |  |
| paraul drept | uncontracted |  |  |
| paraul drumul lui gavrila | uncontracted |  |  |
| paraul filio | uncontracted |  |  |
| paraul ghidut | uncontracted |  |  |
| paraul goagiu | present | AVPS HUBERTUS | audit_match:exact |
| paraul gropsoara | uncontracted |  |  |
| paraul halianu | uncontracted |  |  |
| paraul hidegag | uncontracted |  |  |
| paraul hidegagul mare | uncontracted |  |  |
| paraul hidegagul mic | uncontracted |  |  |
| paraul homorod | present | AJPS Brașov |  |
| paraul hotaru | uncontracted |  |  |
| paraul iancu | uncontracted |  |  |
| paraul iodul | uncontracted |  |  |
| paraul izarel | uncontracted |  |  |
| paraul lazarea | uncontracted |  |  |
| paraul lui marcel | uncontracted |  |  |
| paraul magura intunecoasa | uncontracted |  |  |
| paraul magurii | uncontracted |  |  |
| paraul marsinetul de jos | present | FLY FISHING CLUB SIBIU |  |
| paraul martonca | uncontracted |  |  |
| paraul mortonea | uncontracted |  |  |
| paraul oberet | uncontracted |  |  |
| paraul pavel | uncontracted |  |  |
| paraul pietrei | uncontracted |  |  |
| paraul salard | present | Direcția Silvică Mureș | romsilva_map:exact |
| paraul sarmasului | uncontracted |  |  |
| paraul sestina | uncontracted |  |  |
| paraul solea | uncontracted |  |  |
| paraul stanga sestinii | uncontracted |  |  |
| paraul strunga | uncontracted |  |  |
| paraul strungii | uncontracted |  |  |
| paraul tiba mare | uncontracted |  |  |
| paraul tiba mica | uncontracted |  |  |
| paraul todoran | uncontracted |  |  |
| paraul trecerea | uncontracted |  |  |
| paraul varful mare | uncontracted |  |  |
| paraul varful mic | uncontracted |  |  |
| paraul wagner | uncontracted |  |  |
| pastravului | uncontracted |  |  |
| pietrosu | uncontracted |  |  |
| pr buneasa | uncontracted |  |  |
| pr casoaielor | uncontracted |  |  |
| pr gudea mare | uncontracted |  |  |
| pr gudea mica | uncontracted |  |  |
| pr hreneasa | uncontracted |  |  |
| pr lui lucian | uncontracted |  |  |
| pr lui mihai | uncontracted |  |  |
| pr lui toader | uncontracted |  |  |
| pr magura de sus | uncontracted |  |  |
| pr piatra de jos | uncontracted |  |  |
| pr piatra de sus | uncontracted |  |  |
| praid | uncontracted |  |  |
| rachotias | uncontracted |  |  |
| raul senced | uncontracted |  |  |
| sacadat | uncontracted |  |  |
| sarat | uncontracted |  |  |
| sarmas | uncontracted |  |  |
| sebes | present | AJVPS MUREȘ | anpa_map:sweep:sebes |
| secuieu | uncontracted |  |  |
| senced | uncontracted |  |  |
| sicasau | present | AVPS TÂRNAVA MARE |  |
| silas | uncontracted |  |  |
| sineu | uncontracted |  |  |
| sovata | uncontracted |  |  |
| sugau | uncontracted |  |  |
| sugo | present | Direcția Silvică Covasna | romsilva_map:exact |
| tarnava mare | present | AJVPS MUREȘ |  |
| tarnava mica | present | AJVPS MUREȘ | anpa_map:bistrita-basin |
| tifanpataka | uncontracted |  |  |
| tireu | uncontracted |  |  |
| tisieu | uncontracted |  |  |
| tolvajos | uncontracted |  |  |
| varsag | present | AVPS TÂRNAVA MARE |  |
| veszespatak | uncontracted |  |  |

### Celulă 46.4-46.9N, 25.5-26.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| albert | uncontracted |  |  |
| andre | uncontracted |  |  |
| antal | uncontracted |  |  |
| apries | uncontracted |  |  |
| arsita | uncontracted |  |  |
| asau | present | AJVPS BACĂU |  |
| balaj | uncontracted |  |  |
| barabas | uncontracted |  |  |
| barakasza | uncontracted |  |  |
| bardos | uncontracted |  |  |
| bartos | uncontracted |  |  |
| becheni | uncontracted |  |  |
| belchin | uncontracted |  |  |
| belcina | uncontracted |  |  |
| berecz | uncontracted |  |  |
| bernat patak | uncontracted |  |  |
| bicajel | present | AJVPS NEAMȚ |  |
| bicaz | present | AJVPS NEAMȚ | bbox_fix:lake:Lacul Izvorul Muntelui |
| bistra | present | AJVPS MUREȘ |  |
| boros | uncontracted |  |  |
| borvizul | uncontracted |  |  |
| bradesti | uncontracted |  |  |
| busciuhan | uncontracted |  |  |
| calul | uncontracted |  |  |
| capra | present | Direcția Silvică Argeș | romsilva_map:exact |
| carbunele negru | uncontracted |  |  |
| cealca | uncontracted |  |  |
| cetatea mica | uncontracted |  |  |
| chisita | uncontracted |  |  |
| chiubaniul | uncontracted |  |  |
| cianod | uncontracted |  |  |
| ciobanus | present | AJVPS BACĂU |  |
| covasan | uncontracted |  |  |
| cseke hago patak | uncontracted |  |  |
| cupas | uncontracted |  |  |
| damuc | uncontracted |  |  |
| danesti | uncontracted |  |  |
| dian pataka | uncontracted |  |  |
| ekere pataka | uncontracted |  |  |
| fabrica | uncontracted |  |  |
| fagetul oltului | uncontracted |  |  |
| fagul cetatii | uncontracted |  |  |
| fagul inalt | uncontracted |  |  |
| fagul mures | uncontracted |  |  |
| fanana lata | uncontracted |  |  |
| fanana rece | uncontracted |  |  |
| fantana lui gal | uncontracted |  |  |
| felso visszafolyo patak | uncontracted |  |  |
| fierul | uncontracted |  |  |
| fighesul | uncontracted |  |  |
| floarea | uncontracted |  |  |
| frumoasa | present | AVPS MIERCUREA-CIUC |  |
| gacinoiul | uncontracted |  |  |
| gheorghe matei | uncontracted |  |  |
| gherpatocul mare | uncontracted |  |  |
| gherpatocul mic | uncontracted |  |  |
| glodul | uncontracted |  |  |
| goce patak | uncontracted |  |  |
| groapa | uncontracted |  |  |
| hidegkut arka | uncontracted |  |  |
| homorodul carbunos | uncontracted |  |  |
| homorodul mare | present | AVPS TÂRNAVA MARE |  |
| hotarul | uncontracted |  |  |
| huisurez | uncontracted |  |  |
| iavardi | uncontracted |  |  |
| intunecoasa | uncontracted |  |  |
| izvoare | uncontracted |  |  |
| jahor patak | uncontracted |  |  |
| jancsik | uncontracted |  |  |
| janik | uncontracted |  |  |
| jgeabul ceagailor | uncontracted |  |  |
| jgheabul cherecului | uncontracted |  |  |
| jgheabul urzicariei | uncontracted |  |  |
| jolotca | present | AVPS MIERCUREA-CIUC |  |
| kis kurusz patak | uncontracted |  |  |
| kupu vize | uncontracted |  |  |
| la hotar | uncontracted |  |  |
| ladok pataka | uncontracted |  |  |
| lapos | uncontracted |  |  |
| licas | uncontracted |  |  |
| lukobukk patak | uncontracted |  |  |
| lunca | uncontracted |  |  |
| lunca mare | uncontracted |  |  |
| lunca mica | uncontracted |  |  |
| lupul | uncontracted |  |  |
| madaras | uncontracted |  |  |
| madarasul mare | present | AVPS MIERCUREA-CIUC |  |
| madicea | uncontracted |  |  |
| malnoves | uncontracted |  |  |
| mediasul | uncontracted |  |  |
| mesteacanul mare | uncontracted |  |  |
| mures | present | AJVPS MUREȘ |  |
| nierghes | uncontracted |  |  |
| oaia | uncontracted |  |  |
| olt | present | AJVPS COVASNA |  |
| oniga | uncontracted |  |  |
| p cetatii | uncontracted |  |  |
| p lui let | uncontracted |  |  |
| padina | uncontracted |  |  |
| paltinisul | uncontracted |  |  |
| parau borvizului | uncontracted |  |  |
| parau caracau | uncontracted |  |  |
| parau chiurchianului | uncontracted |  |  |
| parau omlas | uncontracted |  |  |
| paraul arsita | uncontracted |  |  |
| paraul arsita aramei | uncontracted |  |  |
| paraul asaul alb | uncontracted |  |  |
| paraul bailor | uncontracted |  |  |
| paraul band | uncontracted |  |  |
| paraul banos | uncontracted |  |  |
| paraul barzava | present | AP BANATUL |  |
| paraul batului | uncontracted |  |  |
| paraul bodoc | uncontracted |  |  |
| paraul bothavas | uncontracted |  |  |
| paraul bratesului | uncontracted |  |  |
| paraul bukkeszka | uncontracted |  |  |
| paraul cad | uncontracted |  |  |
| paraul cad mare | uncontracted |  |  |
| paraul cadul mic | uncontracted |  |  |
| paraul caloda | uncontracted |  |  |
| paraul capelei | uncontracted |  |  |
| paraul cartofului | uncontracted |  |  |
| paraul cetatii | uncontracted |  |  |
| paraul cheontid | uncontracted |  |  |
| paraul chighenilor | uncontracted |  |  |
| paraul cianod | uncontracted |  |  |
| paraul ciherek | uncontracted |  |  |
| paraul colina mare | uncontracted |  |  |
| paraul colina mica | uncontracted |  |  |
| paraul comiat | uncontracted |  |  |
| paraul crusitu | uncontracted |  |  |
| paraul csikik | uncontracted |  |  |
| paraul cu smeurisu | uncontracted |  |  |
| paraul curut | uncontracted |  |  |
| paraul delnita | uncontracted |  |  |
| paraul ditrau | uncontracted |  |  |
| paraul dobak | uncontracted |  |  |
| paraul drept | uncontracted |  |  |
| paraul drumul lui gavrila | uncontracted |  |  |
| paraul ecem | uncontracted |  |  |
| paraul egret | uncontracted |  |  |
| paraul fagul ciobanului | uncontracted |  |  |
| paraul fagul ingust | uncontracted |  |  |
| paraul fagului | uncontracted |  |  |
| paraul fagului ingust | uncontracted |  |  |
| paraul fagului rotund | uncontracted |  |  |
| paraul fata | uncontracted |  |  |
| paraul fierarilor | uncontracted |  |  |
| paraul filio | uncontracted |  |  |
| paraul focsenilor | uncontracted |  |  |
| paraul galusa | uncontracted |  |  |
| paraul garbea | uncontracted |  |  |
| paraul gheorghe matei | uncontracted |  |  |
| paraul ghidut | uncontracted |  |  |
| paraul groapa apei | uncontracted |  |  |
| paraul groapa usrului | uncontracted |  |  |
| paraul heviz | uncontracted |  |  |
| paraul hivac | uncontracted |  |  |
| paraul homorod | present | AJPS Brașov |  |
| paraul hotar | uncontracted |  |  |
| paraul imre | uncontracted |  |  |
| paraul intunecos | uncontracted |  |  |
| paraul jartok | uncontracted |  |  |
| paraul kurta | uncontracted |  |  |
| paraul lazarea | uncontracted |  |  |
| paraul loc | uncontracted |  |  |
| paraul locul scurt | uncontracted |  |  |
| paraul lofirez | uncontracted |  |  |
| paraul lui gheorghita | uncontracted |  |  |
| paraul lui melot | uncontracted |  |  |
| paraul lunca | uncontracted |  |  |
| paraul lunca bobasa | uncontracted |  |  |
| paraul lunecos | uncontracted |  |  |
| paraul lupi | uncontracted |  |  |
| paraul madaras | uncontracted |  |  |
| paraul madarasul mic | uncontracted |  |  |
| paraul mare | present | AVPS MIERCUREA-CIUC |  |
| paraul martonca | uncontracted |  |  |
| paraul morareni | uncontracted |  |  |
| paraul mortonea | uncontracted |  |  |
| paraul muhos | uncontracted |  |  |
| paraul murelor | uncontracted |  |  |
| paraul negru | present | AJVPS COVASNA | audit_match:prefix |
| paraul nicolesti | uncontracted |  |  |
| paraul nyikak | uncontracted |  |  |
| paraul oltovani | uncontracted |  |  |
| paraul palos | uncontracted |  |  |
| paraul pauleni | uncontracted |  |  |
| paraul pericolul | uncontracted |  |  |
| paraul pietros | uncontracted |  |  |
| paraul poteca noua | uncontracted |  |  |
| paraul prisca | uncontracted |  |  |
| paraul rata | uncontracted |  |  |
| paraul rece | uncontracted |  |  |
| paraul rosu | present | Direcția Silvică Harghita |  |
| paraul salamas | uncontracted |  |  |
| paraul sandru | uncontracted |  |  |
| paraul saracilor | uncontracted |  |  |
| paraul saraturii | uncontracted |  |  |
| paraul sec | uncontracted |  |  |
| paraul seche | uncontracted |  |  |
| paraul sedloca | uncontracted |  |  |
| paraul senetea | uncontracted |  |  |
| paraul sentes | uncontracted |  |  |
| paraul sep | uncontracted |  |  |
| paraul silos | uncontracted |  |  |
| paraul singai | uncontracted |  |  |
| paraul solonca | uncontracted |  |  |
| paraul szent miklos | uncontracted |  |  |
| paraul szocsok | uncontracted |  |  |
| paraul talnic | uncontracted |  |  |
| paraul tasa | uncontracted |  |  |
| paraul torda | uncontracted |  |  |
| paraul udvar | uncontracted |  |  |
| paraul urasag | uncontracted |  |  |
| paraul ursu | uncontracted |  |  |
| paraul uscat | uncontracted |  |  |
| paraul utusoi | uncontracted |  |  |
| patul cel mare | uncontracted |  |  |
| piciorul | uncontracted |  |  |
| piciorul scurt | uncontracted |  |  |
| pietrosu | uncontracted |  |  |
| poiana fagului | uncontracted |  |  |
| porcul | uncontracted |  |  |
| pr cad | uncontracted |  |  |
| pr cepega | uncontracted |  |  |
| pr hivac | uncontracted |  |  |
| pr ilont | uncontracted |  |  |
| pr kurta | uncontracted |  |  |
| pr lunca bobasa | uncontracted |  |  |
| pr oltovani | uncontracted |  |  |
| pr sedloca | uncontracted |  |  |
| pustnicul | uncontracted |  |  |
| putna | present | Direcția Silvică Suceava | romsilva_map:exact |
| putna intunecoasa | uncontracted |  |  |
| putna noroioasa | uncontracted |  |  |
| racosul mare | uncontracted |  |  |
| racosul mic | uncontracted |  |  |
| racul | uncontracted |  |  |
| radu | uncontracted |  |  |
| rata | uncontracted |  |  |
| raul bardos | uncontracted |  |  |
| raul trotus | present | AJVPS BACĂU |  |
| rezul mare | uncontracted |  |  |
| rompatel | uncontracted |  |  |
| roseni | uncontracted |  |  |
| saca | uncontracted |  |  |
| sadocut | uncontracted |  |  |
| sadocutu | uncontracted |  |  |
| saloc | uncontracted |  |  |
| sarariei | uncontracted |  |  |
| scursura | uncontracted |  |  |
| seche | uncontracted |  |  |
| seghes | uncontracted |  |  |
| sermasau | uncontracted |  |  |
| sicasau | present | AVPS TÂRNAVA MARE |  |
| simina | uncontracted |  |  |
| sina | uncontracted |  |  |
| sipos | uncontracted |  |  |
| soarecul | uncontracted |  |  |
| stiuca | uncontracted |  |  |
| sugau | uncontracted |  |  |
| suhard | uncontracted |  |  |
| sulta | present | AJVPS BACĂU |  |
| sumuleu | uncontracted |  |  |
| szasz patak | uncontracted |  |  |
| szelhas | uncontracted |  |  |
| szenete patak | uncontracted |  |  |
| tarvezul | uncontracted |  |  |
| tatarul | uncontracted |  |  |
| telec | uncontracted |  |  |
| tepeseni | uncontracted |  |  |
| tibec | uncontracted |  |  |
| tibre | uncontracted |  |  |
| ticos | uncontracted |  |  |
| tisasu | uncontracted |  |  |
| trotus | present | AJVPS BACĂU |  |
| ugra | uncontracted |  |  |
| v antaloc | uncontracted |  |  |
| valea adanca | uncontracted |  |  |
| valea babasa | uncontracted |  |  |
| valea cremenii | uncontracted |  |  |
| valea noscolat | uncontracted |  |  |
| valea oii | uncontracted |  |  |
| valea rece | uncontracted |  |  |
| varga patak | uncontracted |  |  |
| varghis | present | AJVPS COVASNA | audit_match:exact |
| vetea mare | uncontracted |  |  |

### Celulă 46.4-46.9N, 26.0-26.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| apries | uncontracted |  |  |
| ardele | uncontracted |  |  |
| ardeluta | uncontracted |  |  |
| arinisul | uncontracted |  |  |
| asau | present | AJVPS BACĂU |  |
| barnisul | uncontracted |  |  |
| batca | uncontracted |  |  |
| bicaz | present | AJVPS NEAMȚ | bbox_fix:lake:Lacul Izvorul Muntelui |
| bistrita | present | AJVPS NEAMȚ | anpa_map:bistrita-basin |
| boros | uncontracted |  |  |
| borta ursului | uncontracted |  |  |
| bothavas | uncontracted |  |  |
| brates | uncontracted |  |  |
| calu | uncontracted |  |  |
| camenca | uncontracted |  |  |
| carpenul | uncontracted |  |  |
| casaria | uncontracted |  |  |
| cheita | uncontracted |  |  |
| cichiva | uncontracted |  |  |
| cichivei | uncontracted |  |  |
| ciobanus | present | AJVPS BACĂU |  |
| ciungi | uncontracted |  |  |
| cojocul | uncontracted |  |  |
| cracau | uncontracted |  |  |
| cracul tazlau | uncontracted |  |  |
| cseke hago patak | uncontracted |  |  |
| danesti | uncontracted |  |  |
| dosetel | uncontracted |  |  |
| floarea | uncontracted |  |  |
| frasinul | uncontracted |  |  |
| frumoasa | present | AVPS MIERCUREA-CIUC |  |
| gaina | uncontracted |  |  |
| garbea | uncontracted |  |  |
| gosmanu | uncontracted |  |  |
| hanu | uncontracted |  |  |
| hanul | uncontracted |  |  |
| herman | uncontracted |  |  |
| hotarul | uncontracted |  |  |
| iapa | present | Direcția Silvică Neamț | romsilva_map:exact |
| izvorul alb | present | AJVPS CARAȘ-SEVERIN | multiway_chain |
| jancsik | uncontracted |  |  |
| janik | uncontracted |  |  |
| jgheabu mare | uncontracted |  |  |
| jghiabu larg | uncontracted |  |  |
| malina | uncontracted |  |  |
| mastacanul | uncontracted |  |  |
| meleius | uncontracted |  |  |
| murgoci | present | AJVPS VÂLCEA |  |
| nechit | uncontracted |  |  |
| oantu | uncontracted |  |  |
| pararul dracoiu | uncontracted |  |  |
| paraul alachec | uncontracted |  |  |
| paraul aldamas | uncontracted |  |  |
| paraul apahavas | uncontracted |  |  |
| paraul ardelea | uncontracted |  |  |
| paraul arsita | uncontracted |  |  |
| paraul berbecilor | uncontracted |  |  |
| paraul bisericii | uncontracted |  |  |
| paraul bolovanis | uncontracted |  |  |
| paraul borjuvesz | uncontracted |  |  |
| paraul bortoseni | uncontracted |  |  |
| paraul bothavas | uncontracted |  |  |
| paraul buha | uncontracted |  |  |
| paraul cailor | uncontracted |  |  |
| paraul capelei | uncontracted |  |  |
| paraul catargelului | uncontracted |  |  |
| paraul cheontid | uncontracted |  |  |
| paraul cihanios | uncontracted |  |  |
| paraul ciurghes | uncontracted |  |  |
| paraul coacaza | uncontracted |  |  |
| paraul craca popoiului | uncontracted |  |  |
| paraul crasna | present | AJVPS VASLUI | anpa_map:sweep:crasna |
| paraul crasnita | uncontracted |  |  |
| paraul croitorilor | uncontracted |  |  |
| paraul crusitu | uncontracted |  |  |
| paraul csikik | uncontracted |  |  |
| paraul cu smeurisu | uncontracted |  |  |
| paraul cuchinis | uncontracted |  |  |
| paraul cujbelor | uncontracted |  |  |
| paraul dracoiu | uncontracted |  |  |
| paraul drum nou | uncontracted |  |  |
| paraul fundoaiei | uncontracted |  |  |
| paraul gazului | uncontracted |  |  |
| paraul gontu | uncontracted |  |  |
| paraul izvorului | uncontracted |  |  |
| paraul la jgheab | uncontracted |  |  |
| paraul laptoacelor | uncontracted |  |  |
| paraul lat | uncontracted |  |  |
| paraul lespezi | uncontracted |  |  |
| paraul lofirez | uncontracted |  |  |
| paraul lui herman | uncontracted |  |  |
| paraul lui molnar | uncontracted |  |  |
| paraul lui nita | uncontracted |  |  |
| paraul lui taciune | uncontracted |  |  |
| paraul lupului | uncontracted |  |  |
| paraul mare | present | AVPS MIERCUREA-CIUC |  |
| paraul negru | present | AJVPS COVASNA | audit_match:prefix |
| paraul nilenc | uncontracted |  |  |
| paraul nyikak | uncontracted |  |  |
| paraul palistineni | uncontracted |  |  |
| paraul pascu | uncontracted |  |  |
| paraul pasculetul | uncontracted |  |  |
| paraul petrut | uncontracted |  |  |
| paraul popoiu | uncontracted |  |  |
| paraul potoci | uncontracted |  |  |
| paraul prelucaci | uncontracted |  |  |
| paraul radului | uncontracted |  |  |
| paraul rapelor | uncontracted |  |  |
| paraul scurt | uncontracted |  |  |
| paraul simo | uncontracted |  |  |
| paraul smida rosie | uncontracted |  |  |
| paraul soimul | uncontracted |  |  |
| paraul sugura | uncontracted |  |  |
| paraul taca | uncontracted |  |  |
| paraul tekenyos | uncontracted |  |  |
| paraul tinioasa | uncontracted |  |  |
| paraul toplita | present | AV VIDA SURDUCEL DOBREȘTI |  |
| paraul troci | uncontracted |  |  |
| paraul tulbure | uncontracted |  |  |
| paraul ursului | uncontracted |  |  |
| paraul verde | uncontracted |  |  |
| pascu | uncontracted |  |  |
| ponor | uncontracted |  |  |
| porcarici | uncontracted |  |  |
| rachita | uncontracted |  |  |
| raul agas | uncontracted |  |  |
| raul agasul | uncontracted |  |  |
| raul ciobanus | present | AJVPS BACĂU |  |
| raul cotumba | uncontracted |  |  |
| raul seaca | uncontracted |  |  |
| raul sulta | present | AJVPS BACĂU |  |
| raul tazlau | present | AJVPS BACĂU |  |
| raul trotus | present | AJVPS BACĂU |  |
| raul urmenis | uncontracted |  |  |
| runcul | uncontracted |  |  |
| santul | uncontracted |  |  |
| secu mahlit | uncontracted |  |  |
| smardan | uncontracted |  |  |
| stuhul | uncontracted |  |  |
| stuhuletul | uncontracted |  |  |
| sulta | present | AJVPS BACĂU |  |
| tapu | uncontracted |  |  |
| tarcau | present | Direcția Silvică Neamț | romsilva_map:group-shares-course |
| tarcaul | uncontracted |  |  |
| tarcuta | uncontracted |  |  |
| tarhaos | uncontracted |  |  |
| tarhausi | uncontracted |  |  |
| tazlau | present | AJVPS BACĂU |  |
| tazlaul sarat | present | AJVPS BACĂU |  |
| trotus | present | AJVPS BACĂU |  |
| ugra | uncontracted |  |  |
| valea batrana | uncontracted |  |  |
| valea rece | uncontracted |  |  |
| varari | uncontracted |  |  |
| veverita | uncontracted |  |  |
| vitioara | uncontracted |  |  |

### Celulă 46.4-46.9N, 26.5-27.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| barnat | uncontracted |  |  |
| bistrita | present | AJVPS BACĂU | anpa_map:bistrita-basin |
| bolborositoarea | uncontracted |  |  |
| boul | uncontracted |  |  |
| brateasca | uncontracted |  |  |
| coman | uncontracted |  |  |
| cracau | uncontracted |  |  |
| frumoasa | present | AVPS MIERCUREA-CIUC |  |
| hociungi | uncontracted |  |  |
| limpedea | uncontracted |  |  |
| lipoveni | uncontracted |  |  |
| nechit | uncontracted |  |  |
| negel | uncontracted |  |  |
| paraul albu | uncontracted |  |  |
| paraul bradului | uncontracted |  |  |
| paraul bursuni | uncontracted |  |  |
| paraul cilnes | uncontracted |  |  |
| paraul ciubotei | uncontracted |  |  |
| paraul codiului | uncontracted |  |  |
| paraul cu ulmi | uncontracted |  |  |
| paraul larg | uncontracted |  |  |
| paraul letcana | uncontracted |  |  |
| paraul racova | present | AJVPS VASLUI | audit_match:exact |
| paraul runcu | present | Direcția Silvică Dâmbovița | romsilva_map:token0.00 |
| paraul rupturei | uncontracted |  |  |
| paraul valea seaca | uncontracted |  |  |
| paraul verde | uncontracted |  |  |
| paraul zanoaga | present | Direcția Silvică Hunedoara | bbox_fix:lake:Lacul Zănoaga Mare |
| precista | uncontracted |  |  |
| rachitis | uncontracted |  |  |
| raul tazlau | present | AJVPS BACĂU |  |
| romani | uncontracted |  |  |
| siret | present | Centrul Regional de Ecologie Bacău |  |
| tazlau | present | AJVPS BACĂU |  |
| tazlaul sarat | present | AJVPS BACĂU |  |
| trebes | uncontracted |  |  |
| turbata | uncontracted |  |  |
| undrei | uncontracted |  |  |

### Celulă 46.4-46.9N, 27.0-27.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| barlad | present | AJVPS VASLUI |  |
| brateasca | uncontracted |  |  |
| duraceasa | uncontracted |  |  |
| duraceasca | uncontracted |  |  |
| garboveta | uncontracted |  |  |
| gaureni | uncontracted |  |  |
| raul stavnic | uncontracted |  |  |
| sacovat | uncontracted |  |  |
| siret | present | Centrul Regional de Ecologie Bacău |  |
| velna | uncontracted |  |  |

### Celulă 46.4-46.9N, 27.5-28.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| barlad | present | AJVPS VASLUI |  |
| crasna | present | AJVPS VASLUI | anpa_map:sweep:crasna |
| dobrovat | uncontracted |  |  |
| paraul ciortesti | uncontracted |  |  |
| raul barlad | present | AJVPS VASLUI |  |
| raul crasna | present | AJVPS VASLUI | anpa_map:sweep:crasna |
| raul mosna | uncontracted |  |  |
| raul rebricea | uncontracted |  |  |
| rediu | uncontracted |  |  |
| tutova | present | AJVPS VASLUI |  |
| vaslui | uncontracted |  |  |

### Celulă 46.4-46.9N, 28.0-28.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| gura vaii | uncontracted |  |  |
| husi | uncontracted |  |  |
| lapusna | uncontracted |  |  |
| paraul lui ivan | uncontracted |  |  |
| prut | present | AVPS IAȘI |  |
| prut / прут | uncontracted |  |  |
| raul mosna | uncontracted |  |  |
| raul mosnisoara | uncontracted |  |  |
| recea | uncontracted |  |  |
| sarata | present | AJVPS BOTOȘANI |  |

### Celulă 46.4-46.9N, 28.5-29.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bardar | uncontracted |  |  |
| botna | uncontracted |  |  |
| botnisoara | uncontracted |  |  |
| cainar | uncontracted |  |  |
| ceaga | uncontracted |  |  |
| cogalnic | uncontracted |  |  |
| hatia | uncontracted |  |  |
| ialpug | uncontracted |  |  |
| raul cogalnic | uncontracted |  |  |
| schinoasa | uncontracted |  |  |
| valea baltati | uncontracted |  |  |
| valea budai | uncontracted |  |  |
| valea gradistei | uncontracted |  |  |
| valea misovca | uncontracted |  |  |
| valea negrea | uncontracted |  |  |
| valea rapa | uncontracted |  |  |
| valea sarmeza | uncontracted |  |  |
| valea schinoasa | uncontracted |  |  |
| valea tipalei | uncontracted |  |  |
| скіноса | uncontracted |  |  |

### Celulă 46.4-46.9N, 29.0-29.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bic | uncontracted |  |  |
| botna | uncontracted |  |  |
| cainar | uncontracted |  |  |
| calantir | uncontracted |  |  |
| ceaga | uncontracted |  |  |
| girlo | uncontracted |  |  |
| jidovca | uncontracted |  |  |
| larga | uncontracted |  |  |
| nistru днестр | uncontracted |  |  |
| pirau | uncontracted |  |  |
| raul ceaga | uncontracted |  |  |
| saca | uncontracted |  |  |
| sarata | present | AJVPS BOTOȘANI |  |
| valea misovca | uncontracted |  |  |
| valea puhoiului | uncontracted |  |  |
| valea schinoasa | uncontracted |  |  |
| valea varaticului | uncontracted |  |  |
| volontir | uncontracted |  |  |
| арса | uncontracted |  |  |
| балка | uncontracted |  |  |
| балка комарова | uncontracted |  |  |
| гырло | uncontracted |  |  |
| дністер / nistru | uncontracted |  |  |
| жидівка | uncontracted |  |  |
| кантемір | uncontracted |  |  |
| сака | uncontracted |  |  |
| сарата | uncontracted |  |  |
| чага | uncontracted |  |  |

### Celulă 46.4-46.9N, 29.5-30.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| babei | uncontracted |  |  |
| botna | uncontracted |  |  |
| copceac | uncontracted |  |  |
| gealair | uncontracted |  |  |
| girlo | uncontracted |  |  |
| nistru днестр | uncontracted |  |  |
| nistrul vechi | uncontracted |  |  |
| nistrul vechi / старыи днестр | uncontracted |  |  |
| nistrul vechi старыи днестр | uncontracted |  |  |
| бабеи | uncontracted |  |  |
| балка комарова | uncontracted |  |  |
| ботна | uncontracted |  |  |
| джалаір | uncontracted |  |  |
| дністер / nistru | uncontracted |  |  |
| кучурган / cuciurgan | uncontracted |  |  |
| ручеи светлыи | uncontracted |  |  |
| ручеи чистыи | uncontracted |  |  |
| сарата | uncontracted |  |  |
| турунчук | uncontracted |  |  |

### Celulă 46.9-47.4N, 20.0-20.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| danube | uncontracted |  |  |
| harmas koros | uncontracted |  |  |
| holt zagyva | uncontracted |  |  |
| karancs er | uncontracted |  |  |
| tisza | uncontracted |  |  |
| zagyva | uncontracted |  |  |

### Celulă 46.9-47.4N, 20.5-21.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| crisul repede | present | AJVPS BIHOR |  |
| danube | uncontracted |  |  |
| felso rehelyi csatorna | uncontracted |  |  |
| harmas koros | uncontracted |  |  |
| hortobagy berettyo focsatorna | uncontracted |  |  |
| kettos koros | uncontracted |  |  |
| nagykodmonos gorbeszigeti csatorna | uncontracted |  |  |
| sebes koros | uncontracted |  |  |
| szolostanyai csatorna | uncontracted |  |  |
| tisza | uncontracted |  |  |

### Celulă 46.9-47.4N, 21.0-21.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| akaszto er | uncontracted |  |  |
| arok | uncontracted |  |  |
| barcau/berettyo | uncontracted |  |  |
| berettyo | uncontracted |  |  |
| bungosdi focsatorna | uncontracted |  |  |
| crisul repede | present | AJVPS BIHOR |  |
| csente er | uncontracted |  |  |
| csorsz arka | uncontracted |  |  |
| danube | uncontracted |  |  |
| halcsatorna | uncontracted |  |  |
| hortobagy | uncontracted |  |  |
| hortobagy berettyo focsatorna | uncontracted |  |  |
| kettos koros | uncontracted |  |  |
| kutas focsatorna | uncontracted |  |  |
| nagykodmonos gorbeszigeti csatorna | uncontracted |  |  |
| olyvos er | uncontracted |  |  |
| sebes koros | uncontracted |  |  |
| toprongyos korhany csatorna | uncontracted |  |  |

### Celulă 46.9-47.4N, 21.5-22.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| adona | uncontracted |  |  |
| bagameri er | uncontracted |  |  |
| barat er | uncontracted |  |  |
| barcau | present | AJVPS BIHOR |  |
| barcau/berettyo | uncontracted |  |  |
| berettyo | uncontracted |  |  |
| cerna | present | Direcția Silvică Mehedinți | sweep:hidden:group-shares-course |
| cozmau | uncontracted |  |  |
| crisul mic | uncontracted |  |  |
| crisul mic/kis koros | uncontracted |  |  |
| crisul repede | present | AJVPS BIHOR |  |
| csente er | uncontracted |  |  |
| csikos er | uncontracted |  |  |
| danube | uncontracted |  |  |
| hencida csereerdo csatorna | uncontracted |  |  |
| ier | present | AJVPS TIMIȘ | audit_match:exact |
| kis palyi er | uncontracted |  |  |
| konyari kallo | uncontracted |  |  |
| kutas focsatorna | uncontracted |  |  |
| letai er | uncontracted |  |  |
| monostori er | uncontracted |  |  |
| olyvos er | uncontracted |  |  |
| palyi er | uncontracted |  |  |
| peta | present | AJVPS BIHOR |  |
| saros er | uncontracted |  |  |
| sebes koros | uncontracted |  |  |
| toprongyos korhany csatorna | uncontracted |  |  |
| villongo er | uncontracted |  |  |

### Celulă 46.9-47.4N, 22.0-22.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| barcau | present | AJVPS BIHOR |  |
| barcau/berettyo | uncontracted |  |  |
| bistra | present | AJVPS MUREȘ |  |
| copacel | uncontracted |  |  |
| cozmau | uncontracted |  |  |
| crisul repede | present | AJVPS BIHOR |  |
| danube | uncontracted |  |  |
| ghepes | uncontracted |  |  |
| ier | present | AJVPS TIMIȘ | audit_match:exact |
| inot | uncontracted |  |  |
| paraul dobricionesti | present | AJVPS BIHOR | audit_match:override |
| paraul iacoboaia | uncontracted |  |  |
| paraul mniera | uncontracted |  |  |
| paraul vida | present | AJVPS BIHOR |  |
| sarcau vale | uncontracted |  |  |
| valea hutii | uncontracted |  |  |
| valea pestireului | uncontracted |  |  |
| valea sinteului | uncontracted |  |  |

### Celulă 46.9-47.4N, 22.5-23.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| agrij | present | AJVPS SĂLAJ |  |
| almas | uncontracted |  |  |
| babiu | uncontracted |  |  |
| barcau | present | AJVPS BIHOR |  |
| barcau/berettyo | uncontracted |  |  |
| bistra | present | AJVPS MUREȘ |  |
| crasna | present | AJVPS SĂLAJ | anpa_map:sweep |
| crisul repede | present | AJVPS BIHOR |  |
| dragan | present | Direcția Silvică Bihor | romsilva_map:exact |
| iada | uncontracted |  |  |
| kraszna | uncontracted |  |  |
| mihaesti | uncontracted |  |  |
| paraul bratcuta | uncontracted |  |  |
| paraul butgheorghesti | uncontracted |  |  |
| paraul misid | uncontracted |  |  |
| paraul negruta | uncontracted |  |  |
| paraul rachitelor | uncontracted |  |  |
| paraul scridosului | uncontracted |  |  |
| paraul secatura | uncontracted |  |  |
| paraul toplita | present | AV VIDA SURDUCEL DOBREȘTI |  |
| paraul zalau | present | AJVPS SĂLAJ | audit_match:override |
| raul agrij | present | AJVPS SĂLAJ |  |
| saracelu | uncontracted |  |  |
| styx | uncontracted |  |  |
| valea banului | uncontracted |  |  |
| valea boiului | uncontracted |  |  |
| valea caselor | present | AJVPS ALBA |  |
| valea fagetului | uncontracted |  |  |
| valea huta | uncontracted |  |  |
| valea maguricii | uncontracted |  |  |
| valea negreni | present | ANPA - Ape Necontractate | bbox_fix:lake-unnamed: |

### Celulă 46.9-47.4N, 23.0-23.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| adalin | uncontracted |  |  |
| agrij | present | AJVPS SĂLAJ |  |
| almas | uncontracted |  |  |
| babiu | uncontracted |  |  |
| bezded | uncontracted |  |  |
| borsa | uncontracted |  |  |
| briglez | uncontracted |  |  |
| buda | present | Direcția Silvică Argeș | romsilva_map:exact |
| ceaca | uncontracted |  |  |
| cernuc | uncontracted |  |  |
| clit | uncontracted |  |  |
| cristoltel | uncontracted |  |  |
| cristorel | uncontracted |  |  |
| dolu | uncontracted |  |  |
| dragu | uncontracted |  |  |
| groapa gombosoaiei | uncontracted |  |  |
| hollos patak | uncontracted |  |  |
| jebuc | uncontracted |  |  |
| lonea | uncontracted |  |  |
| lozna | uncontracted |  |  |
| marton | uncontracted |  |  |
| paraul zalau | present | AJVPS SĂLAJ | audit_match:override |
| printre vai | uncontracted |  |  |
| purcaret | uncontracted |  |  |
| raul agrij | present | AJVPS SĂLAJ |  |
| raul garbou | uncontracted |  |  |
| raul rastolt | uncontracted |  |  |
| saliste | present | FLY FISHING CLUB SIBIU |  |
| sancraiu almasului | uncontracted |  |  |
| sardu | uncontracted |  |  |
| saros patak | uncontracted |  |  |
| soimeni | uncontracted |  |  |
| solona | uncontracted |  |  |
| somes | present | AJVPS CLUJ |  |
| somtelec | uncontracted |  |  |
| topa mica | uncontracted |  |  |
| trestia | uncontracted |  |  |
| treznea | uncontracted |  |  |
| ugrutiu | uncontracted |  |  |
| valea babiu | uncontracted |  |  |
| valea dragului | uncontracted |  |  |
| valea dreapta | uncontracted |  |  |
| valea hraii | uncontracted |  |  |
| valea mare | present | Direcția Silvică Alba | romsilva_map:group-shares-course |
| valea mitii | uncontracted |  |  |
| valea morii | uncontracted |  |  |
| valea ortelecului | uncontracted |  |  |
| valea rece | uncontracted |  |  |
| valea voivodeniului | uncontracted |  |  |

### Celulă 46.9-47.4N, 23.5-24.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| badesti | uncontracted |  |  |
| bandau | uncontracted |  |  |
| bobalna | uncontracted |  |  |
| borsa | uncontracted |  |  |
| buda | present | Direcția Silvică Argeș | romsilva_map:exact |
| bunesti | uncontracted |  |  |
| canal | uncontracted |  |  |
| canalul morii | uncontracted |  |  |
| canciu | present | Direcția Silvică Alba | bbox_fix:lake:Canciu |
| ceaca | uncontracted |  |  |
| chidea | uncontracted |  |  |
| ciepega | uncontracted |  |  |
| cormenis | uncontracted |  |  |
| cubles | uncontracted |  |  |
| elciu | uncontracted |  |  |
| faureni | uncontracted |  |  |
| fizes | present | AJPS Cluj |  |
| fundaturi | uncontracted |  |  |
| gadalin | uncontracted |  |  |
| garbaul dejului | uncontracted |  |  |
| ghirolt | uncontracted |  |  |
| giula | uncontracted |  |  |
| gostila | uncontracted |  |  |
| groapa gombosoaiei | uncontracted |  |  |
| guga | uncontracted |  |  |
| hosu | uncontracted |  |  |
| husuer | uncontracted |  |  |
| iapa | present | Direcția Silvică Neamț | romsilva_map:exact |
| ileanda | present | AJVPS SĂLAJ |  |
| jichis | uncontracted |  |  |
| lelesti | uncontracted |  |  |
| lonea | uncontracted |  |  |
| lozna | uncontracted |  |  |
| lujerdiu | uncontracted |  |  |
| mintiu | uncontracted |  |  |
| muncel | uncontracted |  |  |
| nima | uncontracted |  |  |
| olpret | uncontracted |  |  |
| orman | uncontracted |  |  |
| paraul ocnei | uncontracted |  |  |
| pestes | uncontracted |  |  |
| pruni | uncontracted |  |  |
| puini | uncontracted |  |  |
| raul fizes | present | AJPS Cluj |  |
| saca | uncontracted |  |  |
| salatruc | uncontracted |  |  |
| salca | uncontracted |  |  |
| sanasele | uncontracted |  |  |
| santejude | uncontracted |  |  |
| sarata | present | AJVPS BOTOȘANI |  |
| sicu | uncontracted |  |  |
| simisna | uncontracted |  |  |
| soimeni | uncontracted |  |  |
| somes | present | AJVPS CLUJ |  |
| somesul mare | present | AJVPS BISTRIȚA-NĂSĂUD | anpa_map:sweep |
| somesul mic | present | AJVPS CLUJ |  |
| somesul mort | uncontracted |  |  |
| strambu | uncontracted |  |  |
| tioltiur | uncontracted |  |  |
| vad | uncontracted |  |  |
| valea chiejdului | uncontracted |  |  |
| valea cu mori | uncontracted |  |  |
| valea furcilor | uncontracted |  |  |
| valea marului | uncontracted |  |  |
| valea perii | uncontracted |  |  |
| valea peteroaii | uncontracted |  |  |
| valea poiana | present | AJVPS BIHOR |  |
| valea topului | uncontracted |  |  |
| vitroape | uncontracted |  |  |

### Celulă 46.9-47.4N, 24.0-24.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| agris | uncontracted |  |  |
| apatiu | uncontracted |  |  |
| archiud | uncontracted |  |  |
| bandau | uncontracted |  |  |
| batin | uncontracted |  |  |
| beudiu | uncontracted |  |  |
| bichigiu | uncontracted |  |  |
| bistrita | present | AJVPS BISTRIŢA NĂSĂUD |  |
| brateni | uncontracted |  |  |
| bratosa | uncontracted |  |  |
| bretea | uncontracted |  |  |
| budac | uncontracted |  |  |
| bungard | uncontracted |  |  |
| caciu | uncontracted |  |  |
| canci | uncontracted |  |  |
| canciu | present | Direcția Silvică Alba | bbox_fix:lake:Canciu |
| chirales | uncontracted |  |  |
| cotior | uncontracted |  |  |
| dipsa | uncontracted |  |  |
| diviciorii mari | uncontracted |  |  |
| dobricel | uncontracted |  |  |
| dumbravita | present | AJVPS TIMIȘ |  |
| fizes | present | AJPS Cluj |  |
| gaureni | uncontracted |  |  |
| gersa | present | AJVPS BISTRIŢA NĂSĂUD |  |
| halmas | uncontracted |  |  |
| hasmas | uncontracted |  |  |
| husuer | uncontracted |  |  |
| ilisua | present | Direcția Silvică Bistrița-Năsăud | romsilva_map:exact |
| intre hotare | uncontracted |  |  |
| lechinta | present | AJVPS BISTRIȚA-NĂSĂUD |  |
| lunca | uncontracted |  |  |
| magherus | present | AVPS TOPLIȚA |  |
| magura | uncontracted |  |  |
| malin | uncontracted |  |  |
| pintic | uncontracted |  |  |
| pucioasa | present | AJVPS DÂMBOVIȚA | bbox_fix:lake:Lacul de acumulare Pucioasa |
| puini | uncontracted |  |  |
| raul fizes | present | AJPS Cluj |  |
| rebra | present | Direcția Silvică Bistrița-Năsăud | romsilva_map:exact |
| rituria | uncontracted |  |  |
| rosua | present | AJVPS BISTRIŢA NĂSĂUD |  |
| runc | uncontracted |  |  |
| salauta | present | AJVPS BISTRIŢA NĂSĂUD | audit_match:prefix |
| sanmartin | uncontracted |  |  |
| sarata | present | AJVPS BOTOȘANI |  |
| sicu | uncontracted |  |  |
| sieu | present | AJVPS BISTRIŢA NĂSĂUD |  |
| somesul mare | present | AJVPS BISTRIȚA-NĂSĂUD | anpa_map:sweep |
| suciuas | uncontracted |  |  |
| tarpiu | uncontracted |  |  |
| tau | present | Direcția Silvică Alba | romsilva_map:exact |
| tibles | present | AJVPS MARAMUREȘ | anpa_map:sweep:tibles |
| valea aurului | uncontracted |  |  |
| valea blajenilor | uncontracted |  |  |
| valea budacului | uncontracted |  |  |
| valea caselor | present | AJVPS ALBA |  |
| valea lunga | uncontracted |  |  |
| valea mare | present | Direcția Silvică Alba | romsilva_map:group-shares-course |
| valea meles | present | AJVPS BISTRIȚA-NĂSĂUD | audit_match:override |
| valea mica | uncontracted |  |  |
| valea morii | uncontracted |  |  |
| valea negrilestilor | uncontracted |  |  |
| valea poienii | uncontracted |  |  |
| valea satului | uncontracted |  |  |
| valea sigmirului | uncontracted |  |  |
| valea stanelor | uncontracted |  |  |
| valea tarpiu | uncontracted |  |  |
| valea topului | uncontracted |  |  |
| valea viilor | uncontracted |  |  |

### Celulă 46.9-47.4N, 24.5-25.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| ardan | uncontracted |  |  |
| arsita | uncontracted |  |  |
| bargau | uncontracted |  |  |
| bistra | present | AJVPS MUREȘ |  |
| bistrita | present | AJVPS BISTRIŢA NĂSĂUD |  |
| blajul | uncontracted |  |  |
| blidareasa | uncontracted |  |  |
| bolovan | uncontracted |  |  |
| borcut | uncontracted |  |  |
| borzia | uncontracted |  |  |
| bradul | uncontracted |  |  |
| budac | uncontracted |  |  |
| budus | uncontracted |  |  |
| budusel | uncontracted |  |  |
| buduselu | uncontracted |  |  |
| colbu | uncontracted |  |  |
| corca | uncontracted |  |  |
| cormaia | present | AJVPS BISTRIŢA NĂSĂUD |  |
| cucureasa | uncontracted |  |  |
| cusma | uncontracted |  |  |
| donca | uncontracted |  |  |
| erboasa | uncontracted |  |  |
| fanatele | uncontracted |  |  |
| feldrisel | uncontracted |  |  |
| galaoaia | present | AJVPS MUREȘ |  |
| gersa | present | AJVPS BISTRIŢA NĂSĂUD |  |
| ghinda | uncontracted |  |  |
| iad | uncontracted |  |  |
| ilva | present | Direcția Silvică Mureș | romsilva_map:exact |
| ivaneasa | uncontracted |  |  |
| izvorul lung | present | AJVPS CARAȘ-SEVERIN | audit_match:exact |
| jisa | uncontracted |  |  |
| lesul | uncontracted |  |  |
| lut | present | AJVPS MUREȘ | audit_match:exact |
| magura | uncontracted |  |  |
| muncel | uncontracted |  |  |
| mures | present | AJVPS MUREȘ |  |
| obarsie | uncontracted |  |  |
| panu | uncontracted |  |  |
| panulet | uncontracted |  |  |
| parau carligaturilor | uncontracted |  |  |
| parau stiubeiului | uncontracted |  |  |
| paraul ardanului | uncontracted |  |  |
| paraul iodul | uncontracted |  |  |
| paraul jiului | uncontracted |  |  |
| paraul lut | present | AJVPS MUREȘ | audit_match:exact |
| paraul plotonului | uncontracted |  |  |
| paraul stegii | present | A.FLY FISHING CLUB SIBIU | audit_match:override |
| petris | present | Direcția Silvică Arad | romsilva_map:exact |
| pietris | uncontracted |  |  |
| pietroasa | uncontracted |  |  |
| pintic | uncontracted |  |  |
| poiana | present | AJVPS BIHOR |  |
| rapa | uncontracted |  |  |
| rastolita | present | AJVPS MUREȘ |  |
| rebra | present | Direcția Silvică Bistrița-Năsăud | romsilva_map:exact |
| repedea | present | Direcția Silvică Maramureș | romsilva_map:exact |
| sacal | uncontracted |  |  |
| secul | uncontracted |  |  |
| ses | present | Direcția Silvică Hunedoara | romsilva_map:sweep:raul ses |
| sieu | present | AJVPS BISTRIŢA NĂSĂUD |  |
| silhoasa | uncontracted |  |  |
| slatinita | uncontracted |  |  |
| soimul de sus | present | FLY FISHING CLUB SIBIU |  |
| somesul mare | present | AJVPS BISTRIȚA-NĂSĂUD | anpa_map:sweep |
| stana | uncontracted |  |  |
| strada rusului | uncontracted |  |  |
| stramba | present | AJPS Brașov |  |
| surupatura | uncontracted |  |  |
| tanase | uncontracted |  |  |
| targul | uncontracted |  |  |
| tisa | present | AJVPS MARAMUREȘ |  |
| tureac | uncontracted |  |  |
| uila | uncontracted |  |  |
| ulmul | uncontracted |  |  |
| ursoaia | uncontracted |  |  |
| valcalita | uncontracted |  |  |
| valea aurului | uncontracted |  |  |
| valea borcutului | uncontracted |  |  |
| valea budacului | uncontracted |  |  |
| valea carelor | uncontracted |  |  |
| valea ghinzii | uncontracted |  |  |
| valea jelnei | uncontracted |  |  |
| valea lesilor | uncontracted |  |  |
| valea lui dan | uncontracted |  |  |
| valea mare | present | AVPS MIERCUREA-CIUC |  |
| valea mica | uncontracted |  |  |
| valea pustie | uncontracted |  |  |
| valea rusului | uncontracted |  |  |
| valea satului | uncontracted |  |  |
| valeni | uncontracted |  |  |
| zapodea cu cale | uncontracted |  |  |
| zapodea cu pod | uncontracted |  |  |

### Celulă 46.9-47.4N, 25.0-25.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| argestru | uncontracted |  |  |
| bargau | uncontracted |  |  |
| barnaru | uncontracted |  |  |
| bezna | uncontracted |  |  |
| bistricioara | present | AJVPS VÂLCEA |  |
| bistrita | present | AJVPS BISTRIŢA NĂSĂUD |  |
| bistrita aurie | present | Direcția Silvică Maramureș | romsilva_map:exact |
| bolovan | uncontracted |  |  |
| bradul | uncontracted |  |  |
| bucinis | uncontracted |  |  |
| cabana | uncontracted |  |  |
| calimanel | present | AVPS TOPLIȚA |  |
| calul | uncontracted |  |  |
| cascada | uncontracted |  |  |
| cibeu | uncontracted |  |  |
| cica mare | uncontracted |  |  |
| cica mica | uncontracted |  |  |
| cocosul | uncontracted |  |  |
| colbu | uncontracted |  |  |
| corca | uncontracted |  |  |
| creanga | uncontracted |  |  |
| cucubertul mare | uncontracted |  |  |
| cucubertul mic | uncontracted |  |  |
| cucureasa | uncontracted |  |  |
| doamna | uncontracted |  |  |
| dorna | present | AJVPS BOTOȘANI | audit_match:prefix |
| dornisoara | present | Direcția Silvică Suceava | romsilva_map:exact |
| dragus | uncontracted |  |  |
| dusa | uncontracted |  |  |
| ferigelor | uncontracted |  |  |
| filipea | uncontracted |  |  |
| frasinelul | uncontracted |  |  |
| ghilosa | uncontracted |  |  |
| haita | uncontracted |  |  |
| ilisoara | uncontracted |  |  |
| ilisoara mare | uncontracted |  |  |
| ilisoara mica | uncontracted |  |  |
| ilva | present | Direcția Silvică Mureș | romsilva_map:exact |
| izvorul lung | present | AJVPS CARAȘ-SEVERIN | audit_match:exact |
| jingul cadarenilor | uncontracted |  |  |
| jnepenisul | uncontracted |  |  |
| lomasita | uncontracted |  |  |
| lomasul | uncontracted |  |  |
| magherus | present | AVPS TOPLIȚA |  |
| mermezeu | uncontracted |  |  |
| mihailet | uncontracted |  |  |
| moldisul | uncontracted |  |  |
| mures | present | AJVPS MUREȘ |  |
| neagra | present | Direcția Silvică Suceava | romsilva_map:group-shares-course |
| neagra sarului | uncontracted |  |  |
| negoiul | uncontracted |  |  |
| negrisoara | uncontracted |  |  |
| paraul andreneasa | uncontracted |  |  |
| paraul arsa | uncontracted |  |  |
| paraul arsita | uncontracted |  |  |
| paraul belciu | uncontracted |  |  |
| paraul ciobotani | uncontracted |  |  |
| paraul corbu | uncontracted |  |  |
| paraul creanga | uncontracted |  |  |
| paraul cucuta din fata | uncontracted |  |  |
| paraul doamnei | present | AJVPS ARGEȘ | audit_match:prefix |
| paraul fodoreni | uncontracted |  |  |
| paraul ghiorfas | uncontracted |  |  |
| paraul haclean | uncontracted |  |  |
| paraul iliseni | uncontracted |  |  |
| paraul intre pietre | uncontracted |  |  |
| paraul intunericului | uncontracted |  |  |
| paraul iodul | uncontracted |  |  |
| paraul izarel | uncontracted |  |  |
| paraul jirca | uncontracted |  |  |
| paraul jungul niculesti | uncontracted |  |  |
| paraul lui burus | uncontracted |  |  |
| paraul lui nicolae | uncontracted |  |  |
| paraul lui pavel | uncontracted |  |  |
| paraul lung | present | AJVPS CARAȘ-SEVERIN | audit_match:exact |
| paraul magura intunecoasa | uncontracted |  |  |
| paraul marsinetul de jos | present | FLY FISHING CLUB SIBIU |  |
| paraul mesteacanul | uncontracted |  |  |
| paraul mesterhazul | uncontracted |  |  |
| paraul neagra calin | uncontracted |  |  |
| paraul neamtului | uncontracted |  |  |
| paraul paltinu | present | A.PENEȘ CURCANUL | bbox_fix:lake:Lacul Paltinu |
| paraul pescoasa mare | uncontracted |  |  |
| paraul pestelui | uncontracted |  |  |
| paraul popii | uncontracted |  |  |
| paraul puturos | uncontracted |  |  |
| paraul rau | uncontracted |  |  |
| paraul repede | uncontracted |  |  |
| paraul salard | present | Direcția Silvică Mureș | romsilva_map:exact |
| paraul sarmasului | uncontracted |  |  |
| paraul saros | uncontracted |  |  |
| paraul strungii | uncontracted |  |  |
| paraul tarnita | present | D.S. Cluj |  |
| paraul tiba mare | uncontracted |  |  |
| paraul tiba mica | uncontracted |  |  |
| paraul todoran | uncontracted |  |  |
| paraul tomii | uncontracted |  |  |
| paraul trecerea | uncontracted |  |  |
| paraul zespezel | uncontracted |  |  |
| pietrosul | uncontracted |  |  |
| pr bufantau | uncontracted |  |  |
| pr cracul din mijloc | uncontracted |  |  |
| pr cracul stang | uncontracted |  |  |
| pr gudea | uncontracted |  |  |
| pr gudea mare | uncontracted |  |  |
| pr gudea mica | uncontracted |  |  |
| pr iadul | uncontracted |  |  |
| pr magura de jos | uncontracted |  |  |
| pr magura de sus | uncontracted |  |  |
| pr magura din mijloc | uncontracted |  |  |
| pr padina | uncontracted |  |  |
| pr paltinul | uncontracted |  |  |
| pr piatra de jos | uncontracted |  |  |
| pr popa | uncontracted |  |  |
| pr schwartz | uncontracted |  |  |
| rastolita | present | AJVPS MUREȘ |  |
| saracinul mare | uncontracted |  |  |
| sarmas | uncontracted |  |  |
| scurtu | uncontracted |  |  |
| secu | present | AP BANATUL | bbox_fix:lake:Lacul Secu |
| secul | uncontracted |  |  |
| sihla | uncontracted |  |  |
| silhoasa | uncontracted |  |  |
| stana | uncontracted |  |  |
| stega | uncontracted |  |  |
| tarnita | present | D.S. Cluj |  |
| tesna | uncontracted |  |  |
| tesnita | uncontracted |  |  |
| tihul | uncontracted |  |  |
| tihul ilvei | uncontracted |  |  |
| tihulet | uncontracted |  |  |
| tomoroga | uncontracted |  |  |
| ungurasul | uncontracted |  |  |
| ungurasul mare | uncontracted |  |  |
| ungurasul mic | uncontracted |  |  |
| ursul mare | uncontracted |  |  |
| ursul mica | uncontracted |  |  |
| valea fantanel | uncontracted |  |  |
| valea toplitei | present | Direcția Silvică Harghita | romsilva_map:exact |
| zebrac | present | Direcția Silvică Mureș | romsilva_map:exact |

### Celulă 46.9-47.4N, 25.5-26.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| armenilor | uncontracted |  |  |
| baicu | present | Direcția Silvică Maramureș | romsilva_map:exact |
| baisescu | uncontracted |  |  |
| balaj | uncontracted |  |  |
| balatau | uncontracted |  |  |
| barnaru | uncontracted |  |  |
| bistra | present | AJVPS MUREȘ |  |
| bistra mare | present | AJVPS MUREȘ |  |
| bistra mica | present | AJVPS MUREȘ |  |
| bistricioara | present | AJVPS VÂLCEA |  |
| bistrita | present | AJVPS NEAMȚ | anpa_map:bistrita-basin |
| boina | uncontracted |  |  |
| bolatau | uncontracted |  |  |
| borca | present | Direcția Silvică Neamț | romsilva_map:exact |
| bordeiului | uncontracted |  |  |
| borvizul | uncontracted |  |  |
| brateasa | uncontracted |  |  |
| breaza | uncontracted |  |  |
| buda | present | Direcția Silvică Argeș | romsilva_map:exact |
| budacu | uncontracted |  |  |
| capra | present | Direcția Silvică Argeș | romsilva_map:exact |
| capriorul | uncontracted |  |  |
| carja | uncontracted |  |  |
| cazatura | uncontracted |  |  |
| cerebuc | uncontracted |  |  |
| cibeni | uncontracted |  |  |
| cornul | uncontracted |  |  |
| coroiu | uncontracted |  |  |
| cracul paduretului | uncontracted |  |  |
| cristisor | uncontracted |  |  |
| crucea | uncontracted |  |  |
| dartu stream | uncontracted |  |  |
| dia cocoaia | uncontracted |  |  |
| dolita | uncontracted |  |  |
| fagul | uncontracted |  |  |
| fulop andras patak | uncontracted |  |  |
| furcituri | uncontracted |  |  |
| galu | uncontracted |  |  |
| garboaia | uncontracted |  |  |
| gemenea | uncontracted |  |  |
| grasul mare | uncontracted |  |  |
| grintiesul mare | uncontracted |  |  |
| haciogosul | uncontracted |  |  |
| haiducul | uncontracted |  |  |
| hasca | uncontracted |  |  |
| hollo patak | uncontracted |  |  |
| hotarul | uncontracted |  |  |
| iepurele | uncontracted |  |  |
| izvor balaj | uncontracted |  |  |
| izvoru alb | uncontracted |  |  |
| izvorul muntelui | uncontracted |  |  |
| jgheabu cu hotar | uncontracted |  |  |
| jgheabul lui voda | uncontracted |  |  |
| jgheabul mare | uncontracted |  |  |
| lutu rosu | uncontracted |  |  |
| mitropolitul | uncontracted |  |  |
| moldova | present | AVPS IAȘI |  |
| neagra | present | Direcția Silvică Suceava | romsilva_map:group-shares-course |
| neamt | uncontracted |  |  |
| neamtul cel mare | uncontracted |  |  |
| neamtul cel mic | uncontracted |  |  |
| negrileasa | uncontracted |  |  |
| negrisoara | uncontracted |  |  |
| nemtisorul | uncontracted |  |  |
| nican | uncontracted |  |  |
| nicanu | uncontracted |  |  |
| ortoita | uncontracted |  |  |
| p lui martin | uncontracted |  |  |
| p paduretul | uncontracted |  |  |
| padina stanei | uncontracted |  |  |
| paduretul | uncontracted |  |  |
| paltinul | uncontracted |  |  |
| paraul adanc | uncontracted |  |  |
| paraul alautului | uncontracted |  |  |
| paraul argelea | uncontracted |  |  |
| paraul argintaria | uncontracted |  |  |
| paraul arsitei | uncontracted |  |  |
| paraul bofului | uncontracted |  |  |
| paraul bradului | uncontracted |  |  |
| paraul branza | uncontracted |  |  |
| paraul caboaiei | uncontracted |  |  |
| paraul calugarului | uncontracted |  |  |
| paraul capra | present | Direcția Silvică Argeș | romsilva_map:exact |
| paraul capriorul | uncontracted |  |  |
| paraul capritei | uncontracted |  |  |
| paraul casei | uncontracted |  |  |
| paraul celarului | uncontracted |  |  |
| paraul cerbului | uncontracted |  |  |
| paraul cineilor | uncontracted |  |  |
| paraul cojocarului | uncontracted |  |  |
| paraul comorii | uncontracted |  |  |
| paraul cotargasi | uncontracted |  |  |
| paraul cu peste | uncontracted |  |  |
| paraul curmaturii | uncontracted |  |  |
| paraul curmaturii adanci | uncontracted |  |  |
| paraul diac | uncontracted |  |  |
| paraul dintre bulbuci | uncontracted |  |  |
| paraul doliei | uncontracted |  |  |
| paraul dolita | uncontracted |  |  |
| paraul druganului | uncontracted |  |  |
| paraul fantanii | uncontracted |  |  |
| paraul fierului | uncontracted |  |  |
| paraul fulgerisului | uncontracted |  |  |
| paraul galben | uncontracted |  |  |
| paraul genunilor | uncontracted |  |  |
| paraul grasul | uncontracted |  |  |
| paraul hancker | uncontracted |  |  |
| paraul hascutii | uncontracted |  |  |
| paraul ianitoaii | uncontracted |  |  |
| paraul larg | uncontracted |  |  |
| paraul leurda | uncontracted |  |  |
| paraul lui ana | uncontracted |  |  |
| paraul lui grigore | uncontracted |  |  |
| paraul lui martin | uncontracted |  |  |
| paraul lui pascu | uncontracted |  |  |
| paraul lui petrisor | uncontracted |  |  |
| paraul lui zgarie branza | uncontracted |  |  |
| paraul lung | present | AJVPS CARAȘ-SEVERIN | audit_match:exact |
| paraul maicilor | uncontracted |  |  |
| paraul malisorului | uncontracted |  |  |
| paraul malnas | uncontracted |  |  |
| paraul mandra | uncontracted |  |  |
| paraul mesteacanul | uncontracted |  |  |
| paraul mielul | uncontracted |  |  |
| paraul nadas | present | AJPS Cluj |  |
| paraul negrului | uncontracted |  |  |
| paraul paltinisului | uncontracted |  |  |
| paraul paltinului | uncontracted |  |  |
| paraul piatra lupilor | uncontracted |  |  |
| paraul pietroasa | uncontracted |  |  |
| paraul rascoalelor | uncontracted |  |  |
| paraul scorusul | uncontracted |  |  |
| paraul sec | uncontracted |  |  |
| paraul soldanului | uncontracted |  |  |
| paraul stanii | uncontracted |  |  |
| paraul tarsoasei | uncontracted |  |  |
| paraul tarsos | uncontracted |  |  |
| paraul tiganului | uncontracted |  |  |
| paraul tinova | uncontracted |  |  |
| paraul tracilor | uncontracted |  |  |
| paraul ungurenilor | uncontracted |  |  |
| paraul ungurului de jos | present | FLY FISHING CLUB SIBIU |  |
| paraul ungurului de sus | present | FLY FISHING CLUB SIBIU |  |
| paraul vadutii | uncontracted |  |  |
| paraul vinisorul | uncontracted |  |  |
| paraul vinului | uncontracted |  |  |
| parvu | uncontracted |  |  |
| piatra lupului | uncontracted |  |  |
| pintic | uncontracted |  |  |
| prislopul | uncontracted |  |  |
| putna | present | Direcția Silvică Suceava | romsilva_map:exact |
| rasca | uncontracted |  |  |
| raul bolatau | uncontracted |  |  |
| rezu mare | uncontracted |  |  |
| rezul mare | uncontracted |  |  |
| roseni | uncontracted |  |  |
| rupturi | uncontracted |  |  |
| ruseni | uncontracted |  |  |
| sabasita | uncontracted |  |  |
| sagariei | uncontracted |  |  |
| schitu | uncontracted |  |  |
| slatina | uncontracted |  |  |
| slatiorul | uncontracted |  |  |
| smida lupului | uncontracted |  |  |
| stana | uncontracted |  |  |
| stana manastirii | uncontracted |  |  |
| stanei | uncontracted |  |  |
| suha | uncontracted |  |  |
| suha mare | uncontracted |  |  |
| suha mica | uncontracted |  |  |
| tiflic | uncontracted |  |  |
| tiganca | uncontracted |  |  |
| voaides | uncontracted |  |  |
| vremelnita | uncontracted |  |  |

### Celulă 46.9-47.4N, 26.0-26.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| afinisul | uncontracted |  |  |
| almaselul | uncontracted |  |  |
| almasul | uncontracted |  |  |
| alunisul | uncontracted |  |  |
| arinisul | uncontracted |  |  |
| arsita lunga | uncontracted |  |  |
| audia | uncontracted |  |  |
| bahna | present | AJVPS BOTOȘANI |  |
| balmes | uncontracted |  |  |
| barbunti | uncontracted |  |  |
| bicaz | present | AJVPS NEAMȚ | bbox_fix:lake:Lacul Izvorul Muntelui |
| bistrita | present | AJVPS NEAMȚ | anpa_map:bistrita-basin |
| blaga | uncontracted |  |  |
| bolatau | uncontracted |  |  |
| bolovanul | uncontracted |  |  |
| borzogheanu | uncontracted |  |  |
| botolia | uncontracted |  |  |
| bouarii | uncontracted |  |  |
| bouletul mare | uncontracted |  |  |
| bouletul mic | uncontracted |  |  |
| bran | uncontracted |  |  |
| cacova | uncontracted |  |  |
| caldarea | uncontracted |  |  |
| calugarita | uncontracted |  |  |
| calugaritei | uncontracted |  |  |
| calugarul | uncontracted |  |  |
| cantonul | uncontracted |  |  |
| carbunele | uncontracted |  |  |
| carpenul | uncontracted |  |  |
| cerbul | uncontracted |  |  |
| cerbusorul | uncontracted |  |  |
| chifanului | uncontracted |  |  |
| chiruta | uncontracted |  |  |
| chita mare | uncontracted |  |  |
| cioronisul | uncontracted |  |  |
| ciresul | uncontracted |  |  |
| ciuculoaia | uncontracted |  |  |
| coacazul | uncontracted |  |  |
| coroiu | uncontracted |  |  |
| coroiu stream | uncontracted |  |  |
| cotnarel | uncontracted |  |  |
| cracau | uncontracted |  |  |
| cracaul alb | uncontracted |  |  |
| cracaul negru | uncontracted |  |  |
| crucea | uncontracted |  |  |
| cucurezul | uncontracted |  |  |
| cuejdel | uncontracted |  |  |
| cuejdiu | uncontracted |  |  |
| dartu stream | uncontracted |  |  |
| dobreanu | uncontracted |  |  |
| dobrenasu | uncontracted |  |  |
| drahuta | uncontracted |  |  |
| drajinelor | uncontracted |  |  |
| dranguleasa | uncontracted |  |  |
| dranitei | uncontracted |  |  |
| eufrosin | uncontracted |  |  |
| fagetul | uncontracted |  |  |
| fantana | present | Direcția Silvică Maramureș | romsilva_map:exact |
| fartagi | uncontracted |  |  |
| frasinelul | uncontracted |  |  |
| frasinul | uncontracted |  |  |
| furcituri | uncontracted |  |  |
| ghermanu mic | uncontracted |  |  |
| girda | uncontracted |  |  |
| gloduri | uncontracted |  |  |
| gradina | uncontracted |  |  |
| grohotisul | uncontracted |  |  |
| halgeanu | uncontracted |  |  |
| hangu | uncontracted |  |  |
| huciasu | uncontracted |  |  |
| huma | uncontracted |  |  |
| humaria | uncontracted |  |  |
| icoana | uncontracted |  |  |
| iftimia | uncontracted |  |  |
| imasului | uncontracted |  |  |
| inginerul | uncontracted |  |  |
| izvoru alb | uncontracted |  |  |
| izvoru muntelui | uncontracted |  |  |
| izvorul muntelui | uncontracted |  |  |
| jgheabu mare | uncontracted |  |  |
| laptaria | uncontracted |  |  |
| lazar baroi | uncontracted |  |  |
| macesul | uncontracted |  |  |
| maguricea | uncontracted |  |  |
| manzatul mare | uncontracted |  |  |
| mesteacanu | present | AVPS MIERCUREA-CIUC | audit_match:char0.95 |
| mihaietul sec | uncontracted |  |  |
| moldova | present | AVPS IAȘI |  |
| molidul | uncontracted |  |  |
| neamt | uncontracted |  |  |
| oantu | uncontracted |  |  |
| odailor | uncontracted |  |  |
| opresti | uncontracted |  |  |
| p bursucariei | uncontracted |  |  |
| paltinisul | uncontracted |  |  |
| pangaracior | uncontracted |  |  |
| paraul adanc | uncontracted |  |  |
| paraul alb | present | AJVPS CARAȘ-SEVERIN | multiway_chain |
| paraul argelea | uncontracted |  |  |
| paraul arinului | uncontracted |  |  |
| paraul balaurului | uncontracted |  |  |
| paraul boistea | uncontracted |  |  |
| paraul bolatau | uncontracted |  |  |
| paraul borzogheanu | uncontracted |  |  |
| paraul caramidariei | uncontracted |  |  |
| paraul carbunoasa | uncontracted |  |  |
| paraul catargelului | uncontracted |  |  |
| paraul chitele | uncontracted |  |  |
| paraul chitelelor | uncontracted |  |  |
| paraul crasnita | uncontracted |  |  |
| paraul de la cruce | uncontracted |  |  |
| paraul doliei | uncontracted |  |  |
| paraul dolita | uncontracted |  |  |
| paraul farsituri | uncontracted |  |  |
| paraul fundurilor | uncontracted |  |  |
| paraul horaita | uncontracted |  |  |
| paraul in imas | uncontracted |  |  |
| paraul la groapa cu fragi | uncontracted |  |  |
| paraul lui gabura | uncontracted |  |  |
| paraul lui gheorghita | uncontracted |  |  |
| paraul lui stamate | uncontracted |  |  |
| paraul lung | present | AJVPS CARAȘ-SEVERIN | audit_match:exact |
| paraul moisa | uncontracted |  |  |
| paraul parloagelor | uncontracted |  |  |
| paraul pietros | uncontracted |  |  |
| paraul platonesti | uncontracted |  |  |
| paraul plotanasul | uncontracted |  |  |
| paraul popii | uncontracted |  |  |
| paraul porcului | uncontracted |  |  |
| paraul putred | uncontracted |  |  |
| paraul puturos | uncontracted |  |  |
| paraul rachitelor | uncontracted |  |  |
| paraul radacinesti | uncontracted |  |  |
| paraul rascuta | uncontracted |  |  |
| paraul recea | uncontracted |  |  |
| paraul ruginei | uncontracted |  |  |
| paraul sarbului | uncontracted |  |  |
| paraul sarpelui | uncontracted |  |  |
| paraul scaioasa | uncontracted |  |  |
| paraul smeului | uncontracted |  |  |
| paraul sorbului | uncontracted |  |  |
| paraul stegei | uncontracted |  |  |
| paraul tociloasa | uncontracted |  |  |
| paraul vaca babei | uncontracted |  |  |
| paraul vacariei | uncontracted |  |  |
| paraul viisorei | uncontracted |  |  |
| parul | uncontracted |  |  |
| pascau | uncontracted |  |  |
| pietraria | uncontracted |  |  |
| plostina | uncontracted |  |  |
| pochivnica | uncontracted |  |  |
| poitele | uncontracted |  |  |
| popa | uncontracted |  |  |
| potoci | uncontracted |  |  |
| prisaci | uncontracted |  |  |
| prislopasul | uncontracted |  |  |
| procov | uncontracted |  |  |
| purcaroaia | uncontracted |  |  |
| rasca | uncontracted |  |  |
| runcu | present | AJVPS MARAMUREȘ |  |
| runcul | uncontracted |  |  |
| runcului | uncontracted |  |  |
| ruptura | uncontracted |  |  |
| salantrucul | uncontracted |  |  |
| sarata | present | AJVPS BOTOȘANI |  |
| sasca | uncontracted |  |  |
| sascuta | uncontracted |  |  |
| sasul | uncontracted |  |  |
| sbrancea | uncontracted |  |  |
| seaca | uncontracted |  |  |
| secatura | uncontracted |  |  |
| secatura mare | uncontracted |  |  |
| secatura mica | uncontracted |  |  |
| secaturel | uncontracted |  |  |
| sihastrul | uncontracted |  |  |
| silvestru | uncontracted |  |  |
| simon | uncontracted |  |  |
| snida | uncontracted |  |  |
| straja | uncontracted |  |  |
| strigoesul | uncontracted |  |  |
| strugaria | uncontracted |  |  |
| suha mare | uncontracted |  |  |
| tarnicioarei | uncontracted |  |  |
| tiganca | uncontracted |  |  |
| tisa | present | AJVPS MARAMUREȘ |  |
| tisei | uncontracted |  |  |
| topolita | uncontracted |  |  |
| trapezia | uncontracted |  |  |
| tulva | uncontracted |  |  |
| ulmul | uncontracted |  |  |
| ulmului | uncontracted |  |  |
| ursoaia | uncontracted |  |  |
| valea mare | present | AVPS MIERCUREA-CIUC |  |
| valea mica | uncontracted |  |  |
| valea mormantului | uncontracted |  |  |
| valea rea | uncontracted |  |  |
| zaplazul | uncontracted |  |  |
| zimbrul | uncontracted |  |  |

### Celulă 46.9-47.4N, 26.5-27.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bahlui | uncontracted |  |  |
| bahluiet | uncontracted |  |  |
| bahna | present | AJVPS BOTOȘANI |  |
| boca | uncontracted |  |  |
| cracau | uncontracted |  |  |
| dacita | uncontracted |  |  |
| magura | uncontracted |  |  |
| moldova | present | AVPS IAȘI |  |
| neamt | uncontracted |  |  |
| paraul cilnes | uncontracted |  |  |
| paraul valeni | uncontracted |  |  |
| probota | uncontracted |  |  |
| raul badilita | uncontracted |  |  |
| raul iermolea | uncontracted |  |  |
| raul zmeul | uncontracted |  |  |
| siret | present | Centrul Regional de Ecologie Bacău |  |
| zmeul | uncontracted |  |  |

### Celulă 46.9-47.4N, 27.0-27.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bahlui | uncontracted |  |  |
| bahluiet | uncontracted |  |  |
| bogonos | uncontracted |  |  |
| cacaina | uncontracted |  |  |
| calina | uncontracted |  |  |
| ciurdea | uncontracted |  |  |
| cornet | uncontracted |  |  |
| doroscu | uncontracted |  |  |
| duraceasca | uncontracted |  |  |
| ezareni | uncontracted |  |  |
| garboveta | uncontracted |  |  |
| grind | uncontracted |  |  |
| gurguiata | uncontracted |  |  |
| horlesti | uncontracted |  |  |
| ileana | uncontracted |  |  |
| jijia | present | AJVPS BOTOȘANI |  |
| lupu | uncontracted |  |  |
| magura | uncontracted |  |  |
| miletin | present | AJVPS BOTOȘANI |  |
| p voinesti | uncontracted |  |  |
| pais | uncontracted |  |  |
| pietrosu | uncontracted |  |  |
| piriu mare | uncontracted |  |  |
| prisecii | uncontracted |  |  |
| putina | uncontracted |  |  |
| raul amara | uncontracted |  |  |
| raul stavnic | uncontracted |  |  |
| rediu | uncontracted |  |  |
| rosior | uncontracted |  |  |
| sacovat | uncontracted |  |  |
| sauzeni | uncontracted |  |  |
| sbont | uncontracted |  |  |
| stavnic | uncontracted |  |  |
| stavnicel | uncontracted |  |  |
| totoesti | uncontracted |  |  |
| ursita | uncontracted |  |  |
| valea locei | uncontracted |  |  |
| valea olarilor | uncontracted |  |  |
| valea prisacii | uncontracted |  |  |
| velna | uncontracted |  |  |
| voinesti | uncontracted |  |  |
| vulpoiu | uncontracted |  |  |

### Celulă 46.9-47.4N, 27.5-28.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bahlui | uncontracted |  |  |
| bohotin | uncontracted |  |  |
| bratuleanca | uncontracted |  |  |
| bucium | uncontracted |  |  |
| cacaina | uncontracted |  |  |
| carbunaria | uncontracted |  |  |
| chirita | uncontracted |  |  |
| ciric | uncontracted |  |  |
| cocoara | uncontracted |  |  |
| cornet | uncontracted |  |  |
| coropceni | uncontracted |  |  |
| covasna | present | AJVPS COVASNA |  |
| crasna | present | AJVPS VASLUI | anpa_map:sweep:crasna |
| delia | uncontracted |  |  |
| dobrovat | uncontracted |  |  |
| ezareni | uncontracted |  |  |
| floritoaia | uncontracted |  |  |
| frumoasa | present | AVPS MIERCUREA-CIUC |  |
| garla mare | present | AVPS MIERCUREA-CIUC |  |
| girla mare | uncontracted |  |  |
| girla mica | uncontracted |  |  |
| jijia | present | AJVPS BOTOȘANI |  |
| jijia veche | present | AJVPS BOTOȘANI |  |
| lupu | uncontracted |  |  |
| nicolina | uncontracted |  |  |
| orzeni | uncontracted |  |  |
| osoi | uncontracted |  |  |
| paraul ciortesti | uncontracted |  |  |
| paraul mosna | uncontracted |  |  |
| paraul nicolina | uncontracted |  |  |
| paraul recea | uncontracted |  |  |
| paraul varariei | uncontracted |  |  |
| pietrarie | uncontracted |  |  |
| pietrosu | uncontracted |  |  |
| poiana lunga | uncontracted |  |  |
| prut | present | AVPS IAȘI |  |
| prut / прут | uncontracted |  |  |
| raul ciric | uncontracted |  |  |
| raul coropceni | uncontracted |  |  |
| raul mosna | uncontracted |  |  |
| rediu | uncontracted |  |  |
| soltoaia | uncontracted |  |  |
| tamarca | uncontracted |  |  |
| valea locei | uncontracted |  |  |
| valea olarilor | uncontracted |  |  |
| valea sapte oameni | uncontracted |  |  |
| valea satului | uncontracted |  |  |
| vamasoaia | uncontracted |  |  |
| vaslui | uncontracted |  |  |
| vasluiet | present | AJVPS VASLUI | audit_match:exact |
| vladnic | uncontracted |  |  |

### Celulă 46.9-47.4N, 28.0-28.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bahu | uncontracted |  |  |
| bic | uncontracted |  |  |
| bohotin | uncontracted |  |  |
| bolduresti | uncontracted |  |  |
| botna | uncontracted |  |  |
| bratuleanca | uncontracted |  |  |
| bucovat | uncontracted |  |  |
| bujor | uncontracted |  |  |
| cogalnic | uncontracted |  |  |
| corbu | uncontracted |  |  |
| cula | uncontracted |  |  |
| hultura | uncontracted |  |  |
| ichel | uncontracted |  |  |
| isnovat | uncontracted |  |  |
| jijia | present | AJVPS BOTOȘANI |  |
| jijia veche | present | AJVPS BOTOȘANI |  |
| lapusna | uncontracted |  |  |
| lapusnita | uncontracted |  |  |
| narnova | uncontracted |  |  |
| prut | present | AVPS IAȘI |  |
| prut / прут | uncontracted |  |  |
| raul cogalnic | uncontracted |  |  |
| raul mosnisoara | uncontracted |  |  |
| recateu | uncontracted |  |  |
| strada livezilor | uncontracted |  |  |

### Celulă 46.9-47.4N, 28.5-29.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bahna | present | AJVPS BOTOȘANI |  |
| baltata | uncontracted |  |  |
| bardar | uncontracted |  |  |
| bic | uncontracted |  |  |
| botna | uncontracted |  |  |
| ciocana | uncontracted |  |  |
| cogalnic | uncontracted |  |  |
| cula | uncontracted |  |  |
| draghinici | uncontracted |  |  |
| durlesti | uncontracted |  |  |
| ghidighici | uncontracted |  |  |
| golbaciha | uncontracted |  |  |
| hulboaca | uncontracted |  |  |
| hultura | uncontracted |  |  |
| ichel | uncontracted |  |  |
| isnovat | uncontracted |  |  |
| ivanos | uncontracted |  |  |
| malina mica | uncontracted |  |  |
| motca | uncontracted |  |  |
| rapa cazacului | uncontracted |  |  |
| raul cogalnic | uncontracted |  |  |
| rauletul hulbocica | uncontracted |  |  |
| raut | uncontracted |  |  |
| schinoasa | uncontracted |  |  |
| sfanta vineri | uncontracted |  |  |
| tiganca | uncontracted |  |  |
| tohatin | uncontracted |  |  |
| valea bostancea | uncontracted |  |  |
| valea cojusnei | uncontracted |  |  |
| valea merenilor | uncontracted |  |  |
| valea schinoasa | uncontracted |  |  |
| valea siretilor | uncontracted |  |  |
| valea trandafirilor | uncontracted |  |  |
| valea trusenilor | uncontracted |  |  |
| vatici | uncontracted |  |  |
| zaicana | uncontracted |  |  |
| дністер / nistru | uncontracted |  |  |

### Celulă 46.9-47.4N, 29.0-29.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| baltata | uncontracted |  |  |
| bic | uncontracted |  |  |
| iagorlac / ягорлик | uncontracted |  |  |
| iagorlicul uscat | uncontracted |  |  |
| ichel | uncontracted |  |  |
| maximovca | uncontracted |  |  |
| nistru | uncontracted |  |  |
| nistru / днестр | uncontracted |  |  |
| nistru днестр | uncontracted |  |  |
| raut | uncontracted |  |  |
| recea | uncontracted |  |  |
| tamaslic | uncontracted |  |  |
| tamaslic / тамашлик | uncontracted |  |  |
| tamaslic / тамашлык | uncontracted |  |  |
| valea merenilor | uncontracted |  |  |
| valea sagaidacului | uncontracted |  |  |
| valea schinoasa | uncontracted |  |  |
| вовча | uncontracted |  |  |
| дністер / nistru | uncontracted |  |  |
| сухии ягорлик | uncontracted |  |  |
| сухои ягорлык | uncontracted |  |  |
| тамашлик | uncontracted |  |  |
| тамашлык | uncontracted |  |  |
| черная | uncontracted |  |  |
| ягорлык / iagorlac | uncontracted |  |  |
| ягорлык iagorlac | uncontracted |  |  |

### Celulă 46.9-47.4N, 29.5-30.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| балка комарова | uncontracted |  |  |
| баркуца | uncontracted |  |  |
| бугаі | uncontracted |  |  |
| велика сошка | uncontracted |  |  |
| великии гладиш | uncontracted |  |  |
| великии дракул | uncontracted |  |  |
| двуріцькии | uncontracted |  |  |
| десинора | uncontracted |  |  |
| дністер / nistru | uncontracted |  |  |
| зеленогаичик | uncontracted |  |  |
| каламатин | uncontracted |  |  |
| канаи | uncontracted |  |  |
| комаровская | uncontracted |  |  |
| комаровська | uncontracted |  |  |
| кучурган | uncontracted |  |  |
| кучурган / cuciurgan | uncontracted |  |  |
| мала сошка | uncontracted |  |  |
| малии дракул | uncontracted |  |  |
| малии канаи | uncontracted |  |  |
| мусієнкова | uncontracted |  |  |
| платонівська | uncontracted |  |  |
| стариця | uncontracted |  |  |
| черная | uncontracted |  |  |
| чернечии яр | uncontracted |  |  |

### Celulă 47.4-47.9N, 20.0-20.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| danube | uncontracted |  |  |
| eger csatorna | uncontracted |  |  |
| eger patak | uncontracted |  |  |
| gorbe er | uncontracted |  |  |
| hanyi csatorna | uncontracted |  |  |
| kalapos csatorna | uncontracted |  |  |
| kanya patak | uncontracted |  |  |
| kigyos patak | uncontracted |  |  |
| lasko | uncontracted |  |  |
| maklanyi patak | uncontracted |  |  |
| novaj patak | uncontracted |  |  |
| ostoros patak | uncontracted |  |  |
| rima | uncontracted |  |  |
| szolati patak | uncontracted |  |  |
| tarna | uncontracted |  |  |
| tisza | uncontracted |  |  |
| zagyva | uncontracted |  |  |

### Celulă 47.4-47.9N, 20.5-21.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| agyagos csatorna | uncontracted |  |  |
| arkus focsatorna | uncontracted |  |  |
| csincse ovcsatorna | uncontracted |  |  |
| csincse patak | uncontracted |  |  |
| eger csatorna | uncontracted |  |  |
| gyilkos er | uncontracted |  |  |
| hejo | uncontracted |  |  |
| hor patak | uncontracted |  |  |
| kacsi patak | uncontracted |  |  |
| kalapos csatorna | uncontracted |  |  |
| kanya patak | uncontracted |  |  |
| kis csincse | uncontracted |  |  |
| lasko | uncontracted |  |  |
| lator patak | uncontracted |  |  |
| nad er | uncontracted |  |  |
| novaj patak | uncontracted |  |  |
| orosz er | uncontracted |  |  |
| ostoros patak | uncontracted |  |  |
| rima | uncontracted |  |  |
| salamonta er | uncontracted |  |  |
| salyi patak | uncontracted |  |  |
| szaraz to er | uncontracted |  |  |
| tardi patak | uncontracted |  |  |
| tisza | uncontracted |  |  |
| tiszavalki focsatorna | uncontracted |  |  |
| vekony er | uncontracted |  |  |

### Celulă 47.4-47.9N, 21.0-21.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| brasso er | uncontracted |  |  |
| hejo | uncontracted |  |  |
| hortobagy | uncontracted |  |  |
| kadarcs karacsonyfoki focsatorna | uncontracted |  |  |
| pece er | uncontracted |  |  |
| pere er | uncontracted |  |  |
| tisza | uncontracted |  |  |

### Celulă 47.4-47.9N, 21.5-22.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| acsadi er | uncontracted |  |  |
| asszonylaposi kiagazas | uncontracted |  |  |
| bagameri er | uncontracted |  |  |
| balkanyi folyas | uncontracted |  |  |
| bodzas | uncontracted |  |  |
| brasso er | uncontracted |  |  |
| csaszar olahreti oldalag | uncontracted |  |  |
| csaszar olahreti szivargo | uncontracted |  |  |
| cseres csatorna | uncontracted |  |  |
| erdoslyuki er | uncontracted |  |  |
| guti er | uncontracted |  |  |
| haszontoi csatorna | uncontracted |  |  |
| kallai fofolyas | uncontracted |  |  |
| kati er | uncontracted |  |  |
| kis palyi er | uncontracted |  |  |
| kis vamos er | uncontracted |  |  |
| kisszek hosszuhati szivargo | uncontracted |  |  |
| koc er | uncontracted |  |  |
| kondoros | uncontracted |  |  |
| kondorosi er | uncontracted |  |  |
| konyari kallo | uncontracted |  |  |
| letai er | uncontracted |  |  |
| malomgati er | uncontracted |  |  |
| martinkai er | uncontracted |  |  |
| mely er | uncontracted |  |  |
| mocsankerti szivargo | uncontracted |  |  |
| monostori er | uncontracted |  |  |
| nadastoi szivargo | uncontracted |  |  |
| nagyreti csatorna | uncontracted |  |  |
| nagyreti szivargo | uncontracted |  |  |
| nyirjes toi folyas | uncontracted |  |  |
| olahreti csatorna | uncontracted |  |  |
| palyi er | uncontracted |  |  |
| percsi er | uncontracted |  |  |
| simai fofolyas | uncontracted |  |  |
| szarcsas er | uncontracted |  |  |
| szata er | uncontracted |  |  |
| toco csatorna | uncontracted |  |  |
| toco patak | uncontracted |  |  |
| totapai szivargo | uncontracted |  |  |
| vamos er | uncontracted |  |  |
| viii /3 3 mellekag | uncontracted |  |  |
| villongo er | uncontracted |  |  |
| zugo er | uncontracted |  |  |

### Celulă 47.4-47.9N, 22.0-22.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bagameri er | uncontracted |  |  |
| bodvaj | uncontracted |  |  |
| crasna | present | AJVPS SĂLAJ | anpa_map:sweep |
| csanalosi folyas | uncontracted |  |  |
| ganos | uncontracted |  |  |
| ier | present | AJVPS TIMIȘ | audit_match:exact |
| jozseftanyai csatorna | uncontracted |  |  |
| kallai fofolyas | uncontracted |  |  |
| karolyi folyas | uncontracted |  |  |
| konyari kallo | uncontracted |  |  |
| kraszna | uncontracted |  |  |
| nagy vajas | uncontracted |  |  |
| szenasi vizfolyas | uncontracted |  |  |
| vasvari fofolyaas | uncontracted |  |  |
| vasvari fofolyas | uncontracted |  |  |

### Celulă 47.4-47.9N, 22.5-23.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| canalul homorod | present | AJPS Brașov |  |
| crasna | present | AJVPS SĂLAJ | anpa_map:sweep |
| hodisa | uncontracted |  |  |
| homorodul vechi | uncontracted |  |  |
| ier | present | AJVPS TIMIȘ | audit_match:exact |
| keleti ovcsatorna | uncontracted |  |  |
| kraszna | uncontracted |  |  |
| sar eger csatorna | uncontracted |  |  |
| somes | present | AJVPS CLUJ |  |
| szamos | uncontracted |  |  |
| valea maria | uncontracted |  |  |

### Celulă 47.4-47.9N, 23.0-23.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| baita | uncontracted |  |  |
| csiga patak | uncontracted |  |  |
| hodisa | uncontracted |  |  |
| lapus | present | AJVPS MARAMUREȘ |  |
| rakta er | uncontracted |  |  |
| sarviz | uncontracted |  |  |
| sasar | present | AJVPS MARAMUREȘ |  |
| seinel | uncontracted |  |  |
| somes | present | AJVPS CLUJ |  |
| sziner patak | uncontracted |  |  |
| talna | present | AJVPS SATU MARE |  |
| talna mare | present | AJVPS SATU MARE |  |
| tur | present | AJVPS SATU MARE | audit_match:exact |
| valea maria | uncontracted |  |  |
| valea rea | uncontracted |  |  |

### Celulă 47.4-47.9N, 23.5-24.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| ariniesi | uncontracted |  |  |
| baita | uncontracted |  |  |
| bloaja | present | AJVPS MARAMUREȘ |  |
| breboaia | uncontracted |  |  |
| cavnic | present | Direcția Silvică Maramureș | romsilva_map:exact |
| chechisel | uncontracted |  |  |
| cioncas | uncontracted |  |  |
| cornesita | uncontracted |  |  |
| cosau | present | AJVPS MARAMUREȘ |  |
| criva | uncontracted |  |  |
| darasca | uncontracted |  |  |
| firiza | present | Direcția Silvica Maramureș | bbox_fix:lake:Baraj Firiza |
| hopsia | uncontracted |  |  |
| iza | present | AJVPS MARAMUREȘ | audit_match:exact |
| izvorul alb | present | AJVPS CARAȘ-SEVERIN | multiway_chain |
| izvorul cu scari | uncontracted |  |  |
| izvorul negru | present | AJVPS COVASNA | audit_match:prefix |
| lapus | present | AJVPS MARAMUREȘ |  |
| mara | present | AJVPS MARAMUREȘ |  |
| oanta | uncontracted |  |  |
| paraul morii | uncontracted |  |  |
| paraul sfantul ioan | uncontracted |  |  |
| poiana | present | AJVPS BIHOR |  |
| raul porcului | uncontracted |  |  |
| rausor | present | Direcția Silvică Argeș | romsilva_map:exact |
| ronisoara | uncontracted |  |  |
| runcu | present | AJVPS MARAMUREȘ |  |
| sapanta | uncontracted |  |  |
| sasar | present | AJVPS MARAMUREȘ |  |
| sava | uncontracted |  |  |
| sigau | uncontracted |  |  |
| stedia | uncontracted |  |  |
| suciu | present | AJVPS MARAMUREȘ |  |
| sugau | uncontracted |  |  |
| talna mare | present | AJVPS SATU MARE |  |
| tulburea | uncontracted |  |  |
| tur | present | AJVPS SATU MARE | audit_match:exact |
| usturoiu | uncontracted |  |  |
| valea blonda | uncontracted |  |  |
| valea brazilor | uncontracted |  |  |
| valea caselor | present | AJVPS ALBA |  |
| valea cheii | uncontracted |  |  |
| valea cu arini | uncontracted |  |  |
| valea dragusei | uncontracted |  |  |
| valea dreapta | uncontracted |  |  |
| valea glodului | uncontracted |  |  |
| valea lazului | uncontracted |  |  |
| valea lunga | uncontracted |  |  |
| valea mare | present | Direcția Silvică Alba | romsilva_map:group-shares-course |
| valea merchiului | uncontracted |  |  |
| valea pietrelor | uncontracted |  |  |
| valea podului | uncontracted |  |  |
| valea popii | uncontracted |  |  |
| valea prindelului | uncontracted |  |  |
| valea rachitei | uncontracted |  |  |
| valea rea | uncontracted |  |  |
| valea rosie | uncontracted |  |  |
| valea seaca | uncontracted |  |  |
| valea sunatoarelor | uncontracted |  |  |
| valea talharului | uncontracted |  |  |
| valea vicleanul mare | uncontracted |  |  |
| valea vidrisca | uncontracted |  |  |
| vicleanu mare | uncontracted |  |  |
| vidra | present | Direcția Silvică Vâlcea | bbox_fix:lake:Lacul Vidra |
| vlasinescu | uncontracted |  |  |
| zavoaie | uncontracted |  |  |

### Celulă 47.4-47.9N, 24.0-24.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bardiu | uncontracted |  |  |
| bichigiu | uncontracted |  |  |
| bistra | present | AJVPS MUREȘ |  |
| bocicoel | uncontracted |  |  |
| cornatea | uncontracted |  |  |
| cvasnita | uncontracted |  |  |
| draguiasa | uncontracted |  |  |
| drahmirov | uncontracted |  |  |
| fiad | uncontracted |  |  |
| fiadtel | uncontracted |  |  |
| frumusaua | uncontracted |  |  |
| frumusica | uncontracted |  |  |
| gaureni | uncontracted |  |  |
| gersa | present | AJVPS BISTRIŢA NĂSĂUD |  |
| hodea | uncontracted |  |  |
| ialinc | uncontracted |  |  |
| ieud | present | Direcția Silvică Maramureș | romsilva_map:exact |
| ilisua | present | Direcția Silvică Bistrița-Năsăud | romsilva_map:exact |
| ivancic | uncontracted |  |  |
| iza | present | AJVPS MARAMUREȘ | audit_match:exact |
| izvorul baicului | uncontracted |  |  |
| lapus | present | AJVPS MARAMUREȘ |  |
| lespedea | uncontracted |  |  |
| leurda | uncontracted |  |  |
| lunca | uncontracted |  |  |
| marza | uncontracted |  |  |
| mesteacan | present | ANPA - Ape Necontractate | bbox_fix:lake:Mesteacănul |
| miclusa | uncontracted |  |  |
| misica | uncontracted |  |  |
| paraul repede | uncontracted |  |  |
| paraul soinici | uncontracted |  |  |
| pasini | uncontracted |  |  |
| paulic | uncontracted |  |  |
| pentaia | uncontracted |  |  |
| plaiut | uncontracted |  |  |
| podvesochi | uncontracted |  |  |
| poiana | present | AJVPS BIHOR |  |
| raul satului | uncontracted |  |  |
| raul valenilor | uncontracted |  |  |
| repedea | present | Direcția Silvică Maramureș | romsilva_map:exact |
| rica | uncontracted |  |  |
| ronisoara | uncontracted |  |  |
| runc | uncontracted |  |  |
| runcu mare | present | AJVPS MARAMUREȘ |  |
| ruscova | present | Direcția Silvică Maramureș | romsilva_map:prefix |
| salauta | present | AJVPS BISTRIŢA NĂSĂUD | audit_match:prefix |
| seradia | uncontracted |  |  |
| slatioara | uncontracted |  |  |
| spanu | uncontracted |  |  |
| stramba | present | AJPS Brașov |  |
| suciu | present | AJVPS MARAMUREȘ |  |
| tarlisua | uncontracted |  |  |
| telcisor | uncontracted |  |  |
| tibles | present | AJVPS MARAMUREȘ | anpa_map:sweep:tibles |
| tisovet | uncontracted |  |  |
| valea caselor | present | AJVPS ALBA |  |
| valea corbului | present | AVPS MIERCUREA-CIUC |  |
| valea gastei | uncontracted |  |  |
| valea gurguieti | uncontracted |  |  |
| valea lunga | uncontracted |  |  |
| valea morii | uncontracted |  |  |
| valea muntelui | uncontracted |  |  |
| valea neagra | present | Direcția Silvică Suceava | romsilva_map:group-shares-course |
| valea parusului | uncontracted |  |  |
| valea pestilor | uncontracted |  |  |
| valea plaiului | uncontracted |  |  |
| valea rea | uncontracted |  |  |
| valea sabii | uncontracted |  |  |
| valea scradei | uncontracted |  |  |
| valea stejarului | uncontracted |  |  |
| valea ursoiaia | uncontracted |  |  |
| valea vinului | uncontracted |  |  |
| vaserul | uncontracted |  |  |
| viseu | uncontracted |  |  |
| велика росош | uncontracted |  |  |

### Celulă 47.4-47.9N, 24.5-25.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| anies | present | AJVPS BISTRIŢA NĂSĂUD |  |
| aniesul mic | uncontracted |  |  |
| balasina | uncontracted |  |  |
| bardiu | uncontracted |  |  |
| barloaia | uncontracted |  |  |
| bila | uncontracted |  |  |
| birtu | uncontracted |  |  |
| bistrita | present | AJVPS BISTRIŢA NĂSĂUD |  |
| bistrita aurie | present | Direcția Silvică Maramureș | romsilva_map:exact |
| budescu | uncontracted |  |  |
| cartibavul mare | uncontracted |  |  |
| cercanelul | uncontracted |  |  |
| cobasel | uncontracted |  |  |
| cormaia | present | AJVPS BISTRIŢA NĂSĂUD |  |
| cosnea | uncontracted |  |  |
| cucureasa | uncontracted |  |  |
| dragos | uncontracted |  |  |
| dragovata | uncontracted |  |  |
| fantana | present | Direcția Silvică Maramureș | romsilva_map:exact |
| furul | uncontracted |  |  |
| gagi | uncontracted |  |  |
| gersa | present | AJVPS BISTRIŢA NĂSĂUD |  |
| gusatul mare | uncontracted |  |  |
| iza | present | AJVPS MARAMUREȘ | audit_match:exact |
| izvorul fantanii | uncontracted |  |  |
| izvorul laptelui | uncontracted |  |  |
| izvorul mare | present | AVPS MIERCUREA-CIUC |  |
| izvorul negru | present | AJVPS COVASNA | audit_match:prefix |
| lala | uncontracted |  |  |
| leurda | uncontracted |  |  |
| lutoasa | uncontracted |  |  |
| magura | uncontracted |  |  |
| maieru | uncontracted |  |  |
| maria | uncontracted |  |  |
| negoescu mare | uncontracted |  |  |
| novat | uncontracted |  |  |
| novicior | uncontracted |  |  |
| paraul bailor | uncontracted |  |  |
| paraul mic | present | AVPS MIERCUREA-CIUC |  |
| paraul pietrosul | uncontracted |  |  |
| paraul stanciu | uncontracted |  |  |
| parcalabul | uncontracted |  |  |
| paulic | uncontracted |  |  |
| pietrosu | uncontracted |  |  |
| rebra | present | Direcția Silvică Bistrița-Năsăud | romsilva_map:exact |
| repede | uncontracted |  |  |
| reviaca mare | uncontracted |  |  |
| reviaca mica | uncontracted |  |  |
| rica | uncontracted |  |  |
| rosu | present | Direcția Silvică Harghita |  |
| rosusul | uncontracted |  |  |
| ruscova | present | Direcția Silvică Maramureș | romsilva_map:prefix |
| sarata | present | AJVPS BOTOȘANI |  |
| sec | uncontracted |  |  |
| socolau | uncontracted |  |  |
| somesul mare | present | AJVPS BISTRIȚA-NĂSĂUD | anpa_map:sweep |
| stepan | uncontracted |  |  |
| stramba | present | AJPS Brașov |  |
| tasla | uncontracted |  |  |
| tibau | uncontracted |  |  |
| ursoaia | uncontracted |  |  |
| ursul | uncontracted |  |  |
| valea buneascu | uncontracted |  |  |
| valea caselor | present | AJVPS ALBA |  |
| valea gropii | uncontracted |  |  |
| valea gruietilor | uncontracted |  |  |
| valea hotarului | uncontracted |  |  |
| valea izvorului | uncontracted |  |  |
| valea magurii | uncontracted |  |  |
| valea mare | present | AVPS MIERCUREA-CIUC |  |
| valea pietrelor | uncontracted |  |  |
| valea rapelor | uncontracted |  |  |
| valea rea | uncontracted |  |  |
| valea vinului | uncontracted |  |  |
| vaserul | uncontracted |  |  |
| viemesu | uncontracted |  |  |
| vinisorul | uncontracted |  |  |
| viseu | uncontracted |  |  |
| viseut | uncontracted |  |  |
| альбін | uncontracted |  |  |
| баласинув | uncontracted |  |  |
| баласинів | uncontracted |  |  |
| білии черемош | uncontracted |  |  |
| великии прилучнии | uncontracted |  |  |
| гостовець | uncontracted |  |  |
| грамотнии великии | uncontracted |  |  |
| добрин | uncontracted |  |  |
| кривии | uncontracted |  |  |
| ластунець | uncontracted |  |  |
| лостун | uncontracted |  |  |
| маріін | uncontracted |  |  |
| маскотин | uncontracted |  |  |
| молочнии | uncontracted |  |  |
| мінчель | uncontracted |  |  |
| перкалаба | uncontracted |  |  |
| попадинець | uncontracted |  |  |
| прилучнии струмок | uncontracted |  |  |
| сарата | uncontracted |  |  |
| сивенькии | uncontracted |  |  |
| срібник | uncontracted |  |  |
| тонкии | uncontracted |  |  |
| тіснии | uncontracted |  |  |
| чорнии | uncontracted |  |  |
| чорнии черемош | uncontracted |  |  |
| чімірнии | uncontracted |  |  |
| широкии | uncontracted |  |  |
| яловичора | uncontracted |  |  |

### Celulă 47.4-47.9N, 25.0-25.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| argel | uncontracted |  |  |
| bistrita | present | AJVPS NEAMȚ | anpa_map:bistrita-basin |
| bistrita aurie | present | Direcția Silvică Maramureș | romsilva_map:exact |
| bolovan | uncontracted |  |  |
| boul mare | uncontracted |  |  |
| cibeu | uncontracted |  |  |
| cirlibaba | uncontracted |  |  |
| cucureasa | uncontracted |  |  |
| dubul | uncontracted |  |  |
| giumalau | present | Direcția Silvică Suceava | romsilva_map:exact |
| iezeru | uncontracted |  |  |
| lucina | uncontracted |  |  |
| maria | uncontracted |  |  |
| maria mica | uncontracted |  |  |
| moldova | present | AJVPS BOTOȘANI | anpa_map:bistrita-basin |
| moldovita | present | Direcția Silvică Suceava | romsilva_map:prefix |
| paraul negrei | uncontracted |  |  |
| paraul strajii | uncontracted |  |  |
| petac | uncontracted |  |  |
| pojorata | present-bbox | ANPA - Ape Necontractate |  |
| putna | present | Direcția Silvică Suceava | romsilva_map:exact |
| rascova | uncontracted |  |  |
| raul demacusa | uncontracted |  |  |
| sadau | uncontracted |  |  |
| sadova | uncontracted |  |  |
| sarata | present | AJVPS BOTOȘANI |  |
| somesul mare | present | AJVPS BISTRIȚA-NĂSĂUD | anpa_map:sweep |
| suceava | present | AJVPS BOTOȘANI | audit_match:exact |
| suceava river | uncontracted |  |  |
| suceava сучава | uncontracted |  |  |
| tibau | uncontracted |  |  |
| гидча вершик | uncontracted |  |  |
| горбанівськии | uncontracted |  |  |
| кобалора | uncontracted |  |  |
| кривии | uncontracted |  |  |
| лопушна | uncontracted |  |  |
| мелеш | uncontracted |  |  |
| путилка | uncontracted |  |  |
| рапочів | uncontracted |  |  |
| сарата | uncontracted |  |  |
| сучава | uncontracted |  |  |
| сучава suceava | uncontracted |  |  |
| торниківськии | uncontracted |  |  |
| чорнии | uncontracted |  |  |
| яловичора | uncontracted |  |  |

### Celulă 47.4-47.9N, 25.5-26.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bercheza | uncontracted |  |  |
| bistrita | present | AJVPS NEAMȚ | anpa_map:bistrita-basin |
| bitca neagra | uncontracted |  |  |
| blandet | uncontracted |  |  |
| boul mare | uncontracted |  |  |
| boul mic | uncontracted |  |  |
| brateasa | uncontracted |  |  |
| cheile moara dracului | uncontracted |  |  |
| ciobanu | uncontracted |  |  |
| ciumarna | uncontracted |  |  |
| corlateni | uncontracted |  |  |
| deia | uncontracted |  |  |
| dismireasa | uncontracted |  |  |
| dobra | present | FLY FISHING CLUB SIBIU |  |
| dragosa | uncontracted |  |  |
| frumosu | uncontracted |  |  |
| gemenea | uncontracted |  |  |
| grinda | uncontracted |  |  |
| hinata | uncontracted |  |  |
| humor | uncontracted |  |  |
| hurghis | uncontracted |  |  |
| izvor | uncontracted |  |  |
| izvorul malului | uncontracted |  |  |
| lela | uncontracted |  |  |
| mesteacanul | uncontracted |  |  |
| moara dracului | uncontracted |  |  |
| moldova | present | AVPS IAȘI |  |
| moldovita | present | Direcția Silvică Suceava | romsilva_map:prefix |
| morii | uncontracted |  |  |
| neagra | present | Direcția Silvică Suceava | romsilva_map:group-shares-course |
| negrileasa | uncontracted |  |  |
| p boului | uncontracted |  |  |
| paraul ciurgaului | uncontracted |  |  |
| paraul malului | uncontracted |  |  |
| paraul strajii | uncontracted |  |  |
| paraul toancelor | uncontracted |  |  |
| pojorata | present-bbox | ANPA - Ape Necontractate |  |
| putna | present | Direcția Silvică Suceava | romsilva_map:exact |
| putnisoara | uncontracted |  |  |
| rasca | uncontracted |  |  |
| rascova | uncontracted |  |  |
| raul ciumarna | uncontracted |  |  |
| raul demacusa | uncontracted |  |  |
| raul sucevita | uncontracted |  |  |
| raul vulcanu | uncontracted |  |  |
| remezeu | uncontracted |  |  |
| saca | uncontracted |  |  |
| sacries | uncontracted |  |  |
| sadova | uncontracted |  |  |
| slatioara | uncontracted |  |  |
| solca | uncontracted |  |  |
| solcuta | uncontracted |  |  |
| solonet | uncontracted |  |  |
| suceava | present | AJVPS BOTOȘANI | audit_match:exact |
| suceava river | uncontracted |  |  |
| sucevita | uncontracted |  |  |
| suha | uncontracted |  |  |
| suha mica | uncontracted |  |  |
| valea caselor | present | AJVPS ALBA |  |
| valea colbului | uncontracted |  |  |
| valea seaca | uncontracted |  |  |
| vicov river | uncontracted |  |  |
| voitinel | uncontracted |  |  |
| voronet | uncontracted |  |  |

### Celulă 47.4-47.9N, 26.0-26.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bogata | present | Direcția Silvică Brașov | romsilva_map:exact |
| cotargaci | uncontracted |  |  |
| dragomirna | uncontracted |  |  |
| moldova | present | AVPS IAȘI |  |
| molnita | present | AJVPS BOTOȘANI |  |
| morisca | uncontracted |  |  |
| paraul sipot | uncontracted |  |  |
| paraul targului | present | AJVPS ARGEȘ | audit_match:prefix |
| raul sucevita | uncontracted |  |  |
| siret | present | AVPS IAȘI |  |
| solonet | uncontracted |  |  |
| somuzulu mare | uncontracted |  |  |
| suceava | present | AJVPS BOTOȘANI | audit_match:exact |
| suceava river | uncontracted |  |  |
| sucevita | uncontracted |  |  |
| suha mare | uncontracted |  |  |
| suha mica | uncontracted |  |  |
| targu | uncontracted |  |  |
| valea seaca | uncontracted |  |  |

### Celulă 47.4-47.9N, 26.5-27.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bahlui | uncontracted |  |  |
| bahluiul mic | uncontracted |  |  |
| baiceni | uncontracted |  |  |
| baros | uncontracted |  |  |
| baseu | present | AJVPS BOTOȘANI |  |
| burla | uncontracted |  |  |
| cotargaci | uncontracted |  |  |
| draslea | uncontracted |  |  |
| dresleuca | uncontracted |  |  |
| iazul lipoveanului | uncontracted |  |  |
| ionascu | uncontracted |  |  |
| jijia | present | AJVPS BOTOȘANI |  |
| luizoaia | uncontracted |  |  |
| miletin | present | AJVPS BOTOȘANI |  |
| morisca | uncontracted |  |  |
| plesu | present | AJVPS BOTOȘANI |  |
| siret | present | AVPS IAȘI |  |
| siretel | present | AJVPS BOTOȘANI |  |
| sitna | present | AJVPS BOTOȘANI |  |
| somuzul mare | present | AJVPS BOTOȘANI | audit_match:prefix |
| somuzulu mare | uncontracted |  |  |
| suceava | present | AJVPS BOTOȘANI | audit_match:exact |
| suceava river | uncontracted |  |  |
| teasc | uncontracted |  |  |
| valea ciolpanilor | uncontracted |  |  |
| valea mare | present | AVPS MIERCUREA-CIUC |  |
| varnita | uncontracted |  |  |

### Celulă 47.4-47.9N, 27.0-27.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| baseu | present | AJVPS BOTOȘANI |  |
| caldarusa | uncontracted |  |  |
| camenca | uncontracted |  |  |
| ciuhur | uncontracted |  |  |
| draslea | uncontracted |  |  |
| glodeanca | uncontracted |  |  |
| guranda | uncontracted |  |  |
| gurguiata | uncontracted |  |  |
| jijia | present | AJVPS BOTOȘANI |  |
| miletin | present | AJVPS BOTOȘANI |  |
| pais | uncontracted |  |  |
| prut | present | AVPS IAȘI |  |
| prut / прут | uncontracted |  |  |
| sitna | present | AJVPS BOTOȘANI |  |
| дністер / nistru | uncontracted |  |  |

### Celulă 47.4-47.9N, 27.5-28.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| caldarusa | uncontracted |  |  |
| ciulucul de mijloc | uncontracted |  |  |
| ciulucul mare | uncontracted |  |  |
| ciulucul mic | uncontracted |  |  |
| copaceanca | uncontracted |  |  |
| cubolta | uncontracted |  |  |
| cula | uncontracted |  |  |
| delia | uncontracted |  |  |
| flamanda | uncontracted |  |  |
| garla mare | present | AVPS MIERCUREA-CIUC |  |
| girla mica | uncontracted |  |  |
| glodeanca | uncontracted |  |  |
| parau | uncontracted |  |  |
| prut | present | AVPS IAȘI |  |
| prut / прут | uncontracted |  |  |
| raul cubolta | uncontracted |  |  |
| raut | uncontracted |  |  |
| rautel | uncontracted |  |  |
| soltoaia | uncontracted |  |  |
| sovatul mare | uncontracted |  |  |
| sovatul mic | uncontracted |  |  |
| tarina veche | uncontracted |  |  |
| teioasa | uncontracted |  |  |
| дністер / nistru | uncontracted |  |  |

### Celulă 47.4-47.9N, 28.0-28.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bahu | uncontracted |  |  |
| cainari | uncontracted |  |  |
| camenca | uncontracted |  |  |
| chiva | uncontracted |  |  |
| ciorna | uncontracted |  |  |
| ciulucul de mijloc | uncontracted |  |  |
| ciulucul mare | uncontracted |  |  |
| ciulucul mic | uncontracted |  |  |
| cubolta | uncontracted |  |  |
| cula | uncontracted |  |  |
| eligacea | uncontracted |  |  |
| iligacia | uncontracted |  |  |
| raul cubolta | uncontracted |  |  |
| raul raut | uncontracted |  |  |
| raut | uncontracted |  |  |
| solonet | uncontracted |  |  |
| valea radoaiei | uncontracted |  |  |
| дністер / nistru | uncontracted |  |  |

### Celulă 47.4-47.9N, 28.5-29.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| blanarita | uncontracted |  |  |
| ciorna | uncontracted |  |  |
| ciulucul mare | uncontracted |  |  |
| cula | uncontracted |  |  |
| draghinici | uncontracted |  |  |
| jidauca | uncontracted |  |  |
| malovatet | uncontracted |  |  |
| nistru днестр | uncontracted |  |  |
| raut | uncontracted |  |  |
| vale rezina | uncontracted |  |  |
| белочи | uncontracted |  |  |
| белочи білоч | uncontracted |  |  |
| дністер / nistru | uncontracted |  |  |
| рибниця | uncontracted |  |  |
| рыбница | uncontracted |  |  |
| строенцы | uncontracted |  |  |

### Celulă 47.4-47.9N, 29.0-29.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| iagorlac / ягорлик | uncontracted |  |  |
| nistru днестр | uncontracted |  |  |
| trostinet тростянець тростянец | uncontracted |  |  |
| воронково | uncontracted |  |  |
| дністер / nistru | uncontracted |  |  |
| молокиш | uncontracted |  |  |
| окна | uncontracted |  |  |
| рибниця | uncontracted |  |  |
| рибниця raul ribnita рибниця | uncontracted |  |  |
| рибниця raul ribnita рыбница | uncontracted |  |  |
| рыбница | uncontracted |  |  |
| сухии ягорлик | uncontracted |  |  |
| сухои ягорлык | uncontracted |  |  |
| тростянец | uncontracted |  |  |
| тростянець | uncontracted |  |  |
| ягорлик | uncontracted |  |  |
| ягорлик ягорлик rau iagorlac | uncontracted |  |  |
| ягорлык iagorlac | uncontracted |  |  |
| ягорлык rau iagorlac | uncontracted |  |  |

### Celulă 47.4-47.9N, 29.5-30.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| iagorlac / ягорлик | uncontracted |  |  |
| валегоцулова | uncontracted |  |  |
| великии канаи | uncontracted |  |  |
| великии куяльник | uncontracted |  |  |
| вижна | uncontracted |  |  |
| двуріцькии | uncontracted |  |  |
| десинора | uncontracted |  |  |
| канаи | uncontracted |  |  |
| кучурган | uncontracted |  |  |
| кучурган / cuciurgan | uncontracted |  |  |
| мазурівськии | uncontracted |  |  |
| осач | uncontracted |  |  |
| примка | uncontracted |  |  |
| сомова | uncontracted |  |  |
| сухии ягорлик | uncontracted |  |  |
| тамашлик | uncontracted |  |  |
| тилігул | uncontracted |  |  |
| тілігул | uncontracted |  |  |
| ягорлик | uncontracted |  |  |

### Celulă 47.9-48.4N, 20.0-20.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| almar patak | uncontracted |  |  |
| aranyos patak | uncontracted |  |  |
| arloi patak | uncontracted |  |  |
| ban patak | uncontracted |  |  |
| barci patak | uncontracted |  |  |
| baroc patak | uncontracted |  |  |
| berva patak | uncontracted |  |  |
| blh | uncontracted |  |  |
| boroszlo patak | uncontracted |  |  |
| branicky kanal | uncontracted |  |  |
| bukkszeki patak | uncontracted |  |  |
| cizsky kanal | uncontracted |  |  |
| csaszar patak | uncontracted |  |  |
| cseresznyes patak | uncontracted |  |  |
| csernely patak | uncontracted |  |  |
| csimas patak | uncontracted |  |  |
| csokva patak | uncontracted |  |  |
| csom pataka | uncontracted |  |  |
| csondro patak | uncontracted |  |  |
| csortos patak | uncontracted |  |  |
| ecser patak | uncontracted |  |  |
| eger patak | uncontracted |  |  |
| eskerenna patak | uncontracted |  |  |
| gilitka patak | uncontracted |  |  |
| gizsir patak | uncontracted |  |  |
| gyepes patak | uncontracted |  |  |
| hangony | uncontracted |  |  |
| hatar volgyi patak | uncontracted |  |  |
| hodos patak | uncontracted |  |  |
| horotna patak | uncontracted |  |  |
| kajla patak | uncontracted |  |  |
| kanya patak | uncontracted |  |  |
| karacsony volgyi patak | uncontracted |  |  |
| kelemer patak | uncontracted |  |  |
| kigyos patak | uncontracted |  |  |
| kirald patak | uncontracted |  |  |
| lasko | uncontracted |  |  |
| leany volgyi patak | uncontracted |  |  |
| leleszi patak | uncontracted |  |  |
| macaci potok | uncontracted |  |  |
| malompatak | uncontracted |  |  |
| meh patak | uncontracted |  |  |
| mehecso patak | uncontracted |  |  |
| meller volgy folyasa | uncontracted |  |  |
| mercse patak | uncontracted |  |  |
| mesz volgyi patak | uncontracted |  |  |
| nagy volgyi patak | uncontracted |  |  |
| orveny patak | uncontracted |  |  |
| ostoros patak | uncontracted |  |  |
| pohansky potok | uncontracted |  |  |
| recska patak | uncontracted |  |  |
| rimava | uncontracted |  |  |
| sajo | uncontracted |  |  |
| satai patak | uncontracted |  |  |
| slana | uncontracted |  |  |
| slana / sajo | uncontracted |  |  |
| szalajka patak | uncontracted |  |  |
| szana patak | uncontracted |  |  |
| szentgyorgy patak | uncontracted |  |  |
| szilvas patak | uncontracted |  |  |
| szolati patak | uncontracted |  |  |
| szornyu volgyi patak | uncontracted |  |  |
| szoros patak | uncontracted |  |  |
| szurdokvolgy | uncontracted |  |  |
| tarkanyi patak | uncontracted |  |  |
| tarkanyi viz | uncontracted |  |  |
| tarna | uncontracted |  |  |
| taro patak | uncontracted |  |  |
| teska | uncontracted |  |  |
| uraj patak | uncontracted |  |  |
| uszo patak | uncontracted |  |  |
| villoi patak | uncontracted |  |  |
| vlkynsky potok | uncontracted |  |  |
| voros ko patak | uncontracted |  |  |
| vorosko patak | uncontracted |  |  |
| zsuponyo patak | uncontracted |  |  |

### Celulă 47.9-48.4N, 20.5-21.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| alacska patak | uncontracted |  |  |
| babony patak | uncontracted |  |  |
| babonyi patak | uncontracted |  |  |
| ban patak | uncontracted |  |  |
| barci patak | uncontracted |  |  |
| barsonyos | uncontracted |  |  |
| bodva | uncontracted |  |  |
| bodva / bodva | uncontracted |  |  |
| budos kut volgy | uncontracted |  |  |
| cseresznyes patak | uncontracted |  |  |
| csimas patak | uncontracted |  |  |
| csincse patak | uncontracted |  |  |
| csom pataka | uncontracted |  |  |
| csondro patak | uncontracted |  |  |
| csure patak | uncontracted |  |  |
| damaki patak | uncontracted |  |  |
| dios patak | uncontracted |  |  |
| dios patak deli ag | uncontracted |  |  |
| dios patak keleti ag | uncontracted |  |  |
| disznos patak | uncontracted |  |  |
| galambos patak | uncontracted |  |  |
| galgoci patak | uncontracted |  |  |
| galya patak | uncontracted |  |  |
| garadna patak | uncontracted |  |  |
| goromboly | uncontracted |  |  |
| hangacs patak | uncontracted |  |  |
| harica patak | uncontracted |  |  |
| hejo | uncontracted |  |  |
| hernad | uncontracted |  |  |
| hideg viz | uncontracted |  |  |
| hideg viz also ag | uncontracted |  |  |
| hideg viz felso ag | uncontracted |  |  |
| hideg viz kozep ag | uncontracted |  |  |
| hideg volgy | uncontracted |  |  |
| holt szuha | uncontracted |  |  |
| hor patak | uncontracted |  |  |
| horhos | uncontracted |  |  |
| hornad / hernad | uncontracted |  |  |
| jezus | uncontracted |  |  |
| juhdoglo | uncontracted |  |  |
| kacsi patak | uncontracted |  |  |
| kanya folyas | uncontracted |  |  |
| kereszt patak | uncontracted |  |  |
| kis csincse | uncontracted |  |  |
| kis sajo | uncontracted |  |  |
| kis szallas volgy | uncontracted |  |  |
| kis szinva | uncontracted |  |  |
| kopus volgy | uncontracted |  |  |
| kulcsar volgyi patak | uncontracted |  |  |
| kupai vadasz patak | uncontracted |  |  |
| lator patak | uncontracted |  |  |
| liszko patak | uncontracted |  |  |
| lyuko | uncontracted |  |  |
| mesz patak | uncontracted |  |  |
| nagy hegy volgyi patak | uncontracted |  |  |
| nyeki patak | uncontracted |  |  |
| nyogo patak | uncontracted |  |  |
| nyogo patak holtag | uncontracted |  |  |
| ordog patak | uncontracted |  |  |
| ordogvolgyi patak | uncontracted |  |  |
| ormos patak | uncontracted |  |  |
| penz patak | uncontracted |  |  |
| pereces patak | uncontracted |  |  |
| rednek patak | uncontracted |  |  |
| rejtek patak | uncontracted |  |  |
| sajo | uncontracted |  |  |
| salyi patak | uncontracted |  |  |
| sebes viz | uncontracted |  |  |
| selyebi vadasz patak | uncontracted |  |  |
| slana / sajo | uncontracted |  |  |
| szaraz to er | uncontracted |  |  |
| szinva | uncontracted |  |  |
| szinva patak | uncontracted |  |  |
| szoros patak | uncontracted |  |  |
| szuha patak | uncontracted |  |  |
| szurdok | uncontracted |  |  |
| szurdokvolgy | uncontracted |  |  |
| tamas szeki volgy | uncontracted |  |  |
| tardi er | uncontracted |  |  |
| tardi patak | uncontracted |  |  |
| tardona patak | uncontracted |  |  |
| tatar arok | uncontracted |  |  |
| uri | uncontracted |  |  |
| vadasz patak | uncontracted |  |  |
| vargaszogi patak | uncontracted |  |  |
| varom patak | uncontracted |  |  |
| vasonca | uncontracted |  |  |
| villam godre | uncontracted |  |  |
| vizmosas | uncontracted |  |  |
| ziliz patak | uncontracted |  |  |

### Celulă 47.9-48.4N, 21.0-21.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| aranyos patak | uncontracted |  |  |
| barsonyos | uncontracted |  |  |
| belus patak | uncontracted |  |  |
| benye patak | uncontracted |  |  |
| bodrog | uncontracted |  |  |
| boglyos patak | uncontracted |  |  |
| csobad patak | uncontracted |  |  |
| fancsali patak | uncontracted |  |  |
| furdo patak | uncontracted |  |  |
| galambos patak | uncontracted |  |  |
| gilip patak | uncontracted |  |  |
| harangod er | uncontracted |  |  |
| hernad | uncontracted |  |  |
| hideg patak | uncontracted |  |  |
| hornad / hernad | uncontracted |  |  |
| hortobagy | uncontracted |  |  |
| ilona patak | uncontracted |  |  |
| koldu patak | uncontracted |  |  |
| laposi patak | uncontracted |  |  |
| lencses patak | uncontracted |  |  |
| madi patak | uncontracted |  |  |
| maj patak | uncontracted |  |  |
| megyaszo patak | uncontracted |  |  |
| mely patak | uncontracted |  |  |
| o takta | uncontracted |  |  |
| peres er | uncontracted |  |  |
| rany folyas | uncontracted |  |  |
| remeny patak | uncontracted |  |  |
| sajo | uncontracted |  |  |
| sarkad er | uncontracted |  |  |
| slana / sajo | uncontracted |  |  |
| szarkakuti patak | uncontracted |  |  |
| szerencs patak | uncontracted |  |  |
| tisza | uncontracted |  |  |
| tolcsva patak | uncontracted |  |  |
| uzemviz csatorna | uncontracted |  |  |
| var patak | uncontracted |  |  |
| vasonca | uncontracted |  |  |
| zsadany patak | uncontracted |  |  |

### Celulă 47.9-48.4N, 21.5-22.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| balkanyi folyas | uncontracted |  |  |
| bikakaszaloi szivargo | uncontracted |  |  |
| bodrog | uncontracted |  |  |
| butykai szivargo | uncontracted |  |  |
| csalokozi csatorna | uncontracted |  |  |
| csengeri iskolai szivargo | uncontracted |  |  |
| darno arok | uncontracted |  |  |
| hantos fele szivargo | uncontracted |  |  |
| hercegkuti patak | uncontracted |  |  |
| hosszuhati szivargo | uncontracted |  |  |
| igrice csatorna | uncontracted |  |  |
| igrice oldalag | uncontracted |  |  |
| jakus toi csatorna | uncontracted |  |  |
| kalloi fofolyas | uncontracted |  |  |
| kalmar reti szivargo | uncontracted |  |  |
| karcsa csatorna | uncontracted |  |  |
| kerulohazi csatorna | uncontracted |  |  |
| kisszek hosszuhati szivargo | uncontracted |  |  |
| lukalaposi szivargo | uncontracted |  |  |
| mandai folyas | uncontracted |  |  |
| nadasi szivargo | uncontracted |  |  |
| nadastoi szivargo | uncontracted |  |  |
| nagylapos bogarhazi 1 oldalag | uncontracted |  |  |
| nagylapos bogarhazi szivargo | uncontracted |  |  |
| napkori folyas | uncontracted |  |  |
| nyirjes toi folyas | uncontracted |  |  |
| nyulastoi csatorna | uncontracted |  |  |
| oros pappreti szivargo | uncontracted |  |  |
| oros sostoi szivargo | uncontracted |  |  |
| oros urreti szivargo | uncontracted |  |  |
| pazony kemecsei kulonfolyas | uncontracted |  |  |
| pazonyi folyas | uncontracted |  |  |
| regi hotyka patak | uncontracted |  |  |
| simai fofolyas | uncontracted |  |  |
| skanzen csatorna | uncontracted |  |  |
| szarkakuti patak | uncontracted |  |  |
| sztarek szivargo | uncontracted |  |  |
| tisza | uncontracted |  |  |
| varosi csatorna | uncontracted |  |  |
| vii/1 mellekag | uncontracted |  |  |
| viii /3 1 mellekag | uncontracted |  |  |
| viii /3 3 mellekag | uncontracted |  |  |
| viii /3 4 mellekag | uncontracted |  |  |
| viii/2 sz folyas | uncontracted |  |  |
| viii/3 2 mellekag | uncontracted |  |  |
| zsombekos folyas | uncontracted |  |  |

### Celulă 47.9-48.4N, 22.0-22.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| csaronda csatorna | uncontracted |  |  |
| csaronda csatorna чаронда | uncontracted |  |  |
| dedai focsatorna | uncontracted |  |  |
| doge kisvarda csatorna | uncontracted |  |  |
| kerulohazi csatorna | uncontracted |  |  |
| kraszna | uncontracted |  |  |
| marokpapi csatorna | uncontracted |  |  |
| nagy vajas | uncontracted |  |  |
| oreg tur | uncontracted |  |  |
| sipos arok | uncontracted |  |  |
| szamos | uncontracted |  |  |
| szipa focsatorna | uncontracted |  |  |
| tisza | uncontracted |  |  |
| міц | uncontracted |  |  |
| серне | uncontracted |  |  |

### Celulă 47.9-48.4N, 22.5-23.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| batar patak старии ботар | uncontracted |  |  |
| cser patak | uncontracted |  |  |
| dedai focsatorna | uncontracted |  |  |
| gogo szenke | uncontracted |  |  |
| marokpapi csatorna | uncontracted |  |  |
| mosztok csatorna | uncontracted |  |  |
| oreg tur | uncontracted |  |  |
| palad patak | uncontracted |  |  |
| palad patak паладь | uncontracted |  |  |
| sar eger csatorna | uncontracted |  |  |
| szamos | uncontracted |  |  |
| szamossalyi arapaszto | uncontracted |  |  |
| szipa focsatorna | uncontracted |  |  |
| tisza | uncontracted |  |  |
| tiszaberki sar csatorna | uncontracted |  |  |
| tur | present | AJVPS SATU MARE | audit_match:exact |
| tur тур | uncontracted |  |  |
| бельва | uncontracted |  |  |
| боржава | uncontracted |  |  |
| вебовецькии потік | uncontracted |  |  |
| вербовецькии потік | uncontracted |  |  |
| верке | uncontracted |  |  |
| глибокии | uncontracted |  |  |
| гнилии потік | uncontracted |  |  |
| гримучіи потік | uncontracted |  |  |
| мала боржава | uncontracted |  |  |
| мала тиса | uncontracted |  |  |
| мерце | uncontracted |  |  |
| новии ботар | uncontracted |  |  |
| оночок | uncontracted |  |  |
| паладь | uncontracted |  |  |
| сальва | uncontracted |  |  |
| серне | uncontracted |  |  |
| смердек | uncontracted |  |  |
| старии ботар | uncontracted |  |  |
| тиса | uncontracted |  |  |
| тиса tisza | uncontracted |  |  |
| іршава | uncontracted |  |  |

### Celulă 47.9-48.4N, 23.0-23.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| batarci | uncontracted |  |  |
| tarna mare | uncontracted |  |  |
| tarna mica | uncontracted |  |  |
| tisza | uncontracted |  |  |
| tur | present | AJVPS SATU MARE | audit_match:exact |
| ulics patak | uncontracted |  |  |
| valea rea | uncontracted |  |  |
| баилова | uncontracted |  |  |
| батарч | uncontracted |  |  |
| бельва | uncontracted |  |  |
| бербеке | uncontracted |  |  |
| бистра | uncontracted |  |  |
| боржава | uncontracted |  |  |
| боркут | uncontracted |  |  |
| боронявка | uncontracted |  |  |
| ботар | uncontracted |  |  |
| буковецькии | uncontracted |  |  |
| буковыи потук | uncontracted |  |  |
| білка | uncontracted |  |  |
| великыи глубокыи | uncontracted |  |  |
| вовчии | uncontracted |  |  |
| гаспарка | uncontracted |  |  |
| глибокии | uncontracted |  |  |
| лазувськии струмок | uncontracted |  |  |
| ліпце | uncontracted |  |  |
| маидан | uncontracted |  |  |
| млиновиця | uncontracted |  |  |
| новии ботар | uncontracted |  |  |
| оночок | uncontracted |  |  |
| попець | uncontracted |  |  |
| рика | uncontracted |  |  |
| ріка | uncontracted |  |  |
| сальва | uncontracted |  |  |
| синявка | uncontracted |  |  |
| старии ботар | uncontracted |  |  |
| сільськии | uncontracted |  |  |
| теребля | uncontracted |  |  |
| тиса | uncontracted |  |  |
| тіблер | uncontracted |  |  |
| хустець | uncontracted |  |  |
| хустик | uncontracted |  |  |
| чинґавка | uncontracted |  |  |
| шарош | uncontracted |  |  |
| іршава | uncontracted |  |  |

### Celulă 47.9-48.4N, 23.5-24.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| iza | present | AJVPS MARAMUREȘ | audit_match:exact |
| ronisoara | uncontracted |  |  |
| sapanta | uncontracted |  |  |
| sarasau | uncontracted |  |  |
| tisa | present | AJVPS MARAMUREȘ |  |
| tisza | uncontracted |  |  |
| valea pastailor | uncontracted |  |  |
| valea rea | uncontracted |  |  |
| апшиця | uncontracted |  |  |
| баилова | uncontracted |  |  |
| велика уголька | uncontracted |  |  |
| вільхівчик | uncontracted |  |  |
| глибокии потік | uncontracted |  |  |
| красношурка | uncontracted |  |  |
| лазувськии струмок | uncontracted |  |  |
| лужанка | uncontracted |  |  |
| мала уголька | uncontracted |  |  |
| одарів | uncontracted |  |  |
| рика | uncontracted |  |  |
| ріка | uncontracted |  |  |
| стара ріка | uncontracted |  |  |
| сухии | uncontracted |  |  |
| теребля | uncontracted |  |  |
| тересва | uncontracted |  |  |
| терешілка | uncontracted |  |  |
| тиса | uncontracted |  |  |
| тиса tisa | uncontracted |  |  |
| тьовшаг | uncontracted |  |  |
| тячівець | uncontracted |  |  |
| яблуниця | uncontracted |  |  |

### Celulă 47.9-48.4N, 24.0-24.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bistra | present | AJVPS MUREȘ |  |
| repedea | present | Direcția Silvică Maramureș | romsilva_map:exact |
| ronisoara | uncontracted |  |  |
| rosusul mic | uncontracted |  |  |
| tisza | uncontracted |  |  |
| viseu | uncontracted |  |  |
| апшинець | uncontracted |  |  |
| белеів | uncontracted |  |  |
| богдан | uncontracted |  |  |
| бребенескул | uncontracted |  |  |
| бребоя | uncontracted |  |  |
| бредецел | uncontracted |  |  |
| біла тиса | uncontracted |  |  |
| білии | uncontracted |  |  |
| білинськии | uncontracted |  |  |
| велика росош | uncontracted |  |  |
| великии потік | uncontracted |  |  |
| великии тростянець | uncontracted |  |  |
| видрічка | uncontracted |  |  |
| вовчии | uncontracted |  |  |
| говерла | uncontracted |  |  |
| головник | uncontracted |  |  |
| гропинець | uncontracted |  |  |
| дезескул | uncontracted |  |  |
| кваснии | uncontracted |  |  |
| кевелів | uncontracted |  |  |
| козмещик | uncontracted |  |  |
| комарник | uncontracted |  |  |
| косівська | uncontracted |  |  |
| крив’янка | uncontracted |  |  |
| кукуська | uncontracted |  |  |
| лазещина | uncontracted |  |  |
| лешул | uncontracted |  |  |
| лихии | uncontracted |  |  |
| лопушанка | uncontracted |  |  |
| лощинськии | uncontracted |  |  |
| мала шопурка | uncontracted |  |  |
| малии берлебаш | uncontracted |  |  |
| малии тростянець | uncontracted |  |  |
| маслокрут | uncontracted |  |  |
| нориця | uncontracted |  |  |
| павлик | uncontracted |  |  |
| панськии | uncontracted |  |  |
| пародчин | uncontracted |  |  |
| полунськии | uncontracted |  |  |
| потiк мала росош | uncontracted |  |  |
| радомир | uncontracted |  |  |
| руч лазещина | uncontracted |  |  |
| руч озирны | uncontracted |  |  |
| руч туркулець | uncontracted |  |  |
| ручеи барабуськи | uncontracted |  |  |
| сауляк | uncontracted |  |  |
| свидовець | uncontracted |  |  |
| свинськии | uncontracted |  |  |
| середня ріка | uncontracted |  |  |
| скороднии | uncontracted |  |  |
| скоруш | uncontracted |  |  |
| станіслав | uncontracted |  |  |
| сільськии потік | uncontracted |  |  |
| сітнии | uncontracted |  |  |
| тиса | uncontracted |  |  |
| тиса tisa | uncontracted |  |  |
| труфанець | uncontracted |  |  |
| турбат | uncontracted |  |  |
| чорна тиса | uncontracted |  |  |
| шопурка | uncontracted |  |  |
| шумнєськии | uncontracted |  |  |
| щаул | uncontracted |  |  |
| яблуниця | uncontracted |  |  |
| явiрниковии | uncontracted |  |  |
| ялин | uncontracted |  |  |

### Celulă 47.9-48.4N, 24.5-25.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| paradczyn nimakowski | uncontracted |  |  |
| prut / прут | uncontracted |  |  |
| rica | uncontracted |  |  |
| rosusul | uncontracted |  |  |
| rosusul mare | uncontracted |  |  |
| rosusul mic | uncontracted |  |  |
| ruscova | present | Direcția Silvică Maramureș | romsilva_map:prefix |
| socolau | uncontracted |  |  |
| альбін | uncontracted |  |  |
| бальзатул | uncontracted |  |  |
| безвіннии | uncontracted |  |  |
| безулька | uncontracted |  |  |
| бережниця | uncontracted |  |  |
| бребенескул | uncontracted |  |  |
| брустурка | uncontracted |  |  |
| біла річка | uncontracted |  |  |
| біла тиса | uncontracted |  |  |
| білии | uncontracted |  |  |
| білии черемош | uncontracted |  |  |
| бістрець | uncontracted |  |  |
| вiпчинка | uncontracted |  |  |
| васкуль | uncontracted |  |  |
| велика дристунка | uncontracted |  |  |
| великии білии | uncontracted |  |  |
| великии керничнии | uncontracted |  |  |
| воитул | uncontracted |  |  |
| вущик | uncontracted |  |  |
| віпче | uncontracted |  |  |
| гаврилець великии | uncontracted |  |  |
| гнилець | uncontracted |  |  |
| грамотнии великии | uncontracted |  |  |
| грамотнии малии | uncontracted |  |  |
| грималюків витік | uncontracted |  |  |
| данцежик | uncontracted |  |  |
| данцюжок | uncontracted |  |  |
| датницькии | uncontracted |  |  |
| дешко | uncontracted |  |  |
| дзембронька | uncontracted |  |  |
| дземброня | uncontracted |  |  |
| дихтинець | uncontracted |  |  |
| добрин | uncontracted |  |  |
| жаб євськии | uncontracted |  |  |
| жаб івськии | uncontracted |  |  |
| жовнірськии струмок | uncontracted |  |  |
| за дзюрчем | uncontracted |  |  |
| заросляцькии | uncontracted |  |  |
| зміінськии | uncontracted |  |  |
| кекача | uncontracted |  |  |
| козмеськии | uncontracted |  |  |
| кривець | uncontracted |  |  |
| кровавец | uncontracted |  |  |
| кєкача | uncontracted |  |  |
| кізя | uncontracted |  |  |
| лемськии | uncontracted |  |  |
| липовець | uncontracted |  |  |
| лопушна | uncontracted |  |  |
| лудовець | uncontracted |  |  |
| луковець | uncontracted |  |  |
| мала дрестунка | uncontracted |  |  |
| малии білии | uncontracted |  |  |
| маришевськии | uncontracted |  |  |
| маріін | uncontracted |  |  |
| михаилів | uncontracted |  |  |
| миші | uncontracted |  |  |
| млинівськии потік | uncontracted |  |  |
| мосірнии | uncontracted |  |  |
| мріє | uncontracted |  |  |
| мунчель | uncontracted |  |  |
| нижніи бахончик | uncontracted |  |  |
| озiрнии | uncontracted |  |  |
| озірнии | uncontracted |  |  |
| орендарчик | uncontracted |  |  |
| пародчин | uncontracted |  |  |
| пародчин нимаківськии | uncontracted |  |  |
| плаєк | uncontracted |  |  |
| погорілець | uncontracted |  |  |
| подороватии | uncontracted |  |  |
| прелучнии | uncontracted |  |  |
| прилучнии струмок | uncontracted |  |  |
| припір | uncontracted |  |  |
| пробіина | uncontracted |  |  |
| прут | uncontracted |  |  |
| пігии | uncontracted |  |  |
| пістинька | uncontracted |  |  |
| рабинець | uncontracted |  |  |
| регещик | uncontracted |  |  |
| рибниця | uncontracted |  |  |
| рибніца | uncontracted |  |  |
| руськии | uncontracted |  |  |
| руч озирны | uncontracted |  |  |
| руч туркулець | uncontracted |  |  |
| річка | uncontracted |  |  |
| сліпуика | uncontracted |  |  |
| старии | uncontracted |  |  |
| стоговець | uncontracted |  |  |
| стоянів | uncontracted |  |  |
| студеник | uncontracted |  |  |
| суха | uncontracted |  |  |
| суха розсіч | uncontracted |  |  |
| сухии потік | uncontracted |  |  |
| тиховатчик | uncontracted |  |  |
| томнатик | uncontracted |  |  |
| топiльче | uncontracted |  |  |
| топільче великии | uncontracted |  |  |
| форещанка | uncontracted |  |  |
| форещина | uncontracted |  |  |
| форещинка | uncontracted |  |  |
| хараль | uncontracted |  |  |
| цибульник | uncontracted |  |  |
| черемоватии | uncontracted |  |  |
| черемош | uncontracted |  |  |
| чорна річка | uncontracted |  |  |
| чорнии | uncontracted |  |  |
| чорнии черемош | uncontracted |  |  |
| шибении | uncontracted |  |  |
| шкорушнии | uncontracted |  |  |
| щаул | uncontracted |  |  |
| ільця | uncontracted |  |  |
| ільці | uncontracted |  |  |

### Celulă 47.9-48.4N, 25.0-25.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| falcau | uncontracted |  |  |
| prut / прут | uncontracted |  |  |
| sadau | uncontracted |  |  |
| siret | present | AJVPS BOTOȘANI |  |
| suceava river | uncontracted |  |  |
| арджиу | uncontracted |  |  |
| бабин | uncontracted |  |  |
| бережниця | uncontracted |  |  |
| бережонка | uncontracted |  |  |
| бисків | uncontracted |  |  |
| борсуки | uncontracted |  |  |
| великии бисків | uncontracted |  |  |
| виженка | uncontracted |  |  |
| волиця | uncontracted |  |  |
| ворохтич | uncontracted |  |  |
| гнилиця | uncontracted |  |  |
| гільча | uncontracted |  |  |
| дихтинець | uncontracted |  |  |
| дністер / nistru | uncontracted |  |  |
| думитриця | uncontracted |  |  |
| звараш | uncontracted |  |  |
| зубринець | uncontracted |  |  |
| каменець | uncontracted |  |  |
| коритниця | uncontracted |  |  |
| лекечі | uncontracted |  |  |
| лопушна | uncontracted |  |  |
| лустун | uncontracted |  |  |
| лісківець | uncontracted |  |  |
| мала виженка | uncontracted |  |  |
| малии сірет | uncontracted |  |  |
| мигівка | uncontracted |  |  |
| михидра | uncontracted |  |  |
| михідра | uncontracted |  |  |
| миші | uncontracted |  |  |
| мленюца | uncontracted |  |  |
| пантін | uncontracted |  |  |
| приємськии | uncontracted |  |  |
| просянка | uncontracted |  |  |
| путилка | uncontracted |  |  |
| пістинька | uncontracted |  |  |
| рибниця | uncontracted |  |  |
| рожен великии | uncontracted |  |  |
| роженка | uncontracted |  |  |
| садеу | uncontracted |  |  |
| свідовець | uncontracted |  |  |
| серетель | uncontracted |  |  |
| сикавка | uncontracted |  |  |
| славець | uncontracted |  |  |
| смугар | uncontracted |  |  |
| солонець великии | uncontracted |  |  |
| стебник | uncontracted |  |  |
| сторонецькии потік | uncontracted |  |  |
| стоянів | uncontracted |  |  |
| сухии | uncontracted |  |  |
| сірет | uncontracted |  |  |
| товарниця | uncontracted |  |  |
| фальків | uncontracted |  |  |
| фошке | uncontracted |  |  |
| черемош | uncontracted |  |  |
| черепанка | uncontracted |  |  |

### Celulă 47.9-48.4N, 25.5-26.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| hlinita | uncontracted |  |  |
| prut / прут | uncontracted |  |  |
| putna | present | Direcția Silvică Suceava | romsilva_map:exact |
| remezeu | uncontracted |  |  |
| siret | present | AVPS IAȘI |  |
| suceava | present | AJVPS BOTOȘANI | audit_match:exact |
| suceava river | uncontracted |  |  |
| vicov river | uncontracted |  |  |
| voitinel | uncontracted |  |  |
| бородач | uncontracted |  |  |
| брусниця | uncontracted |  |  |
| вільховець | uncontracted |  |  |
| глиниця | uncontracted |  |  |
| гоинець | uncontracted |  |  |
| дерелуи | uncontracted |  |  |
| дністер / nistru | uncontracted |  |  |
| кися | uncontracted |  |  |
| клокучка | uncontracted |  |  |
| коровія | uncontracted |  |  |
| лаура | uncontracted |  |  |
| личинець | uncontracted |  |  |
| малии сірет | uncontracted |  |  |
| михидра | uncontracted |  |  |
| мольниця | uncontracted |  |  |
| невільниця | uncontracted |  |  |
| пантін | uncontracted |  |  |
| прут | uncontracted |  |  |
| серетель | uncontracted |  |  |
| струмок клитештіи | uncontracted |  |  |
| сурдук | uncontracted |  |  |
| сірет | uncontracted |  |  |
| хрещовець | uncontracted |  |  |
| черемош | uncontracted |  |  |
| чудеи | uncontracted |  |  |
| яблунівець | uncontracted |  |  |
| єзерул | uncontracted |  |  |

### Celulă 47.9-48.4N, 26.0-26.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| baranca | present | AJVPS BOTOȘANI | audit_match:prefix |
| baseu | present | AJVPS BOTOȘANI |  |
| buhai | uncontracted |  |  |
| cotargaci | uncontracted |  |  |
| herta | uncontracted |  |  |
| jijia | present | AJVPS BOTOȘANI |  |
| molnita | present | AJVPS BOTOȘANI |  |
| morisca | uncontracted |  |  |
| paraul intors | uncontracted |  |  |
| prut | present | AVPS IAȘI |  |
| prut / прут | uncontracted |  |  |
| raul baseu | present | AJVPS BOTOȘANI |  |
| siret | present | AVPS IAȘI |  |
| баранка | uncontracted |  |  |
| виця | uncontracted |  |  |
| вледеску | uncontracted |  |  |
| влэдеску | uncontracted |  |  |
| герца | uncontracted |  |  |
| дерелуи | uncontracted |  |  |
| динівці | uncontracted |  |  |
| дністер / nistru | uncontracted |  |  |
| кися | uncontracted |  |  |
| коровія | uncontracted |  |  |
| котелеве | uncontracted |  |  |
| молниця | uncontracted |  |  |
| мольниця | uncontracted |  |  |
| невільниця | uncontracted |  |  |
| нирєу герца | uncontracted |  |  |
| паланка | uncontracted |  |  |
| прут | uncontracted |  |  |
| пурлупка | uncontracted |  |  |
| рингач | uncontracted |  |  |
| сірет | uncontracted |  |  |
| тестурічі | uncontracted |  |  |
| тирла циганілор | uncontracted |  |  |
| тирнаука | uncontracted |  |  |
| тырла цыганилор | uncontracted |  |  |
| тырнаука | uncontracted |  |  |

### Celulă 47.9-48.4N, 26.5-27.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| baseu | present | AJVPS BOTOȘANI |  |
| jijia | present | AJVPS BOTOȘANI |  |
| larga | uncontracted |  |  |
| morisca | uncontracted |  |  |
| prut | present | AVPS IAȘI |  |
| prut / прут | uncontracted |  |  |
| raul vilia вілія | uncontracted |  |  |
| vilia | uncontracted |  |  |
| глодос | uncontracted |  |  |
| дністер / nistru | uncontracted |  |  |

### Celulă 47.9-48.4N, 27.0-27.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| blesteni | uncontracted |  |  |
| bogda | uncontracted |  |  |
| camenca | uncontracted |  |  |
| ciuhur | uncontracted |  |  |
| draghiste | uncontracted |  |  |
| lopatnic | uncontracted |  |  |
| prut | present | AVPS IAȘI |  |
| prut / прут | uncontracted |  |  |
| racovat | uncontracted |  |  |
| дністер / nistru | uncontracted |  |  |

### Celulă 47.9-48.4N, 27.5-28.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| cainari | uncontracted |  |  |
| caldarusa | uncontracted |  |  |
| copaceanca | uncontracted |  |  |
| cubolta | uncontracted |  |  |
| raul cubolta | uncontracted |  |  |
| raut | uncontracted |  |  |
| дністер / nistru | uncontracted |  |  |

### Celulă 47.9-48.4N, 28.0-28.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| cainari | uncontracted |  |  |
| camenca | uncontracted |  |  |
| ciorna | uncontracted |  |  |
| cubolta | uncontracted |  |  |
| nistru днестр | uncontracted |  |  |
| raul cubolta | uncontracted |  |  |
| вільшанка | uncontracted |  |  |
| дністер / nistru | uncontracted |  |  |
| дністер nistru | uncontracted |  |  |
| коритна | uncontracted |  |  |
| марківка | uncontracted |  |  |
| мурафа | uncontracted |  |  |
| ольшанка | uncontracted |  |  |
| русава | uncontracted |  |  |
| яланка | uncontracted |  |  |

### Celulă 47.9-48.4N, 28.5-29.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| cusmirca | uncontracted |  |  |
| nistru днестр | uncontracted |  |  |
| ocnita / окниця / окница | uncontracted |  |  |
| белочи | uncontracted |  |  |
| белочи білоч | uncontracted |  |  |
| буряковая | uncontracted |  |  |
| білоч | uncontracted |  |  |
| вільшанка | uncontracted |  |  |
| глибока | uncontracted |  |  |
| глубокая | uncontracted |  |  |
| гнилая | uncontracted |  |  |
| дністер / nistru | uncontracted |  |  |
| дністер nistru | uncontracted |  |  |
| золотая | uncontracted |  |  |
| кам янка | uncontracted |  |  |
| каменка | uncontracted |  |  |
| каменка/кам янка | uncontracted |  |  |
| кисирняк | uncontracted |  |  |
| малина | uncontracted |  |  |
| марківка | uncontracted |  |  |
| одая | uncontracted |  |  |
| окница | uncontracted |  |  |
| окниця | uncontracted |  |  |
| саврань | uncontracted |  |  |
| хрустова | uncontracted |  |  |

### Celulă 47.9-48.4N, 29.0-29.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| белочи білоч | uncontracted |  |  |
| бритавка | uncontracted |  |  |
| білоч | uncontracted |  |  |
| кодима | uncontracted |  |  |
| мала савранка | uncontracted |  |  |
| молокиш | uncontracted |  |  |
| окна | uncontracted |  |  |
| рибниця | uncontracted |  |  |
| саврань | uncontracted |  |  |

### Celulă 47.9-48.4N, 29.5-30.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| зозулька | uncontracted |  |  |
| кодима | uncontracted |  |  |
| мала савранка | uncontracted |  |  |
| саврань | uncontracted |  |  |
| яланець | uncontracted |  |  |

### Celulă 48.4-48.9N, 20.0-20.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| blh | uncontracted |  |  |
| slana / sajo | uncontracted |  |  |
| teska | uncontracted |  |  |

### Celulă 48.4-48.9N, 20.5-21.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bodva | uncontracted |  |  |
| bodva / bodva | uncontracted |  |  |
| kupai vadasz patak | uncontracted |  |  |
| vadasz patak | uncontracted |  |  |

### Celulă 48.4-48.9N, 21.0-21.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| belus patak | uncontracted |  |  |
| hornad / hernad | uncontracted |  |  |
| tolcsva patak | uncontracted |  |  |

### Celulă 48.4-48.9N, 21.5-22.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| bodrog | uncontracted |  |  |
| hercegkuti patak | uncontracted |  |  |

### Celulă 48.4-48.9N, 22.0-22.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| csaronda csatorna | uncontracted |  |  |
| tisza | uncontracted |  |  |

### Celulă 48.4-48.9N, 23.0-23.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| боржава | uncontracted |  |  |
| рика | uncontracted |  |  |
| ріка | uncontracted |  |  |
| синявка | uncontracted |  |  |

### Celulă 48.4-48.9N, 23.5-24.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| рика | uncontracted |  |  |
| ріка | uncontracted |  |  |
| теребля | uncontracted |  |  |

### Celulă 48.4-48.9N, 24.0-24.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| турбат | uncontracted |  |  |

### Celulă 48.4-48.9N, 24.5-25.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| prut / прут | uncontracted |  |  |

### Celulă 48.4-48.9N, 25.0-25.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| prut / прут | uncontracted |  |  |
| дністер / nistru | uncontracted |  |  |
| пістинька | uncontracted |  |  |
| черемош | uncontracted |  |  |

### Celulă 48.4-48.9N, 25.5-26.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| prut / прут | uncontracted |  |  |
| дністер / nistru | uncontracted |  |  |
| черемош | uncontracted |  |  |

### Celulă 48.4-48.9N, 26.0-26.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| дністер / nistru | uncontracted |  |  |

### Celulă 48.4-48.9N, 26.5-27.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| raul vilia вілія | uncontracted |  |  |
| дністер / nistru | uncontracted |  |  |

### Celulă 48.4-48.9N, 27.0-27.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| дністер / nistru | uncontracted |  |  |

### Celulă 48.4-48.9N, 27.5-28.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| cubolta | uncontracted |  |  |
| дністер / nistru | uncontracted |  |  |

### Celulă 48.4-48.9N, 28.0-28.5E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| мурафа | uncontracted |  |  |
| русава | uncontracted |  |  |

### Celulă 48.4-48.9N, 28.5-29.0E
| Râu | Clasă | Asociație | Detalii |
|---|---|---|---|
| марківка | uncontracted |  |  |
| русава | uncontracted |  |  |

## Legenda claselor
- **present** — există în waters.json CU geometrie → click → card, curs desenat.
- **present-bbox** — există în waters.json, fără geometrie dar CU bbox → se afișează ca dreptunghi (aprox.), click → card.
- **present-hidden** — există în waters.json, fără geometrie ȘI fără bbox → INVIZIBIL pe hartă, deși e contractat → de reparat (bug de clasificare sau lipsă geometrie).
- **anpa-missing** — este în lista ANPA de contracte, dar LIPSEȘTE din waters.json → de adăugat (fixable).
- **areba-missing** — este în lista arebaltapeste.ro, dar LIPSEȘTE din waters.json → de adăugat (fixable).
- **romsilva** — administrat de RNP-Romsilva (listă ANPA separată); NU este contract AJVPS/APS → doar raportat.
- **uncontracted** — nu apare în nicio sursă contractată → doar raportat, NU se inventează contract.