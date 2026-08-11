'use client';

import { useState } from 'react';
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
  const [open, setOpen] = useState(false);
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
      <CommandInput placeholder="Caută asociația…" autoFocus />
      <CommandList className="max-h-[55dvh] overflow-y-auto">
        <CommandEmpty>Nicio asociație găsită</CommandEmpty>
        <CommandGroup heading="Asociații">
          {associations.map((a) => (
            <CommandItem
              key={a.slug}
              value={`${a.name} ${a.slug}`}
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
          <CommandItem value="toate-asociatiile" onSelect={() => handleSelect(null)}>
            <span className="flex-1">Toate asociațiile</span>
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
        aria-label="Caută asociația"
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
                aria-label="Înapoi"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <span className="font-medium">Caută asociația</span>
            </div>
            <div className="flex-1 overflow-hidden p-2">{panel}</div>
          </div>,
          document.body,
        )}

      {/* ── Tablet/desktop: inline trigger + dropdown ─────────────────── */}
      <div className="relative hidden w-full max-w-[280px] md:block lg:max-w-[480px]">
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className={cn(
            'map-touch flex h-9 w-full items-center gap-2 rounded-md border bg-background px-3 text-sm shadow-sm transition-colors hover:bg-accent',
            open && 'ring-2 ring-ring',
          )}
        >
          <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
          <span
            className={cn(
              'flex-1 truncate text-left',
              !selected && 'text-muted-foreground',
            )}
          >
            {selected ? selected.name : 'Caută asociația…'}
          </span>
          <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
        </button>

        {!isMobile && open && (
          <>
            {/* click-outside catcher (portaled — header backdrop-filter traps fixed) */}
            {createPortal(
              <div className="fixed inset-0 z-[99]" onClick={() => setOpen(false)} />,
              document.body,
            )}
            <div className="absolute left-0 right-0 top-full z-[100] mt-1.5">{panel}</div>
          </>
        )}
      </div>
    </>
  );
}
