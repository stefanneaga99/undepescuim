'use client';

import { useState } from 'react';
import { ChevronDown, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useI18n } from '@/i18n/provider';
import { localityKey } from '@/hooks/use-localities';
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
  /** display-name → water count for each locality (useLocalityCounts,
   *  keyed by the same normalized key as useLocalities) — t_e70099a9 */
  counts?: Map<string, number>;
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
export function LocalityFilter({
  localities,
  selected,
  counts,
  onToggle,
  onClear,
}: LocalityFilterProps) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);

  if (localities.length === 0) return null;

  const label =
    selected.length === 0
      ? t('filters.allLocalities')
      : selected.length <= 2
        ? selected.join(', ')
        : t('filters.localitiesCount', { n: selected.length });

  return (
    <div className="flex flex-col gap-1">
      <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        {t('filters.localityLabel')}
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
            <CommandInput placeholder={t('filters.searchLocality')} />
            <CommandList>
              <CommandEmpty>{t('filters.noLocalities')}</CommandEmpty>
              {selected.length > 0 && (
                <CommandGroup heading={t('filters.allLocalities')}>
                  <CommandItem
                    value="__all__"
                    data-testid="locality-reset"
                    onSelect={() => {
                      onClear();
                      setOpen(false);
                    }}
                  >
                    <X className="size-4 opacity-60" />
                    <span>{t('filters.reset')}</span>
                  </CommandItem>
                </CommandGroup>
              )}
              <CommandGroup heading={t('filters.localityLabel')}>
                {localities.map((locality) => {
                  const active = selected.includes(locality);
                  const count = counts?.get(localityKey(locality));
                  return (
                    <CommandItem
                      key={locality}
                      value={locality}
                      data-checked={active}
                      data-testid="locality-option"
                      data-count={count ?? ''}
                      onSelect={() => onToggle(locality)}
                    >
                      <span className="truncate">{locality}</span>
                      {count != null && (
                        <span
                          className="ml-auto shrink-0 rounded-full bg-muted px-1.5 py-0.5 text-[10px] font-medium tabular-nums text-muted-foreground"
                          data-testid="locality-count"
                        >
                          {count}
                        </span>
                      )}
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
