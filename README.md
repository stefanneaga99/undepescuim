This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

Live at [https://undepescuim.vercel.app](https://undepescuim.vercel.app) — auto-deployed from `main` via Vercel.

## Raportarea problemelor de date (F3)

Cardurile de apă au două butoane:

- **„Datele sunt corecte"** — semnal pozitiv rapid (deschide formularul cu motivul `data_correct` preselectat).
- **„Raportează o problemă"** — formular complet (motiv + detalii opționale + email opțional).

Formularul trimite un POST la `POST /api/report` (serverless function pe Vercel),
care creează un **GitHub issue** pe `neagastefan99/undepescuim` cu eticheta
`report` — coada de review pentru mentenanța datelor.

### Variabila de mediu (secret)

`REPORT_GITHUB_TOKEN` — token GitHub cu scop **Issues: Read & Write** pe
`neagastefan99/undepescuim` (sau scope `repo` clasic).

- **Local:** în `.env.local` (ignorat de git) — poți folosi `gh auth token`.
- **Producție:** Vercel → Project → Settings → Environment Variables →
  `REPORT_GITHUB_TOKEN` (Production + Preview). **Niciodată `NEXT_PUBLIC_`** —
  tokenul e folosit doar server-side în `src/app/api/report/route.ts`.

Fără token, endpointul răspunde `503 not_configured`, iar formularul afișează
starea de eroare (fără eșecuri silențioase).

Eticheta `report` trebuie să existe pe repo (`gh label create report`), altfel
crearea issue-ului eșuează cu 422.

**Notă:** `/api/report` necesită runtime serverless — nu seta `output: "export"`
în `next.config.ts`, altfel endpointul dispare din build.
