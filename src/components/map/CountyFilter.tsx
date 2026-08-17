'use client';

import { cn } from '@/lib/utils';
import { useI18n } from '@/i18n/provider';

interface CountyFilterProps {
  /** all counties (from useCounties — never filtered) */
  counties: string[];
  /** currently toggled counties */
  selected: string[];
  onToggle: (county: string) => void;
}

/**
 * Multi-select county chips, derived from data (never hardcoded).
 * Mobile: horizontally scrollable row. Desktop: wrapping chips.
 * "Toate județele" indicator shows while no county is selected.
 */
export function CountyFilter({ counties, selected, onToggle }: CountyFilterProps) {
  const { t } = useI18n();
  if (counties.length === 0) return null;

  return (
    <div className="flex flex-col gap-1">
      <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        {t('filters.countyLabel')}
      </span>
      <div className="no-scrollbar flex items-center gap-1.5 overflow-x-auto md:flex-wrap md:overflow-visible">
        {selected.length === 0 && (
          <span className="shrink-0 cursor-default rounded-full bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground">
            {t('filters.allCounties')}
          </span>
        )}
        {counties.map((county) => {
          const active = selected.includes(county);
          return (
            <button
              key={county}
              type="button"
              onClick={() => onToggle(county)}
              aria-pressed={active}
              data-testid="county-chip"
              data-county={county}
              className={cn(
                'map-touch shrink-0 select-none rounded-full border px-2.5 py-1 text-xs font-medium transition-colors',
                active
                  ? 'border-primary bg-primary text-primary-foreground'
                  : 'border-border bg-background text-foreground hover:bg-accent',
              )}
            >
              {county}
            </button>
          );
        })}
      </div>
    </div>
  );
}
