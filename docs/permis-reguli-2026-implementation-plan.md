# Permis & Reguli 2026 — plan de implementare

**Roadmap item:** F5 (t_a3c4c042, rank #2)
**Owner:** executioner (după review)
**Conținut:** `docs/permis-reguli-2026-content-draft.md` (RO)
**Surse:** `docs/permis-reguli-2026-sources.md`
**Stack:** Next.js 16 (App Router, flat, fără `[locale]` încă), React 19, TypeScript, Tailwind 4,
shadcn/ui, lucide-react. Server components pentru pagini statice (fără Leaflet pe server).

---

## Obiectiv

Adaugă o pagină statică (RO) „Permis & Reguli 2026" care explică tranziția ANPA→ANADSPA:
ce s-a schimbat, cum obții/reînnoiești permisul, capcanele cunoscute și regulile de bază.

## Decizii

- **Rută:** `/permis` (evergreen; H1 „Permis & Reguli 2026"). Alternativă: `/permis-2026`
  (an-stampilată) — nu recomand, fiindcă sparge linkurile la fiecare an. Slug-ul evergreen se
  actualizează în loc, iar „ultima verificare" marchează prospețimea.
- **Server component** — conținutul e static, nu importă Leaflet/stare client.
- **Fapte din surse** într-un modul `src/content/permis-2026.ts` (URL-uri, date, FAQ, termene)
  ca să fie ușor de re-verificat trimestrial, separate de JSX-ul de prezentare.

---

## Pas 0 — Gate de verificare (ÎNAINTE de cod)

Re-confirmă pe surse oficiale (vezi `sources.md` → „Acțiuni de re-verificat"):
1. Denumirea ANADSPA + nr. OUG din Monitorul Oficial.
2. Domeniul curent al portalului de permise.
3. Statutul proiectului de ordin MADR (mai 2026).
Dacă vreun fapt se schimbă, actualizează `content-draft.md` + `src/content/permis-2026.ts` înainte
de a scrie pagina.

---

## Pas 1 — Modul de conținut (fapte, ușor de re-verificat)

Creează `src/content/permis-2026.ts`:

```ts
/**
 * Fapte pentru pagina „Permis & Reguli 2026" (roadmap F5).
 * Surse: docs/permis-reguli-2026-sources.md. Reverificare trimestrială.
 */
export const PERMIS_LAST_UPDATED = '2026-08-15';

export const PERMIS_PORTAL_URL = 'https://permise.anpa.ro:12443/portal-public/permis';

export const PERMIS_FAQ: { q: string; a: string }[] = [
  { q: 'Cât costă permisul de stat în 2026?', a: 'Gratuit.' },
  { q: 'Unde îl obțin?', a: 'Online, pe portalul de permise.' },
  // ... restul din content-draft.md §FAQ
];

export const PERMIS_GOTCHAS: { title: string; body: string }[] = [
  { title: 'Bug-ul de 1 ianuarie', body: '...' },
  { title: '„Permisul deja expirat"', body: '...' },
  { title: 'Chestionarul de legislație e obligatoriu', body: '...' },
  { title: 'Fișa de captură', body: '...' },
];
```

> Conținutul complet (textul integral) e în `content-draft.md` — copiază-l în acest modul,
> împărțit în constantele de mai sus. Separația fapte/prezentare face reverificarea trimestrială
> banală (un singur fișier de actualizat, nu JSX).

## Pas 2 — Pagina (`/permis`)

Creează `src/app/permis/page.tsx` (server component):

```tsx
import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowLeft, ExternalLink } from 'lucide-react';
import {
  PERMIS_LAST_UPDATED,
  PERMIS_PORTAL_URL,
  PERMIS_FAQ,
  PERMIS_GOTCHAS,
} from '@/content/permis-2026';

export const metadata: Metadata = {
  title: 'Permis & Reguli 2026 — UndePescuim.ro',
  description:
    'Ghid 2026: tranziția ANPA→ANADSPA, cum obții și reînnoiești permisul de pescuit recreativ, capcane și reguli esențiale.',
};

export default function PermisPage() {
  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-6 md:py-10">
      <Link href="/" className="mb-4 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Înapoi la hartă
      </Link>
      <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Permis & Reguli 2026</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Ultima verificare a faptelor: {PERMIS_LAST_UPDATED}. Informațiile se pot schimba — verifică
        sursele oficiale înainte de o decizie.
      </p>
      {/* §1 Ce s-a schimbat, §2 Cum obții, §3 Cum reînnoiești, §4 Capcane, §5 Reguli, §6 Ce se pregătește */}
      {/* <a href={PERMIS_PORTAL_URL} target="_blank" rel="noopener noreferrer">Portal permise <ExternalLink/></a> */}
      {/* render {PERMIS_GOTCHAS.map(...)}, {PERMIS_FAQ.map(...)} */}
    </main>
  );
}
```

Convenții de respectat (din codebase):
- `@/` alias de import (deja configurat).
- Text RO cu diacritice; heading-uri descriptive; fără placeholder „N/A".
- Pagina NU importă Leaflet și NU folosește `'use client'` (e statică).
- Stil: utilitare Tailwind, ton identic cu `Header.tsx`/`WaterDetailCard.tsx` (text-sm/xs, muted-foreground).
- Pentru fiecare „gotcha" folosește un bloc `rounded-md border` similar cu notificarea
  „Apă necontractată" din `WaterDetailCard.tsx` (border-teal-200 bg-teal-50 …), sau varianta
  `amber` pentru atenționări.

## Pas 3 — Link în header

Editează `src/components/layout/Header.tsx` (client component): adaugă un link „Permis 2026"
între search și badge-ul RO.

```tsx
<nav className="shrink-0">
  <Link
    href="/permis"
    className="hidden items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-semibold text-muted-foreground hover:bg-accent hover:text-foreground sm:inline-flex"
  >
    Permis 2026
  </Link>
</nav>
```

> Ascuns pe `xs` (`hidden sm:inline-flex`) ca să nu înghesuie header-ul mobil (logo + search + RO).
> Alternativ, dacă vrei vizibil și pe mobil: iconiță `ScrollText`/`BadgeCheck` fără text sub `sm`.

## Pas 4 — Link în cardul de apă

Editează `src/components/waters/WaterDetailCard.tsx`:

1. În blocul „Apă necontractată" (rândurile 60–68), adaugă sub paragraful existent:

```tsx
<Link href="/permis" className="mt-1 inline-flex items-center gap-1 text-xs font-semibold text-teal-800 underline-offset-2 hover:underline dark:text-teal-200">
  Vezi ghidul „Permis & Reguli 2026" →
</Link>
```

2. Lângă butonul „Raportează o problemă" (rândul 145), adaugă un al doilea buton-link:

```tsx
<Link href="/permis" className="mt-1 inline-flex w-fit items-center gap-2 rounded-md border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-accent hover:text-foreground">
  <ScrollText className="h-3.5 w-3.5" />
  Permis & Reguli 2026
</Link>
```

> Importă `Link` din `next/link` și `ScrollText` din `lucide-react` (susul fișierului, unde sunt
> deja importate `ExternalLink`, `Flag` etc.).

## Pas 5 — Verificare locală

```bash
cd ~/undepescuim
npm run lint          # fără erori noi
npm run build         # build de producție trece
npm run dev           # deschide http://localhost:3000/permis
```

Verifică manual:
- `/permis` se randăm corect pe mobil (lățime <768px) și desktop.
- Linkul din header duce la `/permis` și înapoi („Înapoi la hartă").
- Cardul „Apă necontractată" afișează linkul către ghid.
- Cardul unei ape contractate afișează butonul „Permis & Reguli 2026".
- Diacriticele se văd corect (UTF-8).

## Pas 6 — „Ultima actualizare" + întreținere trimestrială

- `PERMIS_LAST_UPDATED` se afișează sus pe pagină (deja în Pas 2).
- Adaugă o notă în `docs/ARCHITECTURE.md` (secțiunea relevantă de întreținere) sau un comentariu
  în `src/content/permis-2026.ts`: „Reverifică trimestrial: madr.ro, portal permise, Monitorul
  Oficial — vezi sources.md". (Opțional: un reminder în kanban, nu un cron, fiindcă e content.)

---

## Fișiere atinse

| Acțiune | Fișier |
|---------|--------|
| creează | `src/content/permis-2026.ts` |
| creează | `src/app/permis/page.tsx` |
| modifică | `src/components/layout/Header.tsx` |
| modifică | `src/components/waters/WaterDetailCard.tsx` |
| (opțional) | `docs/ARCHITECTURE.md` — notă întreținere |

## Riscuri & tradeoffs

- **Fapte în mișcare** (tranziție recentă + proiect de ordin în consultare): conținutul poate
  deveni învechit rapid. Mitigare: `PERMIS_LAST_UPDATED` vizibil + reverificare trimestrială +
  separarea faptelor în `src/content/permis-2026.ts`.
- **Denumire ANADSPA / domeniu portal** pot să difere de cele din draft (sursă de presă). Mitigare:
  Pas 0 gate înainte de cod.
- **Proiect de ordin MADR** nu e în vigoare — pagina trebuie să-l prezinte clar ca „pregătit", nu
  ca regulă activă (altfel inducere în eroare). E marcat ⚠️ în draft.
- **Header aglomerat pe mobil**: linkul e ascuns sub `sm`; dacă e nevoie de vizibilitate pe mobil,
  folosește iconiță fără text.

## Acceptare (definition of done)

- Pagina `/permis` live cu tot conținutul din draft (RO), diacritice corecte.
- „Ultima verificare" afișată.
- Link header + link card de apă funcționale.
- `npm run lint` și `npm run build` trec fără erori noi.
- Faptele trec prin gate-ul Pas 0 (surse oficiale), iar itemele ⚠️ fie sunt rezolvate, fie rămân
  marcate ca atare cu link către sursa oficială.
