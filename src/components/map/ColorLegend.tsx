'use client';

import { useEffect, useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { useMapStore } from '@/stores/map-store';
import { NEUTRAL_COLOR, COVERED_COLOR, UNCOVERED_COLOR } from '@/utils/colors';

interface LegendRow {
  color: string;
  label: string;
}

/**
 * Coverage legend (component_structure_plan.md §3.10).
 * - No association selected → single "Vedere neutră" (blue) row.
 * - Association selected → "Acoperit" (green) + "Neacoperit" (grey).
 * - Mobile: collapsible dots (auto-collapse after 5s), floats above the open
 *   bottom sheet via --sheet-snap-h. Desktop: full labels, always visible.
 */
export function ColorLegend() {
  const coverageSlug = useMapStore((s) => s.selectedAssociationSlug);
  const [expanded, setExpanded] = useState(false);

  // Auto-collapse 5s after manual expansion (mobile-layout-spec §6.1).
  useEffect(() => {
    if (!expanded) return;
    const t = setTimeout(() => setExpanded(false), 5000);
    return () => clearTimeout(t);
  }, [expanded]);

  const rows: LegendRow[] =
    coverageSlug === null
      ? [{ color: NEUTRAL_COLOR, label: 'Vedere neutră' }]
      : [
          { color: COVERED_COLOR, label: 'Acoperit' },
          { color: UNCOVERED_COLOR, label: 'Neacoperit' },
        ];

  return (
    <div
      className="absolute right-3 z-[1000] select-none"
      style={{ bottom: 'calc(var(--sheet-snap-h, 0vh) + 12px)' }}
    >
      {/* Mobile: collapsible dots / labels */}
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        aria-expanded={expanded}
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
      <div className="hidden flex-col gap-1.5 rounded-lg border bg-white/90 px-3 py-2 text-xs shadow-md backdrop-blur-sm md:flex">
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
