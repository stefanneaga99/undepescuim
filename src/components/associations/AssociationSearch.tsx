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
import { useMapStore } from '@/stores/map-store';
import { useMediaQuery } from '@/hooks/use-media-query';
import { useI18n } from '@/i18n/provider';
import { cn } from '@/lib/utils';

/**
 * Searchable association selector (cmdk Command).
 * - Mobile (<768px): icon → fullscreen overlay (z-2000, above the sheet).
 * - Tablet/desktop (≥768px): inline trigger + dropdown in the header.
 * Select → store.selectAssociation(slug); "Toate asociațiile" → null.
 * Local state only: `open` (dropdown/overlay visibility).
 */
export function AssociationSearch() {
  const associations = useMapStore((s) => s.associations);
  const selectedSlug = useMapStore((s) => s.selectedAssociationSlug);
  const selectAssociation = useMapStore((s) => s.selectAssociation);
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  // Escape closes the overlay on mobile too (plan edge case: keyboard nav in
  // the association search — Escape closes). cmdk's own Escape handling only
  // closes its list; the fullscreen overlay is app-controlled.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);
  // Desktop trigger ref — the dropdown panel is portaled to <body> so it can
  // escape the header's backdrop-blur stacking context (t_b6a0e2fe): the
  // panel used to render inside the header (z-50) BELOW the click-outside
  // catcher (z-99), so clicking any item hit the catcher and the dropdown
  // closed WITHOUT selecting — the desktop association search was dead.
  const triggerRef = useRef<HTMLButtonElement>(null);
  // Panel anchor measured in the open click handler (never during render —
  // react-hooks/refs forbids ref reads in render).
  const [panelPos, setPanelPos] = useState<{ top: number; left: number; width: number } | null>(null);
  // Only one Command instance renders per breakpoint — otherwise cmdk typing
  // would target the hidden duplicate input.
  const isMobile = useMediaQuery('(max-width: 767px)');

  const selected = associations.find((a) => a.slug === selectedSlug) ?? null;

  const handleSelect = (slug: string | null) => {
    selectAssociation(slug);
    setOpen(false);
  };

  const panel = (
    <Command className="rounded-lg border bg-popover text-popover-foreground shadow-md">
      <CommandInput placeholder={t('search.placeholder')} autoFocus />
      <CommandList className="max-h-[55dvh] overflow-y-auto">
        <CommandEmpty>{t('search.empty')}</CommandEmpty>
        <CommandGroup heading={t('search.groupHeading')}>
          {associations.map((a) => (
            <CommandItem
              key={a.slug}
              value={`${a.name} ${a.slug}`}
              data-testid="assoc-option"
              data-slug={a.slug}
              onSelect={() => handleSelect(a.slug)}
            >
              <span className="flex-1 truncate">{a.name}</span>
              <span className="ml-2 shrink-0 rounded-full bg-muted px-1.5 py-0.5 text-[10px] font-medium tabular-nums text-muted-foreground">
                {a.ape}
              </span>
              {a.slug === selectedSlug && (
                <Check className="ml-1 h-3.5 w-3.5 shrink-0 text-primary" />
              )}
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandGroup>
          <CommandItem
            value="toate-asociatiile"
            data-testid="assoc-option"
            data-slug="__all__"
            onSelect={() => handleSelect(null)}
          >
            <span className="flex-1">{t('search.all')}</span>
            {selectedSlug === null && <Check className="ml-1 h-3.5 w-3.5 text-primary" />}
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </Command>
  );

  return (
    <>
      {/* Mobile: icon → fullscreen overlay.
          Portaled to <body>: the header's backdrop-blur creates a containing
          block that would otherwise shrink `fixed inset-0` to the header. */}
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="map-touch flex h-9 w-9 shrink-0 items-center justify-center rounded-md border text-muted-foreground md:hidden"
        aria-label={t('search.ariaSearch')}
        data-testid="assoc-search-mobile"
      >
        <Search className="h-4 w-4" />
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
                aria-label={t('search.ariaBack')}
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <span className="font-medium">{t('search.overlayTitle')}</span>
            </div>
            <div className="flex-1 overflow-hidden p-2">{panel}</div>
          </div>,
          document.body,
        )}

      {/* ── Tablet/desktop: inline trigger + dropdown ─────────────────── */}
      <div className="relative hidden w-full max-w-[280px] md:block lg:max-w-[480px]">
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
          className={cn(
            'map-touch flex h-9 w-full items-center gap-2 rounded-md border bg-background px-3 text-sm shadow-sm transition-colors hover:bg-accent',
            open && 'ring-2 ring-ring',
          )}
          data-testid="assoc-search"
        >
          <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
          <span
            className={cn(
              'flex-1 truncate text-left',
              !selected && 'text-muted-foreground',
            )}
          >
            {selected ? selected.name : t('search.placeholder')}
          </span>
          <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
        </button>

        {!isMobile && open && (
          <>
            {/* Both catcher AND panel portaled to <body>: the panel must
                escape the header's backdrop-blur stacking context (see
                triggerRef note) or it renders below the catcher and is
                unclickable. Positioned from the trigger's bounding rect.
                t_7a7192ea: the desktop filter panel (FilterBar, z-1000)
                used to sit ABOVE the dropdown (z-200), covering the left
                strip of every row — clicking an association's NAME (the
                left-aligned text) hit the filter panel and nothing was
                selected. The panel now floats above the filter bar
                (z-1500) and the catcher above it as well (z-1050) so
                outside clicks anywhere (incl. on the filter panel) close
                the dropdown. */}
            {createPortal(
              <div className="fixed inset-0 z-[1050]" onClick={() => setOpen(false)} />,
              document.body,
            )}
            {createPortal(
              <div
                className="fixed z-[1500] mt-1.5"
                style={
                  panelPos ?? { top: 0, left: 0, width: 280 }
                }
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
