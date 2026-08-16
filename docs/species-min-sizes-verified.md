# Species minimum retention sizes — verified dataset (data/species.json)

**Task:** t_561dc7e8 (parent spike t_a336bb75)
**Verified:** 2026-08-16
**Scope:** ~20 inland freshwater recreational species + fully-protected species, **newest official values** (as in force Aug 2026).
**Output:** `data/species.json` — array per task schema `[{species, latin, min_cm, source, seasonal_notes?, retention?, last_updated}]`.

---

## 1. Legal chain (what is actually in force in 2026)

| Layer | Instrument | Role |
|---|---|---|
| Framework law | **Legea nr. 176/2024** a pescuitului și a protecției resursei acvatice vii — MO 517/03.06.2024 | Repeals the OUG 23/2008 provisions on aquatic resources (art. 61) and, until new secondary legislation enters into force, keeps applying the existing norms (art. 60: „Până la intrarea în vigoare a noilor reglementări specifice legislației secundare se vor aplica normele prevăzute…”). |
| **Size table (operative)** | **Ordin MADR nr. 342/2008** — anexa „Dimensiunile minime, în centimetri, ale resurselor acvatice vii din domeniul public al statului, care pot fi capturate din mediul acvatic” — MO 410/02.06.2008 | 45 rows. **Last amended by Ordin 304/2023 (MO 785/31.08.2023): only crap 35→40 and caras 15→20.** Verified via the **consolidated form on legislatie.just.ro (istoric consolidări 31.08.2023)** — no 2024–2026 amendment exists. |
| Prohibition periods (applies to 2026) | **Ordin comun MADR/MMAP nr. 23/297/2025** — MO 95/01.02.2025, **consolidat la 27.10.2025** (ANPA-hosted consolidated PDF) | From 23/297/2025 the order is **no longer annual** — it stays in force until amended/abrogated, so its windows apply for 2026. Verified text of art. 1 and art. 5. |
| Issuing/control body 2026 | **ANADSPA** — Autoritatea Națională pentru Administrarea Domeniilor Statului, Pescuit și Acvacultură | ANPA dissolved by the MADR-reorganization OUG adopted 30.12.2025, published in MO 1225/31.12.2025 (per info-delta.ro update: OUG 92/2025): ANPA absorbed into ADS (fuziune prin absorbție); the resulting institution issues the permits and controls. The size table itself is set by ministerial order (MADR), so **the values did not change with the agency change**. |

**2026 changes:** (a) issuing/control body ANPA → **ANADSPA** (no value change); (b) minimum sizes **unchanged** since 31.08.2023; (c) prohibition windows carried from the 23/297/2025 order (incl. the **year-round bans on lipan, coregon, caracudă** and other strictly-protected species).

**Measurement rule (Ordin 342/2008, art. 3):** „Mărimea peștelui, stabilită pentru pescuit, este determinată prin măsurarea distanței de la vârful botului până la baza înotătoarei caudale.”

---

## 2. 🔴 Discrepancies — RESOLVED (quotes from official text)

All six flagged discrepancies from the spike (eDelta vs pescuit365) are resolved. **The official source is the consolidated annex to Ordin 342/2008 (as amended by 304/2023). The pescuit365 „2026” table values (somn 60, avat 40, clean 28, scobar 25, oblete „—”) have NO basis in the official text** — they match internet folklore, not Monitorul Oficial.

| Species | eDelta (342/2008+2023) | pescuit365 „2026” | **Official value** | Official quote / basis |
|---|---|---|---|---|
| **Somn** | 50 | 60 | **50 cm** | Anexa poz. 30: „Somn (Silurus glanis) 50”. Consolidated form (31.08.2023) shows no amendment. |
| **Avat** | 30 | 40 | **30 cm** | Anexa poz. 1: „Avat (Aspius aspius) 30”. |
| **Clean** | 25 | 28 | **25 cm** | Anexa poz. 10: „Clean (Leuciscus cephalus) 25”. |
| **Scobar** | 20 | 25 | **20 cm** | Anexa poz. 29: „Scobar (Chondostroma nasos) 20”. |
| **Lipan** | 25 | INTERZIS | **25 cm în anexă, dar reținerea INTERZISĂ tot anul** | Anexa poz. 19: „Lipan (Thymallus thymallus) 25” **AND** Ordin 23/297/2025 art. 5 lit. d: „coregonul și lipanul, tot timpul anului”. Both are true: the size survives in the annex, but **since 2025 the species is prohibited to fish year-round → de facto INTERZIS**. |
| **Oblete** | 12 | „—” | **12 cm** | Anexa poz. 22: „Oblete (Alburnus alburnus) 12”. Art. 4 of the order only exempts unlisted species; oblete IS listed. |

Extra finding (neither secondary source flags it): **Caracudă** (așa cum o tratează și eDelta ca legală la 17 cm) este **enumerată explicit la art. 5 lit. c din Ordin 23/297/2025** printre speciile cu pescuitul interzis „tot timpul anului” → în 2026 reținerea caracudei este interzisă, chiar dacă dimensiunea de 17 cm rămâne în anexă.

---

## 3. The 21 inland freshwater species (all verified)

Values from the consolidated annex of Ordin 342/2008 (poz. = row number in the annex); seasonal windows from Ordin 23/297/2025 (MO 95/01.02.2025, consolidat 27.10.2025).

| # | Species | Latin | min_cm | Anexă poz. | Prohibiție / notă |
|---|---|---|---|---|---|
| 1 | Avat | Aspius aspius | 30 | 1 | generală 9 apr–7 iun |
| 2 | Babușcă | Rutilus rutilus | 15 | 3 | generală 9 apr–7 iun |
| 3 | Biban | Perca fluviatilis | 12 | 5 | proprie 20 mar–7 iun |
| 4 | Crap | Cyprinus carpio | 40 | 6 | generală; RBDD catch&release 1 ex/zi |
| 5 | Caras | Carassius auratus gibelio | 20 | 7 | invaziv, fără prohibiție proprie |
| 6 | Caracudă | Carassius carassius | 17 | 8 | **interzis tot anul** (art. 5 lit. c) |
| 7 | Clean | Squalius cephalus | 25 | 10 | generală |
| 8 | Lin | Tinca tinca | 25 | 18 | generală |
| 9 | Lipan | Thymallus thymallus | 25 | 19 | **interzis tot anul** (art. 5 lit. d) |
| 10 | Morunaș | Vimba vimba | 25 | 20 | generală |
| 11 | Mreană | Barbus barbus | 27 | 21 | generală |
| 12 | Oblete | Alburnus alburnus | 12 | 22 | generală; momeală vie permisă |
| 13 | Plătică | Abramis brama | 25 | 23 | generală |
| 14 | Păstrăv indigen | Salmo trutta fario | 20 | 24 „Păstrăv (Salmo sp.)” | proprie 1 oct–31 mar |
| 15 | Păstrăv curcubeu | Oncorhynchus mykiss | 20 | 24 | proprie 1 oct–31 mar |
| 16 | Roșioară | Scardinius erythrophthalmus | 15 | 25 | generală |
| 17 | Scobar | Chondrostoma nasus | 20 | 29 | generală |
| 18 | Somn | Silurus glanis | 50 | 30 | generală; RBDD catch&release 1 ex/zi |
| 19 | Șalău | Sander lucioperca | 40 | 34 | proprie 20 mar–7 iun |
| 20 | Știucă | Esox lucius | 40 | 35 | proprie 1 feb–20 mar (RBDD 1 feb–7 iun) |
| 21 | Văduviță | Leuciscus idus | 30 | 37 | generală |

Prohibiția generală = art. 1 din Ordin 23/297/2025: 60 de zile, **9 aprilie–7 iunie** (ape de frontieră: 45 zile, 24 apr–7 iun; frontieră Ucraina/Golful Musura: 16 apr–30 mai).

## 4. Fully protected („interzis”) — separate entries in the JSON

| Species | Latin | Basis |
|---|---|---|
| Lostriță | Hucho hucho | Ordin 342/2008 art. 4 („cu excepția sturionilor și lostriței, care sunt interziși la pescuit”); Ordin 23/297/2025 art. 5 lit. c; Legea 176/2024 art. 51 lit. f |
| Asprete | Romanichthys valsanicola | Ordin 23/297/2025 art. 5 lit. c; OUG 57/2007 anexele 4A/4B |
| Morun | Huso huso | sturioni: moratoriu din 2006; art. 5 lit. g; Legea 176/2024 art. 51 lit. c |
| Nisetru | Acipenser gueldenstaedtii | same |
| Păstrugă | Acipenser stellatus | same |
| Cegă | Acipenser ruthenus | same |
| Șip | Acipenser nudiventris | same |
| Coregon | Coregonus sp. | anexă poz. 11 (22 cm) dar interzis tot anul (art. 5 lit. d) |

## 5. Explicitly NOT covered (out of scope / not verified here)

- **Prut / Stânca-Costești:** sizes there are set by **HG 1207/2003** (RO–MD agreement), not by the 342/2008 annex (Ordin 342/2008 art. 2) — flagged so the /specii page can add a caveat for that sector.
- **Daily bag limits** (5 kg/zi etc.): separate rule, not part of this dataset (the spike's `SPECIES_DAILY_LIMIT` string needs its own verification pass).
- **Marine / Delta-specific sizes** (ARBDD sector rules): out of the inland scope.

## 6. Sources (official first)

1. Ordin MADR 342/2008, MO 410/02.06.2008 — consolidated form on legislatie.just.ro: https://legislatie.just.ro/Public/DetaliiDocument/93564
2. Ordin MADR 304/2023, MO 785/31.08.2023: https://legislatie.just.ro/Public/DetaliiDocumentAfis/274112
3. Legea 176/2024, MO 517/03.06.2024: https://legislatie.just.ro/public/DetaliiDocument/283479
4. Ordin MADR/MMAP 23/297/2025, MO 95/01.02.2025: https://legislatie.just.ro/Public/DetaliiDocumentAfis/294196 + consolidated PDF (ANPA, consolidat la 27.10.2025): https://www.anpa.ro/wp-content/uploads/2011/05/ordin-23-297-2025-prohibitie-consolidat-la-27.10.2025.pdf
5. ANADSPA (ANPA→ADS): info-delta.ro „ANPA se desființează…” (31.12.2025, actualizat 01.01.2026) + monitoruldegalati.ro + pescuit365.ro/legislatie.html
6. Mirrors used for cross-check ONLY (values differed → rejected where they disagreed with the official text): edelta.ro (reproduces the annex correctly), pescuit365.ro „Dimensiuni legale pești 2026” (**unreliable — somn/avat/clean/scobar/oblete values have no official basis**).

**Re-verify cadence:** annually before the season + whenever MADR publishes a new „ordin de prohibiție” or a size-table amendment. `last_updated` per entry = 2026-08-16.
