# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: flows/nav.spec.ts >> F12 — logo returns home >> clicking the logo from /specii goes back to the map
- Location: tests/e2e/specs/flows/nav.spec.ts:66:7

# Error details

```
Test timeout of 60000ms exceeded.
```

```
Error: locator.click: Test timeout of 60000ms exceeded.
Call log:
  - waiting for getByRole('link', { name: /UndePescuim/ })

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - main [ref=e2]:
    - link "Înapoi la hartă" [ref=e3] [cursor=pointer]:
      - /url: /
    - heading "Dimensiuni minime de reținere, pe specii" [level=1] [ref=e6]
    - paragraph [ref=e7]: "Ultima verificare a faptelor: 2026-08-16. Informațiile se pot schimba anual prin ordin de ministru — verifică sursele oficiale (linkuri la finalul paginii) înainte de o decizie. Conținut sensibil la timp: se re-verifică trimestrial."
    - generic [ref=e8]:
      - paragraph [ref=e9]: Valori naționale
      - paragraph [ref=e10]:
        - text: Dimensiunile de mai jos sunt minimele legale naționale. Bălțile private sau asociațiile pot impune limite
        - strong [ref=e11]: mai mari, niciodată mai mici
        - text: . În Delta Dunării (ARBDD) regimul poate diferi.
    - button "Caută o specie" [ref=e14]:
      - generic [ref=e18]: Caută o specie…
    - generic [ref=e21]:
      - heading "Specii cu dimensiune minimă (19)" [level=2] [ref=e22]
      - generic [ref=e29]:
        - generic [ref=e30]:
          - generic [ref=e32]:
            - paragraph [ref=e33]: Avat
            - paragraph [ref=e34]: Aspius aspius
          - generic [ref=e35]:
            - generic [ref=e36]: 30cm
            - generic [ref=e37]: dimensiune minimă de reținere
          - paragraph [ref=e38]: "Prohibiție generală: 9 apr–7 iun (Ordin MADR/MMAP 23/297/2025, MO 95/01.02.2025, consolidat 27.10.2025)"
          - paragraph [ref=e43]: "Sursă: Ordin MADR 342/2008, anexa poz. 1 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023) · verificat 2026-08-16"
        - generic [ref=e44]:
          - generic [ref=e46]:
            - paragraph [ref=e47]: Babușcă
            - paragraph [ref=e48]: Rutilus rutilus
          - generic [ref=e49]:
            - generic [ref=e50]: 15cm
            - generic [ref=e51]: dimensiune minimă de reținere
          - paragraph [ref=e52]: "Prohibiție generală: 9 apr–7 iun (Ordin MADR/MMAP 23/297/2025, MO 95/01.02.2025)"
          - paragraph [ref=e57]: "Sursă: Ordin MADR 342/2008, anexa poz. 3 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023) · verificat 2026-08-16"
        - generic [ref=e58]:
          - generic [ref=e60]:
            - paragraph [ref=e61]: Biban
            - paragraph [ref=e62]: Perca fluviatilis
          - generic [ref=e63]:
            - generic [ref=e64]: 12cm
            - generic [ref=e65]: dimensiune minimă de reținere
          - paragraph [ref=e66]: "Prohibiție proprie: 20 mar–7 iun (Ordin MADR/MMAP 23/297/2025, MO 95/01.02.2025)"
          - paragraph [ref=e71]: "Sursă: Ordin MADR 342/2008, anexa poz. 5 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023) · verificat 2026-08-16"
        - generic [ref=e72]:
          - generic [ref=e74]:
            - paragraph [ref=e75]: Crap
            - paragraph [ref=e76]: Cyprinus carpio
          - generic [ref=e77]:
            - generic [ref=e78]: 40cm
            - generic [ref=e79]: dimensiune minimă de reținere
          - paragraph [ref=e80]: "Prohibiție generală: 9 apr–7 iun; în Rezervația Delta Dunării, în afara prohibiției, doar catch&release (1 ex/zi) (Ordin MADR/MMAP 23/297/2025, MO 95/01.02.2025)"
          - paragraph [ref=e85]: "Sursă: Ordin MADR 342/2008, anexa poz. 6 (MO 410/02.06.2008), modificat prin Ordin 304/2023 (MO 785/31.08.2023): 35→40 cm · verificat 2026-08-16"
        - generic [ref=e86]:
          - generic [ref=e88]:
            - paragraph [ref=e89]: Caras
            - paragraph [ref=e90]: Carassius auratus gibelio
          - generic [ref=e91]:
            - generic [ref=e92]: 20cm
            - generic [ref=e93]: dimensiune minimă de reținere
          - paragraph [ref=e94]: "Specie invazivă; fără prohibiție proprie, dar se aplică prohibiția generală: 9 apr–7 iun"
          - paragraph [ref=e99]: "Sursă: Ordin MADR 342/2008, anexa poz. 7 (MO 410/02.06.2008), modificat prin Ordin 304/2023 (MO 785/31.08.2023): 15→20 cm · verificat 2026-08-16"
        - generic [ref=e100]:
          - generic [ref=e102]:
            - paragraph [ref=e103]: Clean
            - paragraph [ref=e104]: Squalius cephalus (Leuciscus cephalus)
          - generic [ref=e105]:
            - generic [ref=e106]: 25cm
            - generic [ref=e107]: dimensiune minimă de reținere
          - paragraph [ref=e108]: "Prohibiție generală: 9 apr–7 iun (Ordin MADR/MMAP 23/297/2025, MO 95/01.02.2025)"
          - paragraph [ref=e113]: "Sursă: Ordin MADR 342/2008, anexa poz. 10 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023) · verificat 2026-08-16"
        - generic [ref=e114]:
          - generic [ref=e116]:
            - paragraph [ref=e117]: Lin
            - paragraph [ref=e118]: Tinca tinca
          - generic [ref=e119]:
            - generic [ref=e120]: 25cm
            - generic [ref=e121]: dimensiune minimă de reținere
          - paragraph [ref=e122]: "Prohibiție generală: 9 apr–7 iun (Ordin MADR/MMAP 23/297/2025, MO 95/01.02.2025)"
          - paragraph [ref=e127]: "Sursă: Ordin MADR 342/2008, anexa poz. 18 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023) · verificat 2026-08-16"
        - generic [ref=e128]:
          - generic [ref=e130]:
            - paragraph [ref=e131]: Morunaș
            - paragraph [ref=e132]: Vimba vimba
          - generic [ref=e133]:
            - generic [ref=e134]: 25cm
            - generic [ref=e135]: dimensiune minimă de reținere
          - paragraph [ref=e136]: "Prohibiție generală: 9 apr–7 iun (Ordin MADR/MMAP 23/297/2025, MO 95/01.02.2025)"
          - paragraph [ref=e141]: "Sursă: Ordin MADR 342/2008, anexa poz. 20 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023) · verificat 2026-08-16"
        - generic [ref=e142]:
          - generic [ref=e144]:
            - paragraph [ref=e145]: Mreană
            - paragraph [ref=e146]: Barbus barbus
          - generic [ref=e147]:
            - generic [ref=e148]: 27cm
            - generic [ref=e149]: dimensiune minimă de reținere
          - paragraph [ref=e150]: "Prohibiție generală: 9 apr–7 iun (Ordin MADR/MMAP 23/297/2025, MO 95/01.02.2025)"
          - paragraph [ref=e155]: "Sursă: Ordin MADR 342/2008, anexa poz. 21 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023) · verificat 2026-08-16"
        - generic [ref=e156]:
          - generic [ref=e158]:
            - paragraph [ref=e159]: Oblete
            - paragraph [ref=e160]: Alburnus alburnus
          - generic [ref=e161]:
            - generic [ref=e162]: 12cm
            - generic [ref=e163]: dimensiune minimă de reținere
          - paragraph [ref=e164]: "Fără prohibiție proprie; se aplică prohibiția generală: 9 apr–7 iun. Este permis ca momeală vie, dar dimensiunea minimă de 12 cm se aplică reținerii"
          - paragraph [ref=e169]: "Sursă: Ordin MADR 342/2008, anexa poz. 22 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023) · verificat 2026-08-16"
        - generic [ref=e170]:
          - generic [ref=e172]:
            - paragraph [ref=e173]: Plătică
            - paragraph [ref=e174]: Abramis brama
          - generic [ref=e175]:
            - generic [ref=e176]: 25cm
            - generic [ref=e177]: dimensiune minimă de reținere
          - paragraph [ref=e178]: "Prohibiție generală: 9 apr–7 iun (Ordin MADR/MMAP 23/297/2025, MO 95/01.02.2025)"
          - paragraph [ref=e183]: "Sursă: Ordin MADR 342/2008, anexa poz. 23 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023) · verificat 2026-08-16"
        - generic [ref=e184]:
          - generic [ref=e186]:
            - paragraph [ref=e187]: Păstrăv indigen
            - paragraph [ref=e188]: Salmo trutta fario
          - generic [ref=e189]:
            - generic [ref=e190]: 20cm
            - generic [ref=e191]: dimensiune minimă de reținere
          - paragraph [ref=e192]: "Prohibiție proprie: 1 oct–31 mar (Ordin MADR/MMAP 23/297/2025, MO 95/01.02.2025)"
          - paragraph [ref=e197]: "Sursă: Ordin MADR 342/2008, anexa poz. 24 „Păstrăv (Salmo sp.)” (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023) · verificat 2026-08-16"
        - generic [ref=e198]:
          - generic [ref=e200]:
            - paragraph [ref=e201]: Păstrăv curcubeu
            - paragraph [ref=e202]: Oncorhynchus mykiss
          - generic [ref=e203]:
            - generic [ref=e204]: 20cm
            - generic [ref=e205]: dimensiune minimă de reținere
          - paragraph [ref=e206]: "Prohibiție proprie: 1 oct–31 mar (Ordin MADR/MMAP 23/297/2025, MO 95/01.02.2025)"
          - paragraph [ref=e211]: "Sursă: Ordin MADR 342/2008, anexa poz. 24 „Păstrăv (Salmo sp.)” (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023) · verificat 2026-08-16"
        - generic [ref=e212]:
          - generic [ref=e214]:
            - paragraph [ref=e215]: Roșioară
            - paragraph [ref=e216]: Scardinius erythrophthalmus
          - generic [ref=e217]:
            - generic [ref=e218]: 15cm
            - generic [ref=e219]: dimensiune minimă de reținere
          - paragraph [ref=e220]: "Prohibiție generală: 9 apr–7 iun (Ordin MADR/MMAP 23/297/2025, MO 95/01.02.2025)"
          - paragraph [ref=e225]: "Sursă: Ordin MADR 342/2008, anexa poz. 25 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023) · verificat 2026-08-16"
        - generic [ref=e226]:
          - generic [ref=e228]:
            - paragraph [ref=e229]: Scobar
            - paragraph [ref=e230]: Chondrostoma nasus
          - generic [ref=e231]:
            - generic [ref=e232]: 20cm
            - generic [ref=e233]: dimensiune minimă de reținere
          - paragraph [ref=e234]: "Prohibiție generală: 9 apr–7 iun (Ordin MADR/MMAP 23/297/2025, MO 95/01.02.2025)"
          - paragraph [ref=e239]: "Sursă: Ordin MADR 342/2008, anexa poz. 29 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023) · verificat 2026-08-16"
        - generic [ref=e240]:
          - generic [ref=e242]:
            - paragraph [ref=e243]: Somn
            - paragraph [ref=e244]: Silurus glanis
          - generic [ref=e245]:
            - generic [ref=e246]: 50cm
            - generic [ref=e247]: dimensiune minimă de reținere
          - paragraph [ref=e248]: "Prohibiție generală: 9 apr–7 iun; în Rezervația Delta Dunării, în afara prohibiției, doar catch&release (1 ex/zi) (Ordin MADR/MMAP 23/297/2025, MO 95/01.02.2025)"
          - paragraph [ref=e253]: "Sursă: Ordin MADR 342/2008, anexa poz. 30 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023) · verificat 2026-08-16"
        - generic [ref=e254]:
          - generic [ref=e256]:
            - paragraph [ref=e257]: Șalău
            - paragraph [ref=e258]: Sander lucioperca
          - generic [ref=e259]:
            - generic [ref=e260]: 40cm
            - generic [ref=e261]: dimensiune minimă de reținere
          - paragraph [ref=e262]: "Prohibiție proprie: 20 mar–7 iun (Ordin MADR/MMAP 23/297/2025, MO 95/01.02.2025)"
          - paragraph [ref=e267]: "Sursă: Ordin MADR 342/2008, anexa poz. 34 „Șalău (Stizostedion sp.)” (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023) · verificat 2026-08-16"
        - generic [ref=e268]:
          - generic [ref=e270]:
            - paragraph [ref=e271]: Știucă
            - paragraph [ref=e272]: Esox lucius
          - generic [ref=e273]:
            - generic [ref=e274]: 40cm
            - generic [ref=e275]: dimensiune minimă de reținere
          - paragraph [ref=e276]: "Prohibiție proprie: 1 feb–20 mar (în RBDD: 1 feb–7 iun) + prohibiție generală 9 apr–7 iun (Ordin MADR/MMAP 23/297/2025, MO 95/01.02.2025)"
          - paragraph [ref=e281]: "Sursă: Ordin MADR 342/2008, anexa poz. 35 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023) · verificat 2026-08-16"
        - generic [ref=e282]:
          - generic [ref=e284]:
            - paragraph [ref=e285]: Văduviță
            - paragraph [ref=e286]: Leuciscus idus
          - generic [ref=e287]:
            - generic [ref=e288]: 30cm
            - generic [ref=e289]: dimensiune minimă de reținere
          - paragraph [ref=e290]: "Prohibiție generală: 9 apr–7 iun (Ordin MADR/MMAP 23/297/2025, MO 95/01.02.2025)"
          - paragraph [ref=e295]: "Sursă: Ordin MADR 342/2008, anexa poz. 37 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023) · verificat 2026-08-16"
    - generic [ref=e296]:
      - heading "Protejate / interzise / neconfirmate (10)" [level=2] [ref=e297]
      - generic [ref=e301]:
        - generic [ref=e302]:
          - generic [ref=e303]:
            - generic [ref=e304]:
              - paragraph [ref=e305]: Caracudă
              - paragraph [ref=e306]: Carassius carassius
            - generic [ref=e307]: Interzis
          - generic [ref=e311]: Reținerea este interzisă.
          - paragraph [ref=e313]: "REȚINERE INTERZISĂ tot anul — enumerată explicit la art. 5 lit. c din Ordin MADR/MMAP 23/297/2025 (MO 95/01.02.2025, consolidat 27.10.2025): „...și caracuda (Carassius carassius)... tot timpul anului”. Dimensiunea din anexă (17 cm) rămâne în vigoare dar nu poate fi reținută în 2026"
          - paragraph [ref=e318]: "Sursă: Ordin MADR 342/2008, anexa poz. 8 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023) · verificat 2026-08-16"
        - generic [ref=e319]:
          - generic [ref=e320]:
            - generic [ref=e321]:
              - paragraph [ref=e322]: Lipan
              - paragraph [ref=e323]: Thymallus thymallus
            - generic [ref=e324]: Interzis
          - generic [ref=e328]: Reținerea este interzisă.
          - paragraph [ref=e330]: "REȚINERE INTERZISĂ tot anul — art. 5 lit. d din Ordin MADR/MMAP 23/297/2025 (MO 95/01.02.2025, consolidat 27.10.2025): „coregonul și lipanul, tot timpul anului”. Dimensiunea din anexă (25 cm) rămâne în vigoare, dar pescuitul/reținerea sunt interzise tot anul începând cu 2025"
          - paragraph [ref=e335]: "Sursă: Ordin MADR 342/2008, anexa poz. 19 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023) · verificat 2026-08-16"
        - generic [ref=e336]:
          - generic [ref=e337]:
            - generic [ref=e338]:
              - paragraph [ref=e339]: Coregon
              - paragraph [ref=e340]: Coregonus sp.
            - generic [ref=e341]: Interzis
          - generic [ref=e345]: Reținerea este interzisă.
          - paragraph [ref=e347]: "REȚINERE INTERZISĂ tot anul — art. 5 lit. d din Ordin MADR/MMAP 23/297/2025 (MO 95/01.02.2025): „coregonul și lipanul, tot timpul anului” Dimensiunea din anexă (22 cm) rămâne în vigoare, dar reținerea este interzisă tot anul."
          - paragraph [ref=e352]: "Sursă: Ordin MADR 342/2008, anexa poz. 11 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023) · verificat 2026-08-16"
        - generic [ref=e353]:
          - generic [ref=e354]:
            - generic [ref=e355]:
              - paragraph [ref=e356]: Lostriță
              - paragraph [ref=e357]: Hucho hucho
            - generic [ref=e358]: Interzis
          - generic [ref=e362]: Reținerea este interzisă.
          - paragraph [ref=e364]: Pescuitul, deținerea, transportul, comercializarea sau omorârea lostriței interzise (Legea 176/2024, art. 51 lit. f)
          - paragraph [ref=e369]: "Sursă: Ordin MADR 342/2008, art. 4 (MO 410/02.06.2008): „cu excepția sturionilor și lostriței, care sunt interziși la pescuit”; art. 5 lit. c din Ordin MADR/MMAP 23/297/2025 (MO 95/01.02.2025); art. 51 lit. f din Legea 176/2024 (MO 517/03.06.2024) · verificat 2026-08-16"
        - generic [ref=e370]:
          - generic [ref=e371]:
            - generic [ref=e372]:
              - paragraph [ref=e373]: Asprete
              - paragraph [ref=e374]: Romanichthys valsanicola
            - generic [ref=e375]: Interzis
          - generic [ref=e379]: Reținerea este interzisă.
          - paragraph [ref=e381]: Specie strict protejată, pescuit interzis tot timpul anului
          - paragraph [ref=e386]: "Sursă: Ordin MADR/MMAP 23/297/2025, art. 5 lit. c (MO 95/01.02.2025) + OUG 57/2007, anexele 4A/4B · verificat 2026-08-16"
        - generic [ref=e387]:
          - generic [ref=e388]:
            - generic [ref=e389]:
              - paragraph [ref=e390]: Morun
              - paragraph [ref=e391]: Huso huso
            - generic [ref=e392]: Interzis
          - generic [ref=e396]: Reținerea este interzisă.
          - paragraph [ref=e398]: Moratoriu privind sturionii din 2006, prelungit; pescuitul sturionilor sălbatici interzis tot anul
          - paragraph [ref=e403]: "Sursă: Ordin MADR 342/2008, art. 4 (MO 410/02.06.2008) — sturioni interziși la pescuit; art. 5 lit. g din Ordin MADR/MMAP 23/297/2025 (MO 95/01.02.2025); Legea 176/2024, art. 51 lit. c (MO 517/03.06.2024) · verificat 2026-08-16"
        - generic [ref=e404]:
          - generic [ref=e405]:
            - generic [ref=e406]:
              - paragraph [ref=e407]: Nisetru
              - paragraph [ref=e408]: Acipenser gueldenstaedtii
            - generic [ref=e409]: Interzis
          - generic [ref=e413]: Reținerea este interzisă.
          - paragraph [ref=e415]: Moratoriu privind sturionii din 2006, prelungit; pescuitul sturionilor sălbatici interzis tot anul
          - paragraph [ref=e420]: "Sursă: Ordin MADR 342/2008, art. 4 (MO 410/02.06.2008) — sturioni interziși la pescuit; art. 5 lit. g din Ordin MADR/MMAP 23/297/2025 (MO 95/01.02.2025); Legea 176/2024, art. 51 lit. c (MO 517/03.06.2024) · verificat 2026-08-16"
        - generic [ref=e421]:
          - generic [ref=e422]:
            - generic [ref=e423]:
              - paragraph [ref=e424]: Păstrugă
              - paragraph [ref=e425]: Acipenser stellatus
            - generic [ref=e426]: Interzis
          - generic [ref=e430]: Reținerea este interzisă.
          - paragraph [ref=e432]: Moratoriu privind sturionii din 2006, prelungit; pescuitul sturionilor sălbatici interzis tot anul
          - paragraph [ref=e437]: "Sursă: Ordin MADR 342/2008, art. 4 (MO 410/02.06.2008) — sturioni interziși la pescuit; art. 5 lit. g din Ordin MADR/MMAP 23/297/2025 (MO 95/01.02.2025); Legea 176/2024, art. 51 lit. c (MO 517/03.06.2024) · verificat 2026-08-16"
        - generic [ref=e438]:
          - generic [ref=e439]:
            - generic [ref=e440]:
              - paragraph [ref=e441]: Cegă
              - paragraph [ref=e442]: Acipenser ruthenus
            - generic [ref=e443]: Interzis
          - generic [ref=e447]: Reținerea este interzisă.
          - paragraph [ref=e449]: Moratoriu privind sturionii din 2006, prelungit; pescuitul sturionilor sălbatici interzis tot anul
          - paragraph [ref=e454]: "Sursă: Ordin MADR 342/2008, art. 4 (MO 410/02.06.2008) — sturioni interziși la pescuit; art. 5 lit. g din Ordin MADR/MMAP 23/297/2025 (MO 95/01.02.2025); Legea 176/2024, art. 51 lit. c (MO 517/03.06.2024) · verificat 2026-08-16"
        - generic [ref=e455]:
          - generic [ref=e456]:
            - generic [ref=e457]:
              - paragraph [ref=e458]: Șip
              - paragraph [ref=e459]: Acipenser nudiventris
            - generic [ref=e460]: Interzis
          - generic [ref=e464]: Reținerea este interzisă.
          - paragraph [ref=e466]: Moratoriu privind sturionii din 2006, prelungit; pescuitul sturionilor sălbatici interzis tot anul
          - paragraph [ref=e471]: "Sursă: Ordin MADR 342/2008, art. 4 (MO 410/02.06.2008) — sturioni interziși la pescuit; art. 5 lit. g din Ordin MADR/MMAP 23/297/2025 (MO 95/01.02.2025); Legea 176/2024, art. 51 lit. c (MO 517/03.06.2024) · verificat 2026-08-16"
    - generic [ref=e472]:
      - paragraph [ref=e473]: Limita generală de captură
      - paragraph [ref=e480]: "Captura maximă reținută: maximum 5 kg/zi, sau un singur pește dacă depășește 5 kg."
    - paragraph [ref=e481]:
      - text: Mai multe reguli (permis, unelte, capcane) sunt pe pagina
      - link "Permis & Reguli 2026" [ref=e485] [cursor=pointer]:
        - /url: /permis
      - text: .
    - generic [ref=e486]:
      - heading "Surse" [level=2] [ref=e487]
      - paragraph [ref=e492]: "Valorile din tabel au fost verificate față de sursele oficiale (data verificării: 2026-08-16). Re-verifică-le trimestrial — conținutul este sensibil la timp."
      - list [ref=e493]:
        - listitem [ref=e494]: "Valorile din tabel: Ordin MADR 342/2008, anexa poz. 1 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023)"
        - listitem [ref=e495]: "Valorile din tabel: Ordin MADR 342/2008, anexa poz. 3 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023)"
        - listitem [ref=e496]: "Valorile din tabel: Ordin MADR 342/2008, anexa poz. 5 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023)"
        - listitem [ref=e497]: "Valorile din tabel: Ordin MADR 342/2008, anexa poz. 6 (MO 410/02.06.2008), modificat prin Ordin 304/2023 (MO 785/31.08.2023): 35→40 cm"
        - listitem [ref=e498]: "Valorile din tabel: Ordin MADR 342/2008, anexa poz. 7 (MO 410/02.06.2008), modificat prin Ordin 304/2023 (MO 785/31.08.2023): 15→20 cm"
        - listitem [ref=e499]: "Valorile din tabel: Ordin MADR 342/2008, anexa poz. 8 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023)"
        - listitem [ref=e500]: "Valorile din tabel: Ordin MADR 342/2008, anexa poz. 10 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023)"
        - listitem [ref=e501]: "Valorile din tabel: Ordin MADR 342/2008, anexa poz. 18 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023)"
        - listitem [ref=e502]: "Valorile din tabel: Ordin MADR 342/2008, anexa poz. 19 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023)"
        - listitem [ref=e503]: "Valorile din tabel: Ordin MADR 342/2008, anexa poz. 20 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023)"
        - listitem [ref=e504]: "Valorile din tabel: Ordin MADR 342/2008, anexa poz. 21 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023)"
        - listitem [ref=e505]: "Valorile din tabel: Ordin MADR 342/2008, anexa poz. 22 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023)"
        - listitem [ref=e506]: "Valorile din tabel: Ordin MADR 342/2008, anexa poz. 23 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023)"
        - listitem [ref=e507]: "Valorile din tabel: Ordin MADR 342/2008, anexa poz. 24 „Păstrăv (Salmo sp.)” (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023)"
        - listitem [ref=e508]: "Valorile din tabel: Ordin MADR 342/2008, anexa poz. 25 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023)"
        - listitem [ref=e509]: "Valorile din tabel: Ordin MADR 342/2008, anexa poz. 29 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023)"
        - listitem [ref=e510]: "Valorile din tabel: Ordin MADR 342/2008, anexa poz. 30 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023)"
        - listitem [ref=e511]: "Valorile din tabel: Ordin MADR 342/2008, anexa poz. 34 „Șalău (Stizostedion sp.)” (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023)"
        - listitem [ref=e512]: "Valorile din tabel: Ordin MADR 342/2008, anexa poz. 35 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023)"
        - listitem [ref=e513]: "Valorile din tabel: Ordin MADR 342/2008, anexa poz. 37 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023)"
        - listitem [ref=e514]: "Valorile din tabel: Ordin MADR 342/2008, anexa poz. 11 (MO 410/02.06.2008); valoare nemodificată prin Ordin 304/2023 (MO 785/31.08.2023)"
        - listitem [ref=e515]: "Valorile din tabel: Ordin MADR 342/2008, art. 4 (MO 410/02.06.2008): „cu excepția sturionilor și lostriței, care sunt interziși la pescuit”; art. 5 lit. c din Ordin MADR/MMAP 23/297/2025 (MO 95/01.02.2025); art. 51 lit. f din Legea 176/2024 (MO 517/03.06.2024)"
        - listitem [ref=e516]: "Valorile din tabel: Ordin MADR/MMAP 23/297/2025, art. 5 lit. c (MO 95/01.02.2025) + OUG 57/2007, anexele 4A/4B"
        - listitem [ref=e517]: "Valorile din tabel: Ordin MADR 342/2008, art. 4 (MO 410/02.06.2008) — sturioni interziși la pescuit; art. 5 lit. g din Ordin MADR/MMAP 23/297/2025 (MO 95/01.02.2025); Legea 176/2024, art. 51 lit. c (MO 517/03.06.2024)"
      - list [ref=e518]:
        - listitem [ref=e519]:
          - link "Legea nr. 176/2024 a pescuitului și protecției resursei acvatice vii Legea-cadru; deleagă tabelul dimensiunilor minime către ordin de ministru." [ref=e520] [cursor=pointer]:
            - /url: https://legislatie.just.ro/public/DetaliiDocument/283479
            - generic [ref=e525]:
              - text: Legea nr. 176/2024 a pescuitului și protecției resursei acvatice vii
              - generic [ref=e526]: Legea-cadru; deleagă tabelul dimensiunilor minime către ordin de ministru.
        - listitem [ref=e527]:
          - link "Ordin nr. 23/297/2025 — perioadele de prohibiție Perioade anuale de prohibiție pe specii/zone (știucă, șalău etc.)." [ref=e528] [cursor=pointer]:
            - /url: https://legislatie.just.ro/Public/DetaliiDocumentAfis/294196
            - generic [ref=e533]:
              - text: Ordin nr. 23/297/2025 — perioadele de prohibiție
              - generic [ref=e534]: Perioade anuale de prohibiție pe specii/zone (știucă, șalău etc.).
    - paragraph [ref=e535]: "Ultima verificare a faptelor: 2026-08-16. Conținutul se re-verifică trimestrial (Monitorul Oficial, ANADSPA)."
  - alert [ref=e536]
```

# Test source

```ts
  1  | /**
  2  |  * POM — header nav (logo, inline links, mobile hamburger sheet).
  3  |  * Docs/e2e-test-plan.md §4.3. Selectors are data-testid only.
  4  |  */
  5  | import type { Page } from '@playwright/test';
  6  | import { Selectors } from '../helpers/selectors';
  7  | 
  8  | export class Header {
  9  |   constructor(private readonly page: Page) {}
  10 | 
  11 |   get logo() {
  12 |     return this.page.getByRole('link', { name: /UndePescuim/ });
  13 |   }
  14 | 
  15 |   get navSpecii() {
  16 |     return this.page.getByTestId(Selectors.navSpecii);
  17 |   }
  18 | 
  19 |   get navPermis() {
  20 |     return this.page.getByTestId(Selectors.navPermis);
  21 |   }
  22 | 
  23 |   get hamburger() {
  24 |     return this.page.getByTestId(Selectors.hamburger);
  25 |   }
  26 | 
  27 |   get sheetSpeciiLink() {
  28 |     return this.page.getByTestId(Selectors.navSheetSpecii);
  29 |   }
  30 | 
  31 |   get sheetPermisLink() {
  32 |     return this.page.getByTestId(Selectors.navSheetPermis);
  33 |   }
  34 | 
  35 |   /** Open the mobile hamburger menu; no-op on desktop (button hidden). */
  36 |   async openMenu(): Promise<void> {
  37 |     await this.hamburger.click();
  38 |   }
  39 | 
  40 |   /** Navigate home via the logo. */
  41 |   async goHome(): Promise<void> {
> 42 |     await this.logo.click();
     |                     ^ Error: locator.click: Test timeout of 60000ms exceeded.
  43 |   }
  44 | }
```