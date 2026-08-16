'use client';

import { useState } from 'react';
import { ChevronDown, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';

interface LocalityFilterProps {
  /** all localities present in the SELECTED counties' waters (useLocalities) */
  localities: string[];
  /** currently toggled localities */
  selected: string[];
  onToggle: (locality: string) => void;
  onClear: () => void;
}

/**
 * Locality (localitate) filter (t_dd918db7) — a REFINEMENT of the county
 * filter: rendered only when ≥1 county is selected, lists the UATs present in
 * those counties' waters, ANDs with county/type/contract filters.
 *
 * Searchable popover (Command) rather than chips — a single county exposes
 * 40–100 localities (mobile-first constraint; consistent with FilterBar's
 * pill language). The trigger pill mirrors the county chips.
 */
export function LocalityFilter({ localities, selected, onToggle, onClear }: LocalityFilterProps) {
  const [open, setOpen] = useState(false);

  if (localities.length === 0) return null;

  const label =
    selected.length === 0
      ? 'Toate localitățile'
      : selected.length <= 2
        ? selected.join(', ')
        : `${selected.length} localități`;

  return (
    <div className="flex flex-col gap-1">
      <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        Localitate
      </span>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <button
            type="button"
            aria-expanded={open}
            aria-haspopup="listbox"
            data-testid="locality-filter"
            className={cn(
              'map-touch inline-flex w-fit max-w-full items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors',
              selected.length > 0
                ? 'border-primary bg-primary text-primary-foreground'
                : 'border-border bg-background text-foreground hover:bg-accent',
            )}
          >
            <span className="truncate">{label}</span>
            <ChevronDown className="size-3.5 shrink-0 opacity-70" />
          </button>
        </PopoverTrigger>
        <PopoverContent align="start" sideOffset={6} className="z-[1500] w-72 p-1.5">
          <Command className="rounded-lg">
            <CommandInput placeholder="Caută localitate..." />
            <CommandList>
              <CommandEmpty>Fără localități</CommandEmpty>
              {selected.length > 0 && (
                <CommandGroup heading="Toate localitățile">
                  <CommandItem
                    value="__all__"
                    data-testid="locality-reset"
                    onSelect={() => {
                      onClear();
                      setOpen(false);
                    }}
                  >
                    <X className="size-4 opacity-60" />
                    <span>Resetează</span>
                  </CommandItem>
                </CommandGroup>
              )}
              <CommandGroup heading="Localități">
                {localities.map((locality) => {
                  const active = selected.includes(locality);
                  return (
                    <CommandItem
                      key={locality}
                      value={locality}
                      data-checked={active}
                      data-testid="locality-option"
                      onSelect={() => onToggle(locality)}
                    >
                      <span className="truncate">{locality}</span>
                    </CommandItem>
                  );
                })}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
}
