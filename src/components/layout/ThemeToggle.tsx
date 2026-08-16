'use client';

import { useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';
import { Button } from '@/components/ui/button';

/**
 * Sun/Moon toggle in the header (near the RO badge). Uses next-themes
 * resolvedTheme (not theme) so "system" renders the correct icon.
 * Mounted guard prevents the server/client icon mismatch (next-themes
 * returns undefined until mount).
 *
 * Two-state toggle (light ⇄ dark); "system" is only the initial default —
 * the first explicit click pins the choice (dark-mode-feasibility-plan §3).
 */
export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const isDark = resolvedTheme === 'dark';

  return (
    <Button
      variant="ghost"
      size="icon-sm"
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
      aria-label={isDark ? 'Treci la tema luminoasă' : 'Treci la tema întunecată'}
      title={isDark ? 'Tema luminoasă' : 'Tema întunecată'}
      data-testid="theme-toggle"
      className="shrink-0"
      suppressHydrationWarning
    >
      {mounted ? (isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />) : (
        <Moon className="h-5 w-5" />
      )}
    </Button>
  );
}