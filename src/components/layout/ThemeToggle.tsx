'use client';

import { useSyncExternalStore } from 'react';
import { Moon, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';
import { Button } from '@/components/ui/button';
import { useI18n } from '@/i18n/provider';

/**
 * Sun/Moon toggle in the header (next to the language switcher). Uses
 * next-themes resolvedTheme (not theme) so "system" renders the correct icon.
 * Hydration-safe: useSyncExternalStore reports false on the server and
 * true on the client, so the icon can never mismatch between the server
 * render and the first client render (next-themes returns undefined
 * until mount). Labels are i18n (t_920a7b7b).
 *
 * Two-state toggle (light ⇄ dark); "system" is only the initial default —
 * the first explicit click pins the choice (dark-mode-feasibility-plan §3).
 */
export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const { t } = useI18n();
  // `false` during SSR / first client render, `true` after hydration.
  const mounted = useSyncExternalStore(
    () => () => {}, // subscribe — theme state is reactive via useTheme
    () => true,
    () => false,
  );

  const isDark = mounted && resolvedTheme === 'dark';

  return (
    <Button
      variant="ghost"
      size="icon-sm"
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
      aria-label={isDark ? t('header.themeLight') : t('header.themeDark')}
      title={isDark ? t('header.themeLightTitle') : t('header.themeDarkTitle')}
      data-testid="theme-toggle"
      className="shrink-0"
      suppressHydrationWarning
    >
      {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </Button>
  );
}