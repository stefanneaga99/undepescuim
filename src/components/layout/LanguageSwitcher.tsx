'use client';

import { Languages } from 'lucide-react';
import { useI18n } from '@/i18n/provider';
import { cn } from '@/lib/utils';

/**
 * Language switcher (t_920a7b7b) — replaces the static RO badge in the
 * header. Two-state cycle RO ⇄ EN: the badge shows the CURRENT locale and
 * clicking toggles to the other one. Persistence + browser-language default
 * live in I18nProvider (localStorage `undepescuim.locale`).
 *
 * Cycle (not dropdown) on purpose: the header is a tiny z-50 bar and the
 * filter bar / map overlays sit at z-1000 — a portaled dropdown would need
 * the full z-[1500] treatment (t_7a7192ea) for zero layout benefit over a
 * two-option toggle.
 */
export function LanguageSwitcher() {
  const { locale, setLocale, t } = useI18n();

  return (
    <button
      type="button"
      onClick={() => setLocale(locale === 'ro' ? 'en' : 'ro')}
      aria-label={t('header.switchLanguage')}
      title={t('header.switchLanguage')}
      data-testid="lang-switcher"
      className={cn(
        'shrink-0 rounded-md border px-2 py-0.5 text-xs font-semibold text-muted-foreground transition-colors hover:bg-accent hover:text-foreground',
      )}
    >
      <span className="inline-flex items-center gap-1">
        <Languages className="h-3 w-3" aria-hidden />
        {locale.toUpperCase()}
      </span>
    </button>
  );
}
