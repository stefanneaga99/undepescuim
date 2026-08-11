'use client';

import { cn } from '@/lib/utils';
import type { WaterTypeFilter as WaterTypeFilterValue } from '@/types/data';

interface WaterTypeFilterProps {
  selected: WaterTypeFilterValue;
  onChange: (type: WaterTypeFilterValue) => void;
}

const OPTIONS: { value: WaterTypeFilterValue; label: string }[] = [
  { value: 'all', label: 'Toate' },
  { value: 'lac', label: 'Lacuri' },
  { value: 'rau', label: 'Râuri' },
];

/** Segmented control: Toate / Lacuri / Râuri. Fully controlled. */
export function WaterTypeFilter({ selected, onChange }: WaterTypeFilterProps) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        Tip
      </span>
      <div
        role="group"
        aria-label="Tipul apei"
        className="inline-flex w-fit rounded-full border bg-muted/60 p-0.5"
      >
        {OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            aria-pressed={selected === opt.value}
            className={cn(
              'map-touch select-none rounded-full px-3 py-1 text-xs font-medium transition-colors',
              selected === opt.value
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground',
            )}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
