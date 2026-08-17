'use client';

import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { ArrowLeft, Check, ChevronDown, Search } from 'lucide-react';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import { useMediaQuery } from '@/hooks/use-media-query';
import { normalizeText, type Species } from '@/content/species';
import { useI18n } from '@/i18n/provider';

/**
 * Căutare de specii (cmdk Command) — pagina /specii.
 * - Mobile (<768px): trigger full-width → overlay fullscreen (z-2000).
 * - Desktop (≥768px): trigger + dropdown inline.
 * Select → scroll la rândul speciei + flash de evidențiere (fără store;
 * stare locală doar pentru `open` și `selectedSlug`).
 * Căutarea e diacritic-insensitivă (custom filter pe Command).
 */
export function SpeciesSearch({ species }: { species: Species[] }) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  // Escape closes the mobile search overlay too (plan edge case: keyboard
  // nav in the species search — Escape closes). cmdk's own Escape handling
  // only closes its list; the fullscreen overlay is app-controlled.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const [panelPos, setPanelPos] = useState<{ top: number; left: number; width: number } | null>(null);
  const isMobile = useMediaQuery('(max-width: 767px)');

  const itemValue = (s: Species) =>
    `${s.nameRo} ${s.nameScientific} ${s.minSizeCm !== null ? `${s.minSizeCm} cm` : ''} ${s.retention}`;

  const handleSelect = (slug: string) => {
    setSelectedSlug(slug);
    setOpen(false);
    // Scroll la rând + flash de evidențiere (DOM imperative — efect de focus).
    const el = document.getElementById(`specii-${slug}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      el.classList.add('species-flash');
      window.setTimeout(() => el.classList.remove('species-flash'), 1800);
    }
  };

  const panel = (
    <Command
      filter={(value, search) =>
        normalizeText(value).includes(normalizeText(search)) ? 1 : 0
      }
      className="rounded-lg border bg-popover text-popover-foreground shadow-md"
    >
      <CommandInput placeholder={t('speciesSearch.placeholder')} autoFocus />
      <CommandList className="max-h-[55dvh] overflow-y-auto">
        <CommandEmpty>{t('speciesSearch.empty')}</CommandEmpty>
        <CommandGroup heading={t('speciesSearch.heading')}>
          {species.map((s) => (
            <CommandItem
              key={s.slug}
              value={itemValue(s)}
              data-testid="species-option"
              data-slug={s.slug}
              onSelect={() => handleSelect(s.slug)}
            >
              <span className="flex-1 truncate">
                {s.nameRo}
                {s.nameScientific && (
                  <span className="ml-1 text-xs text-muted-foreground">{s.nameScientific}</span>
                )}
              </span>
              <span className="ml-2 shrink-0 rounded-full bg-muted px-1.5 py-0.5 text-[10px] font-medium tabular-nums text-muted-foreground">
                {s.minSizeCm !== null ? `${s.minSizeCm} cm` : s.retention}
              </span>
              {s.slug === selectedSlug && <Check className="ml-1 h-3.5 w-3.5 shrink-0 text-primary" />}
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </Command>
  );

  return (
    <>
      {/* Mobile: trigger full-width → overlay fullscreen, portale la <body>. */}
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="map-touch flex h-11 w-full items-center gap-2 rounded-md border bg-background px-3 text-sm text-muted-foreground shadow-sm md:hidden"
        aria-label={t('speciesSearch.ariaSearch')}
        data-testid="species-search-mobile"
      >
        <Search className="h-4 w-4 shrink-0" />
        <span className="flex-1 text-left">{t('speciesSearch.trigger')}</span>
      </button>

      {isMobile &&
        open &&
        createPortal(
          <div className="fixed inset-0 z-[2000] flex flex-col bg-background">
            <div className="flex h-12 shrink-0 items-center gap-2 border-b px-3">
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="map-touch flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground"
                aria-label={t('speciesSearch.ariaSearch')}
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <span className="font-medium">{t('speciesSearch.overlayTitle')}</span>
            </div>
            <div className="flex-1 overflow-hidden p-2">{panel}</div>
          </div>,
          document.body,
        )}

      {/* ── Desktop: trigger + dropdown inline ─────────────────────────── */}
      <div className="relative hidden w-full max-w-md md:block">
        <button
          ref={triggerRef}
          type="button"
          onClick={() => {
            if (!open && triggerRef.current) {
              const r = triggerRef.current.getBoundingClientRect();
              setPanelPos({ top: r.bottom + 6, left: r.left, width: r.width });
            }
            setOpen((o) => !o);
          }}
          className="map-touch flex h-11 w-full items-center gap-2 rounded-md border bg-background px-3 text-sm shadow-sm transition-colors hover:bg-accent"
          aria-label={t('speciesSearch.ariaSearch')}
          data-testid="species-search"
        >
          <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
          <span className="flex-1 truncate text-left text-muted-foreground">{t('speciesSearch.trigger')}</span>
          <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
        </button>

        {!isMobile && open && (
          <>
            {createPortal(
              <div className="fixed inset-0 z-[1050]" onClick={() => setOpen(false)} />,
              document.body,
            )}
            {createPortal(
              <div
                className="fixed z-[1500] mt-1.5"
                style={panelPos ?? { top: 0, left: 0, width: 448 }}
              >
                {panel}
              </div>,
              document.body,
            )}
          </>
        )}
      </div>
    </>
  );
}
