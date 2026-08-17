'use client';

import { useI18n } from '@/i18n/provider';
import type { Locale } from '@/i18n/messages';
import { cn } from '@/lib/utils';

/**
 * Language switcher (t_5a65abcf) — two flag buttons, RO 🇷🇴 / EN 🇬🇧, with the
 * active language highlighted. Replaces the t_920a7b7b text badge ("RO"/"EN"
 * single toggle) that the user found non-obvious.
 *
 * Flag choice: UK (Union Jack) for English — "engleză" in Romanian usage is
 * British English; the EN dictionary is orthographically neutral, so UK is the
 * safe pick. Inline SVGs instead of emoji flags on purpose: Chromium on
 * Windows (the primary desktop host) renders flag emoji as the letter pairs
 * "RO"/"GB", so emoji would not show actual flags there.
 *
 * Clicking a flag calls setLocale(lang) — idempotent, so re-clicking the
 * active flag is a no-op. The choice persists via I18nProvider (localStorage
 * `undepescuim.locale`); RO is the hard default (t_5a65abcf §3) and is never
 * overridden by the browser language.
 */
const FLAGS: Record<Locale, { label: string; svg: (className: string) => React.ReactNode }> = {
  ro: {
    label: 'RO',
    svg: (className) => (
      <svg viewBox="0 0 60 30" className={className} aria-hidden focusable="false">
        <rect width="20" height="30" fill="#002B7F" />
        <rect x="20" width="20" height="30" fill="#FCD116" />
        <rect x="40" width="20" height="30" fill="#CE1126" />
      </svg>
    ),
  },
  en: {
    label: 'EN',
    svg: (className) => (
      <svg viewBox="0 0 60 30" className={className} aria-hidden focusable="false">
        <clipPath id="lang-en-clip-s">
          <path d="M0,0 v30 h60 v-30 z" />
        </clipPath>
        <clipPath id="lang-en-clip-t">
          <path d="M30,15 h30 v15 z v15 h-30 z h-30 v-15 z v-15 h30 z" />
        </clipPath>
        <g clipPath="url(#lang-en-clip-s)">
          <path d="M0,0 v30 h60 v-30 z" fill="#012169" />
          <path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" strokeWidth="6" />
          <path d="M0,0 L60,30 M60,0 L0,30" clipPath="url(#lang-en-clip-t)" stroke="#C8102E" strokeWidth="4" />
          <path d="M30,0 v30 M0,15 h60" stroke="#fff" strokeWidth="10" />
          <path d="M30,0 v30 M0,15 h60" stroke="#C8102E" strokeWidth="6" />
        </g>
      </svg>
    ),
  },
};

export function LanguageSwitcher() {
  const { locale, setLocale, t } = useI18n();

  return (
    <div
      role="group"
      aria-label={t('header.chooseLanguage')}
      data-testid="lang-switcher"
      className="flex shrink-0 items-center gap-0.5 rounded-md border p-0.5"
    >
      {(Object.keys(FLAGS) as Locale[]).map((lang) => {
        const active = locale === lang;
        const { label, svg } = FLAGS[lang];
        const title = lang === 'ro' ? t('header.langRomana') : t('header.langEnglish');
        return (
          <button
            key={lang}
            type="button"
            onClick={() => setLocale(lang)}
            aria-pressed={active}
            aria-label={title}
            title={title}
            data-testid={`lang-${lang}`}
            className={cn(
              'flex h-6 items-center gap-1 rounded px-1 text-xs font-semibold transition-colors',
              active
                ? 'bg-accent text-foreground ring-1 ring-inset ring-primary/40'
                : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground',
            )}
          >
            {svg('h-4 w-6 shrink-0 rounded-[1px] object-cover')}
            <span className="sr-only">{lang === 'ro' ? t('header.langRomana') : t('header.langEnglish')}</span>
            {label}
          </button>
        );
      })}
    </div>
  );
}
