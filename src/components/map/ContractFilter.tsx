'use client';

import { cn } from '@/lib/utils';
import type { ContractFilter as ContractFilterValue } from '@/types/data';

interface ContractFilterProps {
  selected: ContractFilterValue;
  onChange: (filter: ContractFilterValue) => void;
}

const OPTIONS: { value: ContractFilterValue; label: string }[] = [
  { value: 'all', label: 'Toate' },
  { value: 'contractate', label: 'Contractate' },
  { value: 'necontractate', label: 'Necontractate' },
];

/** Segmented control: Toate / Contractate / Necontractate (t_471dad64). */
export function ContractFilter({ selected, onChange }: ContractFilterProps) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        Contract
      </span>
      <div
        role="group"
        aria-label="Statusul contractului"
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
