'use client';

import { useEffect, useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { useMapStore } from '@/stores/map-store';
import { useI18n } from '@/i18n/provider';
import { NEUTRAL_COLOR, COVERED_COLOR, UNCOVERED_COLOR, UNCONTRACTED_COLOR, UNCONTRACTED_LAKE_FILL } from '@/utils/colors';

interface LegendRow {
  color: string;
  label: string;
}

/**
 * Coverage legend (component_structure_plan.md §3.10).
 * - No association selected → single "Vedere neutră" (blue) row.
 * - Association selected → "Acoperit" (green) + "Neacoperit" (grey).
 * - Uncontracted overlay visible (t_471dad64) → teal "Necontractate" row.
 * - Mobile: collapsible dots (auto-collapse after 5s), floats above the open
 *   bottom sheet via --sheet-snap-h. Desktop: full labels, always visible.
 */
export function ColorLegend() {
  const coverageSlug = useMapStore((s) => s.selectedAssociationSlug);
  const contractFilter = useMapStore((s) => s.contractFilter);
  const { t } = useI18n();
  const [expanded, setExpanded] = useState(false);

  // Auto-collapse 5s after manual expansion (mobile-layout-spec §6.1).
  useEffect(() => {
    if (!expanded) return;
    const t = setTimeout(() => setExpanded(false), 5000);
    return () => clearTimeout(t);
  }, [expanded]);

  const showUncontracted = contractFilter !== 'contractate';
  const rows: LegendRow[] = [
    ...(coverageSlug === null
      ? [{ color: NEUTRAL_COLOR, label: t('legend.neutralView') }]
      : [
          { color: COVERED_COLOR, label: t('legend.covered') },
          { color: UNCOVERED_COLOR, label: t('legend.uncovered') },
        ]),
    ...(showUncontracted
      ? [
          { color: UNCONTRACTED_COLOR, label: t('legend.uncontractedRivers') },
          { color: UNCONTRACTED_LAKE_FILL, label: t('legend.uncontractedLakes') },
        ]
      : []),
  ];

  return (
    <div
      className="absolute right-3 z-[1000] select-none"
      // Keep the layout anchor stable. Moving an absolutely positioned control
      // by changing `bottom` is still reported as CLS when the sheet snap
      // settles after the user's tap (especially under mobile CPU throttle).
      // Transforms preserve the same visual offset but are compositor-only.
      style={{ bottom: '12px', transform: 'translateY(calc(-1 * var(--sheet-snap-h, 0vh)))' }}
    >
      {/* Mobile: collapsible dots / labels */}
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        aria-expanded={expanded}
        aria-label="Legendă culori"
        className="map-touch rounded-lg bg-black/60 px-2.5 py-1.5 text-xs text-white shadow-md backdrop-blur-sm md:hidden"
      >
        {!expanded ? (
          <span className="flex items-center gap-1.5">
            {rows.map((r) => (
              <span
                key={r.label}
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: r.color }}
              />
            ))}
            <ChevronUp className="h-3 w-3 opacity-70" />
          </span>
        ) : (
          <span className="flex flex-col items-start gap-1">
            {rows.map((r) => (
              <span key={r.label} className="flex items-center gap-1.5">
                <span
                  className="h-2.5 w-2.5 rounded-sm"
                  style={{ backgroundColor: r.color }}
                />
                {r.label}
              </span>
            ))}
            <ChevronDown className="h-3 w-3 opacity-70" />
          </span>
        )}
      </button>

      {/* Desktop: full labels, always visible */}
      <div className="hidden flex-col gap-1.5 rounded-lg border bg-white/90 px-3 py-2 text-xs shadow-md backdrop-blur-sm md:flex dark:bg-neutral-900/90">
        {rows.map((r) => (
          <span key={r.label} className="flex items-center gap-2">
            <span
              className="h-3 w-3 rounded-sm"
              style={{ backgroundColor: r.color }}
            />
            {r.label}
          </span>
        ))}
      </div>
    </div>
  );
}
