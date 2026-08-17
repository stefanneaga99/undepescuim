'use client';

import { cn } from '@/lib/utils';
import { useI18n } from '@/i18n/provider';
import type { ContractFilter as ContractFilterValue } from '@/types/data';

interface ContractFilterProps {
  selected: ContractFilterValue;
  onChange: (filter: ContractFilterValue) => void;
}

const OPTIONS: { value: ContractFilterValue; labelKey: 'filters.all' | 'filters.contracted' | 'filters.uncontracted' }[] = [
  { value: 'all', labelKey: 'filters.all' },
  { value: 'contractate', labelKey: 'filters.contracted' },
  { value: 'necontractate', labelKey: 'filters.uncontracted' },
];

/** Segmented control: Toate / Contractate / Necontractate (t_471dad64). */
export function ContractFilter({ selected, onChange }: ContractFilterProps) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        {t('filters.contractLabel')}
      </span>
      <div
        role="group"
        aria-label={t('filters.contractAria')}
        data-testid="contract-filter"
        className="inline-flex w-fit rounded-full border bg-muted/60 p-0.5"
      >
        {OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            aria-pressed={selected === opt.value}
            data-testid="contract-option"
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
