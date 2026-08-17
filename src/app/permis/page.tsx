'use client';

import Link from 'next/link';
import { ArrowLeft, AlertTriangle, ExternalLink, FileText, HelpCircle, Scale, ShieldCheck, Sparkles } from 'lucide-react';
import {
  useMemo,
} from 'react';
import { useI18n } from '@/i18n/provider';
import * as RO from '@/content/permis-2026';
import { PERMIS_EN } from '@/content/permis-2026.en';

/**
 * Permis & Reguli 2026 — client component (t_920a7b7b) so the language
 * switcher re-renders it instantly. RO content is the default; EN is the
 * type-checked mirror from `permis-2026.en.ts`. SEO metadata lives in the
 * sibling layout.tsx (server component).
 */

function SectionHeading({
  icon,
  children,
}: {
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <h2 className="mt-8 flex items-center gap-2 text-lg font-bold tracking-tight">
      {icon}
      {children}
    </h2>
  );
}

function GotchaCard({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2.5 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
      <p className="flex items-center gap-1.5 font-semibold">
        <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
        {title}
      </p>
      <p className="mt-0.5 text-xs leading-relaxed opacity-90">{body}</p>
    </div>
  );
}

export default function PermisPage() {
  const { locale, t } = useI18n();

  // Pick the locale's content. `RO` is the current-locale shape source;
  // PERMIS_EN is structurally identical (compile-checked).
  const C = useMemo(() => (locale === 'en' ? PERMIS_EN : RO), [locale]);
  const lastUpdated = C.PERMIS_LAST_UPDATED;

  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-6 md:py-10">
      <Link
        href="/"
        className="mb-4 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        {t('permis.backToMap')}
      </Link>

      <h1 className="text-2xl font-bold tracking-tight md:text-3xl">{t('permis.title')}</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        {t('permis.intro', { date: lastUpdated })}
      </p>

      {/* §1 What changed */}
      <SectionHeading icon={<ShieldCheck className="h-4 w-4 text-primary" />}>
        {t('permis.whatChangedHeading')}
      </SectionHeading>
      <p className="mt-2 text-sm leading-relaxed">{C.PERMIS_WHAT_CHANGED.lead}</p>
      <p className="mt-3 text-sm font-medium">{t('permis.whatChangedLead2')}</p>
      <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm leading-relaxed">
        {C.PERMIS_WHAT_CHANGED.bullets.map((b) => (
          <li key={b}>{b}</li>
        ))}
      </ul>
      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{C.PERMIS_WHAT_CHANGED.unchanged}</p>

      {/* §2 How to get it */}
      <SectionHeading icon={<FileText className="h-4 w-4 text-primary" />}>
        {t('permis.getPermitHeading')}
      </SectionHeading>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
        {t('permis.getPermitIntro')}
      </p>

      <h3 className="mt-4 text-sm font-bold">{C.PERMIS_GET_STATE.title}</h3>
      <p className="mt-1 text-sm leading-relaxed">{C.PERMIS_GET_STATE.intro}</p>
      <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm leading-relaxed">
        {C.PERMIS_GET_STATE.items.map((i) => (
          <li key={i}>{i}</li>
        ))}
      </ul>
      <p className="mt-2 text-sm leading-relaxed">
        <a
          href={C.PERMIS_PORTAL_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-primary hover:underline"
        >
          {t('permis.openPortal')}
          <ExternalLink className="h-3.5 w-3.5" />
        </a>
      </p>

      <h3 className="mt-4 text-sm font-bold">{C.PERMIS_GET_ASSOCIATION.title}</h3>
      <p className="mt-1 text-sm leading-relaxed">{C.PERMIS_GET_ASSOCIATION.intro}</p>
      <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm leading-relaxed">
        {C.PERMIS_GET_ASSOCIATION.items.map((i) => (
          <li key={i}>{i}</li>
        ))}
      </ul>

      <h3 className="mt-4 text-sm font-bold">{C.PERMIS_GET_DELTA.title}</h3>
      <p className="mt-1 text-sm leading-relaxed">{C.PERMIS_GET_DELTA.intro}</p>
      <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm leading-relaxed">
        {C.PERMIS_GET_DELTA.items.map((i) => (
          <li key={i}>{i}</li>
        ))}
      </ul>

      <div className="mt-4 rounded-md border border-teal-200 bg-teal-50 px-3 py-2.5 text-sm text-teal-900 dark:border-teal-900 dark:bg-teal-950/40 dark:text-teal-100">
        <p className="font-medium">{t('permis.goldenRuleTitle')}</p>
        <p className="mt-0.5 text-xs leading-relaxed opacity-90">{C.PERMIS_GOLDEN_RULE}</p>
      </div>

      {/* Link to /specii — minimum sizes by species */}
      <div className="mt-3 rounded-md border bg-accent/40 px-3 py-2.5 text-sm">
        <p className="font-medium">{t('permis.retentionQuestion')}</p>
        <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">
          {t('permis.retentionAnswer')}
        </p>
        <Link
          href="/specii"
          className="mt-1 inline-flex items-center gap-1 text-xs font-semibold text-primary underline-offset-2 hover:underline"
        >
          {t('permis.retentionLink')}
        </Link>
      </div>

      {/* §3 How to renew */}
      <SectionHeading icon={<Sparkles className="h-4 w-4 text-primary" />}>
        {t('permis.renewHeading')}
      </SectionHeading>
      <p className="mt-2 text-sm leading-relaxed">{C.PERMIS_RENEW.intro}</p>
      <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm leading-relaxed">
        <li>{C.PERMIS_RENEW.currentRule}</li>
        <li>{C.PERMIS_RENEW.changing}</li>
      </ul>

      {/* §4 Gotchas */}
      <SectionHeading icon={<AlertTriangle className="h-4 w-4 text-primary" />}>
        {t('permis.gotchasHeading')}
      </SectionHeading>
      <div className="mt-2 flex flex-col gap-2">
        {C.PERMIS_GOTCHAS.map((g) => (
          <GotchaCard key={g.title} title={g.title} body={g.body} />
        ))}
      </div>

      {/* §5 Rules */}
      <SectionHeading icon={<Scale className="h-4 w-4 text-primary" />}>
        {t('permis.rulesHeading')}
      </SectionHeading>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
        {t('permis.rulesIntro')}
      </p>
      <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm leading-relaxed">
        {C.PERMIS_RULES.map((r) => (
          <li key={r}>{r}</li>
        ))}
      </ul>

      {/* §6 What's coming */}
      <SectionHeading icon={<Sparkles className="h-4 w-4 text-primary" />}>
        {t('permis.upcomingHeading')}
      </SectionHeading>
      <div className="mt-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2.5 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
        <p className="font-semibold">{t('permis.notInForce')}</p>
        <p className="mt-0.5 text-xs leading-relaxed opacity-90">{C.PERMIS_UPCOMING.status}</p>
      </div>
      <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm leading-relaxed">
        {C.PERMIS_UPCOMING.bullets.map((b) => (
          <li key={b}>{b}</li>
        ))}
      </ul>
      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{C.PERMIS_UPCOMING.unchanged}</p>

      {/* FAQ */}
      <SectionHeading icon={<HelpCircle className="h-4 w-4 text-primary" />}>
        {t('permis.faqHeading')}
      </SectionHeading>
      <dl className="mt-2 flex flex-col gap-3">
        {C.PERMIS_FAQ.map((f) => (
          <div key={f.q} className="rounded-md border px-3 py-2.5">
            <dt className="text-sm font-semibold">{f.q}</dt>
            <dd className="mt-0.5 text-sm leading-relaxed text-muted-foreground">{f.a}</dd>
          </div>
        ))}
      </dl>

      {/* Sources */}
      <SectionHeading icon={<ExternalLink className="h-4 w-4 text-primary" />}>
        {t('permis.sourcesHeading')}
      </SectionHeading>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
        {t('permis.sourcesIntro', { date: lastUpdated })}
      </p>
      <ul className="mt-2 flex flex-col gap-1.5">
        {C.PERMIS_SOURCES.map((s) => (
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

      <p className="mt-8 border-t pt-4 text-xs text-muted-foreground">
        {t('permis.footer', { date: lastUpdated })}
      </p>
    </main>
  );
}