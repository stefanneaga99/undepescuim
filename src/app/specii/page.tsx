import type { Metadata } from 'next';
import Link from 'next/link';
import {
  AlertTriangle,
  ArrowLeft,
  CalendarClock,
  ExternalLink,
  Fish,
  Ruler,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import {
  SPECIES,
  SPECIES_DAILY_LIMIT,
  SPECIES_ISSUING_BODY,
  SPECIES_LAST_UPDATED,
  SPECIES_ROW_SOURCES,
  SPECIES_SOURCES,
  SPECIES_WITH_SIZE,
  SPECIES_WITHOUT_SIZE,
  type Species,
} from '@/content/species';
import { SpeciesSearch } from '@/components/species/SpeciesSearch';

export const metadata: Metadata = {
  title: 'Specii — dimensiuni minime de reținere — UndePescuim.ro',
  description:
    'Dimensiunile minime legale de reținere pentru peștii de apă dulce din România, cu surse și ultima verificare. Valori naționale — bălțile private pot impune limite mai mari.',
};

function RetentionBadge({ species }: { species: Species }) {
  if (species.retention === 'interzis') {
    return (
      <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-red-700 dark:bg-red-950/60 dark:text-red-300">
        <ShieldCheck className="h-3 w-3" />
        Interzis
      </span>
    );
  }
  if (species.retention === 'neconfirmat') {
    return (
      <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-700 dark:bg-amber-950/60 dark:text-amber-300">
        <AlertTriangle className="h-3 w-3" />
        Neconfirmat
      </span>
    );
  }
  if (species.retention === 'fara-limita') {
    return (
      <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-600 dark:bg-slate-800 dark:text-slate-300">
        Fără limită
      </span>
    );
  }
  return null;
}

function SpeciesCard({ species }: { species: Species }) {
  return (
    <div
      id={`specii-${species.slug}`}
      className="flex flex-col gap-2 rounded-md border p-3 transition-shadow scroll-mt-24"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-bold">{species.nameRo}</p>
          {species.nameScientific && (
            <p className="truncate text-xs italic text-muted-foreground">{species.nameScientific}</p>
          )}
        </div>
        <RetentionBadge species={species} />
      </div>

      <div className="flex items-baseline gap-1.5">
        {species.retention !== 'min-size' ? (
          <span className="text-sm text-muted-foreground">
            {species.retention === 'interzis'
              ? 'Reținerea este interzisă.'
              : species.retention === 'fara-limita'
                ? 'Fără dimensiune minimă stabilită.'
                : 'Dimensiune neconfirmată — vezi sursa.'}
          </span>
        ) : species.minSizeCm !== null ? (
          <>
            <span className="text-2xl font-extrabold tabular-nums tracking-tight">
              {species.minSizeCm}
              <span className="ml-0.5 text-sm font-semibold text-muted-foreground">cm</span>
            </span>
            <span className="text-xs text-muted-foreground">dimensiune minimă de reținere</span>
          </>
        ) : (
          <span className="text-sm text-muted-foreground">Dimensiune neconfirmată — vezi sursa.</span>
        )}
      </div>

      {species.prohibition && (
        <p className="flex items-start gap-1.5 text-xs leading-relaxed text-muted-foreground">
          <CalendarClock className="mt-0.5 h-3 w-3 shrink-0" />
          {species.prohibition}
        </p>
      )}
      {species.notes && species.notes !== species.prohibition && (
        <p className="text-xs leading-relaxed text-muted-foreground">{species.notes}</p>
      )}

      <p className="mt-auto border-t pt-1.5 text-[10px] leading-relaxed text-muted-foreground">
        Sursă: {species.sourceRef}
        {species.lastUpdated ? ` · verificat ${species.lastUpdated}` : ''}
      </p>
    </div>
  );
}

export default function SpeciiPage() {
  const sizeCount = SPECIES_WITH_SIZE.length;
  const withoutCount = SPECIES_WITHOUT_SIZE.length;

  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-6 md:py-10">
      <Link
        href="/"
        className="mb-4 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Înapoi la hartă
      </Link>

      <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
        Dimensiuni minime de reținere, pe specii
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Ultima verificare a faptelor: {SPECIES_LAST_UPDATED}.
        {SPECIES_ISSUING_BODY ? ` Emitent: ${SPECIES_ISSUING_BODY}.` : ''} Informațiile se pot
        schimba anual prin ordin de ministru — verifică sursele oficiale (linkuri la finalul
        paginii) înainte de o decizie. Conținut sensibil la timp: se re-verifică trimestrial.
      </p>

      <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 px-3 py-2.5 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
        <p className="font-medium">Valori naționale</p>
        <p className="mt-0.5 text-xs leading-relaxed opacity-90">
          Dimensiunile de mai jos sunt minimele legale naționale. Bălțile private sau asociațiile pot
          impune limite <strong>mai mari, niciodată mai mici</strong>. În Delta Dunării (ARBDD)
          regimul poate diferi.
        </p>
      </div>

      {/* Căutare */}
      <div className="mt-4">
        <SpeciesSearch species={SPECIES} />
      </div>

      {/* Lista */}
      <section className="mt-6">
        <h2 className="flex items-center gap-2 text-lg font-bold tracking-tight">
          <Ruler className="h-4 w-4 text-primary" />
          Specii cu dimensiune minimă ({sizeCount})
        </h2>
        {sizeCount > 0 ? (
          <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
            {SPECIES_WITH_SIZE.map((s) => (
              <SpeciesCard key={s.slug} species={s} />
            ))}
          </div>
        ) : (
          <p className="mt-2 text-sm text-muted-foreground">
            Momentan nicio dimensiune confirmată — datele sunt în verificare.
          </p>
        )}
      </section>

      {withoutCount > 0 && (
        <section className="mt-6">
          <h2 className="flex items-center gap-2 text-lg font-bold tracking-tight">
            <ShieldCheck className="h-4 w-4 text-primary" />
            Protejate / interzise / neconfirmate ({withoutCount})
          </h2>
          <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
            {SPECIES_WITHOUT_SIZE.map((s) => (
              <SpeciesCard key={s.slug} species={s} />
            ))}
          </div>
        </section>
      )}

      {/* Limită zilnică */}
      <div className="mt-6 rounded-md border border-teal-200 bg-teal-50 px-3 py-2.5 text-sm text-teal-900 dark:border-teal-900 dark:bg-teal-950/40 dark:text-teal-100">
        <p className="flex items-center gap-1.5 font-medium">
          <Fish className="h-3.5 w-3.5 shrink-0" />
          Limita generală de captură
        </p>
        <p className="mt-0.5 text-xs leading-relaxed opacity-90">{SPECIES_DAILY_LIMIT}</p>
      </div>

      <p className="mt-4 flex items-start gap-1.5 text-xs leading-relaxed text-muted-foreground">
        <Sparkles className="mt-0.5 h-3 w-3 shrink-0" />
        Mai multe reguli (permis, unelte, capcane) sunt pe pagina{' '}
        <Link href="/permis" className="text-primary underline-offset-2 hover:underline">
          Permis &amp; Reguli 2026
        </Link>
        .
      </p>

      {/* Surse */}
      <section className="mt-8">
        <h2 className="flex items-center gap-2 text-lg font-bold tracking-tight">
          <ExternalLink className="h-4 w-4 text-primary" />
          Surse
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          Valorile din tabel au fost verificate față de sursele oficiale (data verificării:{' '}
          {SPECIES_LAST_UPDATED}). Re-verifică-le trimestrial — conținutul este sensibil la timp.
        </p>
        {SPECIES_ROW_SOURCES.length > 0 && (
          <ul className="mt-2 flex flex-col gap-1.5">
            {SPECIES_ROW_SOURCES.map((src) => (
              <li key={src} className="text-xs text-muted-foreground">
                <span className="font-medium text-foreground">Valorile din tabel:</span> {src}
              </li>
            ))}
          </ul>
        )}
        <ul className="mt-2 flex flex-col gap-1.5">
          {SPECIES_SOURCES.map((s) => (
            <li key={s.url} className="text-sm">
              <a
                href={s.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-start gap-1 text-primary hover:underline"
              >
                <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                <span>
                  {s.label}
                  <span className="block text-xs text-muted-foreground">{s.note}</span>
                </span>
              </a>
            </li>
          ))}
        </ul>
      </section>

      <p className="mt-8 border-t pt-4 text-xs text-muted-foreground">
        Ultima verificare a faptelor: {SPECIES_LAST_UPDATED}. Conținutul se re-verifică trimestrial
        (Monitorul Oficial, ANADSPA).
      </p>
    </main>
  );
}
