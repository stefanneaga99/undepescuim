# Arhitectura curentă — UndePescuim.ro

Actualizat: 2026-08-18

Acest document descrie implementarea curentă. Fișierele din `docs/` care au
`plan`, `feasibility` sau `report` în nume sunt documente istorice de lucru și
pot descrie stări intermediare.

## Privire de ansamblu

UndePescuim.ro este o aplicație Next.js mobile-first pentru explorarea apelor de
pescuit din România. Interfața rulează în principal în browser, datele sunt
livrate ca JSON/GeoJSON static, iar raportarea problemelor folosește o singură
rută serverless care creează GitHub issues.

```text
browser
  ├─ Next.js App Router: /, /permis, /specii
  ├─ Leaflet + OpenStreetMap
  ├─ Zustand + filtre în URL
  ├─ JSON/GeoJSON din /public/data
  └─ POST /api/report
                 └─ GitHub Issues API

pipeline Python/Node
  └─ surse + geocodare + audituri
                 └─ /public/data
```

## Runtime și rute

- `src/app/page.tsx` oferă shell-ul server-rendered al hărții.
- `src/components/map/MapShell.tsx` încarcă datele și interfața client-side.
- `src/components/map/MapView.tsx` găzduiește harta Leaflet.
- `/permis` și `/specii` sunt pagini informative bilingve.
- `src/app/api/report/route.ts` validează cererile, aplică rate limiting și
  creează issues prin GitHub API.
- `src/app/sw.ts`, compilat de Serwist, furnizează suportul PWA.

Aplicația nu este static-exportată: ruta de raportare necesită runtime serverless.
Vercel publică automat ramura `main`.

## Strat de date

Datele livrate aplicației sunt în `public/data/`:

- `waters.json`: 1.013 ape contractate și metadatele lor;
- `associations.json`: 96 de asociații;
- `uncontracted_majors.json`: subsetul prioritar, preîncărcat;
- `uncontracted_rivers.json` și `uncontracted_lakes.json`: straturi complete,
  încărcate la nevoie;
- `waters_county_clips.json`: geometrii decupate pe județ;
- `counties.geojson` și `localities.geojson`: limite pentru filtre și atribuire.

Geometriile mari sunt simplificate în pipeline. Harta aplică viewport culling și
niveluri de detaliu dependente de zoom, astfel încât să nu monteze toate
feature-urile simultan.

Tipurile domeniului sunt în `src/types/data.ts`. Hook-urile din `src/hooks/`
încarcă și combină seturile de date, utilitarele din `src/utils/` rezolvă
geometriile, sectoarele și filtrele, iar `src/stores/map-store.ts` păstrează
starea hărții și o sincronizează cu URL-ul.

## Interfață și localizare

Interfața folosește Tailwind CSS, shadcn/ui și primitive Radix. Textele comune
sunt în `src/i18n/`, iar conținutul juridic și despre specii este în
`src/content/`. Schimbarea limbii se face client-side, fără prefix de rută.

Leaflet este încărcat exclusiv client-side. Tema este gestionată de
`next-themes`. Harta folosește tile-uri OpenStreetMap fără cheie API.

## PWA și cache

Serwist compilează `src/app/sw.ts` în `public/sw.js` la build. Shell-ul este
precache-uit, iar fișierele de date folosesc cache runtime; seturile mari nu sunt
incluse în precache. `sw.js` este servit cu `Cache-Control: no-cache`, în timp ce
asset-urile Next primesc cache immutable, iar datele au cache de 24 de ore.

## Pipeline și automatizare

`npm run data:refresh` orchestrează regenerarea datelor. Scripturile Python și
Node din `scripts/` acoperă geocodarea, asocierea cu județe/localități,
simplificarea geometriei, trasabilitatea și verificările de integritate.

GitHub Actions rulează:

- unit tests și coverage pentru TypeScript;
- pytest pentru pipeline;
- Playwright pentru fluxuri UI și contracte cu date reale;
- audituri de integritate, securitate și URL-uri;
- bugete de payload, Lighthouse și urme de performanță;
- refresh lunar al datelor.

## Configurare

Singurul secret necesar aplicației este `REPORT_GITHUB_TOKEN`, utilizat exclusiv
server-side de `/api/report`. Build-urile de analiză pot seta `ANALYZE=true`, iar
scriptul de performanță acceptă `BASE_URL`, `PLAYWRIGHT_CDP` și
`PERF_THROTTLE`.

Headerele de securitate sunt definite în `next.config.ts`, iar regulile de cache
specifice Vercel sunt oglindite în `vercel.json`.

## Principii de modificare

- Schimbările de logică sau pipeline trebuie să includă teste, conform
  `AGENTS.md`.
- Fișierele generate (`public/sw.js`, `public/data/meta.json` și intermediarii
  de geocodare) nu se editează manual.
- `public/data/` este contractul dintre pipeline și frontend; orice schimbare de
  schemă trebuie actualizată în tipuri, teste și consumatori.
- Nu se activează `output: "export"` cât timp raportarea GitHub rămâne activă.
