# UndePescuim.ro

Hartă interactivă a apelor de pescuit din România, cu informații despre ape
contractate și necontractate, asociații, permise și reguli.

Aplicația este disponibilă la [undepescuim.vercel.app](https://undepescuim.vercel.app)
și este publicată automat de Vercel la fiecare push pe `main`.

## Funcționalități

- hartă Leaflet/OpenStreetMap cu geometrii reale pentru râuri și lacuri;
- ape contractate și necontractate, cu nivel de detaliu adaptat zoom-ului și
  randare limitată la viewport;
- filtre după județ, localitate, tip de apă și statut contractual;
- căutare și detalii pentru asociațiile de pescuit;
- localizare și listă de ape din apropiere;
- ghid bilingv română/engleză pentru permise și reguli (`/permis`);
- dimensiuni minime și perioade de prohibiție pe specii (`/specii`);
- raportarea problemelor de date direct ca GitHub issues;
- mod luminos/întunecat și suport PWA cu cache offline pentru shell și date.

## Tehnologii

- Next.js 16 (App Router), React 19 și TypeScript;
- Leaflet și React Leaflet pentru hartă;
- Tailwind CSS 4 și componente shadcn/ui/Radix;
- Zustand pentru starea clientului;
- Serwist pentru service worker și PWA;
- Vitest, Playwright și pytest pentru testare;
- Vercel pentru hosting și funcția serverless de raportare.

Arhitectura curentă este descrisă în
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). Documentele cu `plan`,
`feasibility` sau `report` în nume păstrează contextul și deciziile de la
momentul implementării și nu reprezintă neapărat starea curentă.

## Dezvoltare locală

Cerințe:

- Node.js 22 recomandat (CI folosește Node.js 22 pentru testele unitare);
- npm, folosind lockfile-ul inclus;
- Python 3.12 și un mediu virtual pentru testele pipeline-ului de date.

```bash
npm ci
npm run dev
```

Deschide [http://localhost:3000](http://localhost:3000). Pagina principală
este în `src/app/page.tsx`.

Comenzi uzuale:

```bash
npm run lint             # ESLint
npm test                 # teste unitare TypeScript
npm run test:coverage    # teste + praguri de coverage
npm run build            # build de producție cu webpack + Serwist
npm run test:e2e         # suită Playwright
npm run perf:budget      # bugete pentru payload-urile de date
```

Pentru testele Python:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest
```

## Date

Fișierele livrate clientului se află în `public/data/`. În prezent, setul
principal conține 1.013 ape contractate și 96 de asociații; straturile
necontractate și geometriile pe județe sunt păstrate separat pentru încărcare
și randare eficientă.

Reîmprospătarea completă se poate porni cu:

```bash
npm run data:refresh
```

Workflow-ul `Monthly Data Refresh` rulează și lunar. Pipeline-ul are verificări
de integritate, trasabilitate, determinism și bugete de dimensiune înainte ca
datele regenerate să fie acceptate.

## Raportarea problemelor de date

Formularul din cardul unei ape trimite `POST /api/report`. Endpointul serverless
creează un issue în acest repository cu eticheta `report`.

Este necesară variabila server-side:

```text
REPORT_GITHUB_TOKEN
```

Tokenul trebuie să aibă acces de scriere la Issues pentru repository. Local se
pune în `.env.local`; în producție se configurează în Vercel pentru mediile
dorite. Nu folosi prefixul `NEXT_PUBLIC_`, deoarece tokenul nu trebuie expus în
browser. Fără variabilă, endpointul răspunde cu `503 not_configured`.

Aplicația are nevoie de runtime-ul serverless pentru acest endpoint; nu activa
`output: "export"` în `next.config.ts`.

## CI și deploy

GitHub Actions verifică:

- testele TypeScript și Python, inclusiv pragurile de coverage;
- fluxurile E2E și contractele datelor reale;
- integritatea și bugetele payload-urilor de date;
- auditul de securitate și dependențe;
- bugetele Lighthouse și urmele de performanță ale hărții;
- disponibilitatea periodică a URL-urilor asociațiilor.

Push-urile pe `main` declanșează automat build-ul și deploy-ul Vercel.
