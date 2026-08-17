'use client';

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
import { useI18n, type I18nT } from '@/i18n/provider';
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

function RetentionBadge({ species, t }: { species: Species; t: I18nT }) {
  if (species.retention === 'interzis') {
    return (
      <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-red-700 dark:bg-red-950/60 dark:text-red-300">
        <ShieldCheck className="h-3 w-3" />
        {t('specii.retentionInterzis')}
      </span>
    );
  }
  if (species.retention === 'neconfirmat') {
    return (
      <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-700 dark:bg-amber-950/60 dark:text-amber-300">
        <AlertTriangle className="h-3 w-3" />
        {t('specii.retentionNeconfirmat')}
      </span>
    );
  }
  if (species.retention === 'fara-limita') {
    return (
      <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-600 dark:bg-slate-800 dark:text-slate-300">
        {t('specii.retentionFaraLimita')}
      </span>
    );
  }
  return null;
}

function SpeciesCard({ species, t }: { species: Species; t: I18nT }) {
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
        <RetentionBadge species={species} t={t} />
      </div>

      <div className="flex items-baseline gap-1.5">
        {species.retention !== 'min-size' ? (
          <span className="text-sm text-muted-foreground">
            {species.retention === 'interzis'
              ? t('specii.retentionInterzisSentence')
              : species.retention === 'fara-limita'
                ? t('specii.retentionFaraLimitaSentence')
                : t('specii.retentionNeconfirmatSentence')}
          </span>
        ) : species.minSizeCm !== null ? (
          <>
            <span className="text-2xl font-extrabold tabular-nums tracking-tight">
              {species.minSizeCm}
              <span className="ml-0.5 text-sm font-semibold text-muted-foreground">cm</span>
            </span>
            <span className="text-xs text-muted-foreground">{t('specii.minSizeSuffix')}</span>
          </>
        ) : (
          <span className="text-sm text-muted-foreground">{t('specii.retentionNeconfirmatSentence')}</span>
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
        {t('specii.sourceLabel', { ref: species.sourceRef })}
        {species.lastUpdated ? t('specii.verifiedLabel', { date: species.lastUpdated }) : ''}
      </p>
    </div>
  );
}

export default function SpeciiPage() {
  const { t } = useI18n();
  const sizeCount = SPECIES_WITH_SIZE.length;
  const withoutCount = SPECIES_WITHOUT_SIZE.length;

  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-6 md:py-10">
      <Link
        href="/"
        className="mb-4 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        {t('specii.backToMap')}
      </Link>

      <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
        {t('specii.title')}
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">
        {t('specii.introLastChecked', { date: SPECIES_LAST_UPDATED })}
        {SPECIES_ISSUING_BODY ? ` ${t('specii.introIssuer', { issuer: SPECIES_ISSUING_BODY })}` : ''}{' '}
        {t('specii.introRest')}
      </p>

      <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 px-3 py-2.5 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
        <p className="font-medium">{t('specii.nationalTitle')}</p>
        <p className="mt-0.5 text-xs leading-relaxed opacity-90">
          {t('specii.nationalBody')}
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
          {t('specii.withSizeHeading', { n: sizeCount })}
        </h2>
        {sizeCount > 0 ? (
          <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
            {SPECIES_WITH_SIZE.map((s) => (
              <SpeciesCard key={s.slug} species={s} t={t} />
            ))}
          </div>
        ) : (
          <p className="mt-2 text-sm text-muted-foreground">
            {t('specii.noConfirmed')}
          </p>
        )}
      </section>

      {withoutCount > 0 && (
        <section className="mt-6">
          <h2 className="flex items-center gap-2 text-lg font-bold tracking-tight">
            <ShieldCheck className="h-4 w-4 text-primary" />
            {t('specii.withoutSizeHeading', { n: withoutCount })}
          </h2>
          <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
            {SPECIES_WITHOUT_SIZE.map((s) => (
              <SpeciesCard key={s.slug} species={s} t={t} />
            ))}
          </div>
        </section>
      )}

      {/* Limită zilnică */}
      <div className="mt-6 rounded-md border border-teal-200 bg-teal-50 px-3 py-2.5 text-sm text-teal-900 dark:border-teal-900 dark:bg-teal-950/40 dark:text-teal-100">
        <p className="flex items-center gap-1.5 font-medium">
          <Fish className="h-3.5 w-3.5 shrink-0" />
          {t('specii.dailyLimitHeading')}
        </p>
        <p className="mt-0.5 text-xs leading-relaxed opacity-90">{SPECIES_DAILY_LIMIT}</p>
      </div>

      <p className="mt-4 flex items-start gap-1.5 text-xs leading-relaxed text-muted-foreground">
        <Sparkles className="mt-0.5 h-3 w-3 shrink-0" />
        {t('specii.moreRules')}{' '}
        <Link href="/permis" className="text-primary underline-offset-2 hover:underline">
          {t('specii.moreRulesLink')}
        </Link>
        .
      </p>

      {/* Surse */}
      <section className="mt-8">
        <h2 className="flex items-center gap-2 text-lg font-bold tracking-tight">
          <ExternalLink className="h-4 w-4 text-primary" />
          {t('specii.sourcesHeading')}
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          {t('specii.sourcesIntro', { date: SPECIES_LAST_UPDATED })}
        </p>
        {SPECIES_ROW_SOURCES.length > 0 && (
          <ul className="mt-2 flex flex-col gap-1.5">
            {SPECIES_ROW_SOURCES.map((src) => (
              <li key={src} className="text-xs text-muted-foreground">
                <span className="font-medium text-foreground">{t('specii.tableValuesLabel')}</span> {src}
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
        {t('specii.footer', { date: SPECIES_LAST_UPDATED })}
      </p>
    </main>
  );
}