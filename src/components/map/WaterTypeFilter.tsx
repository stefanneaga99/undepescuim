'use client';

import { cn } from '@/lib/utils';
import { useI18n } from '@/i18n/provider';
import type { WaterTypeFilter as WaterTypeFilterValue } from '@/types/data';

interface WaterTypeFilterProps {
  selected: WaterTypeFilterValue;
  onChange: (type: WaterTypeFilterValue) => void;
}

const OPTIONS: { value: WaterTypeFilterValue; labelKey: 'filters.all' | 'filters.lakes' | 'filters.rivers' }[] = [
  { value: 'all', labelKey: 'filters.all' },
  { value: 'lac', labelKey: 'filters.lakes' },
  { value: 'rau', labelKey: 'filters.rivers' },
];

/** Segmented control: Toate / Lacuri / Râuri. Fully controlled. */
export function WaterTypeFilter({ selected, onChange }: WaterTypeFilterProps) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        {t('filters.typeLabel')}
      </span>
      <div
        role="group"
        aria-label={t('filters.typeAria')}
        data-testid="type-filter"
        className="inline-flex w-fit rounded-full border bg-muted/60 p-0.5"
      >
        {OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            aria-pressed={selected === opt.value}
            data-testid="type-option"
            data-value={opt.value}
            className={cn(
              'map-touch select-none rounded-full px-3 py-1 text-xs font-medium transition-colors',
              selected === opt.value
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground',
            )}
          >
            {t(opt.labelKey)}
          </button>
        ))}
      </div>
    </div>
  );
}
