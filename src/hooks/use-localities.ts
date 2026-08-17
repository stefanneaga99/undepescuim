'use client';

import { useMemo } from 'react';
import { useMapStore } from '@/stores/map-store';

/**
 * Normalization key used to dedupe the locality list (t_f6445fda).
 *
 * The dropdown must never render two rows that LOOK identical. Raw locality
 * values in the data can differ in ways that are invisible to the user:
 * trailing/leading whitespace ('Brașov ' vs 'Brașov'), case ('BRASOV'),
 * or diacritic encoding/missing diacritics ('Brasov' vs 'Brașov') — each
 * variants yields a SEPARATE `Set` entry with the plain exact-string dedup,
 * so the same place shows up twice. Folding on a normalized key (NFC →
 * trim → lowercase → strip combining diacritics) collapses those variants
 * into one option while keeping the first-seen (canonical) spelling for
 * display.
 */
function localityKey(locality: string): string {
  return locality
    .normalize('NFC')
    .trim()
    .toLocaleLowerCase('ro')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');
}

/**
 * Derived (t_dd918db7): sorted, deduplicated locality (UAT) list for the
 * CURRENT county selection. Locality is county-scoped — same-name UATs in
 * different counties (Călărași ×4, Unirea ×4) never collide because the list
 * is derived only from waters whose judet is selected. Waters without a
 * resolved locality simply contribute nothing.
 *
 * t_f6445fda: dedup is case/whitespace/diacritic-insensitive — visually
 * identical locality names collapse to a single option.
 *
 * Empty when no county is selected — the UI hides the locality control
 * entirely in that case (locality is meaningless without a county).
 */
export function useLocalities(): string[] {
  const waters = useMapStore((s) => s.waters);
  const uncontracted = useMapStore((s) => s.uncontracted);
  const countyFilter = useMapStore((s) => s.countyFilter);

  return useMemo(() => {
    if (countyFilter.length === 0) return [];
    const displayByKey = new Map<string, string>();
    for (const w of [...waters, ...uncontracted]) {
      if (!countyFilter.includes(w.judet)) continue;
      if (!w.locality) continue;
      const display = w.locality.trim();
      if (!display) continue;
      const key = localityKey(display);
      if (!displayByKey.has(key)) displayByKey.set(key, display);
    }
    return [...displayByKey.values()].sort((a, b) => a.localeCompare(b, 'ro'));
  }, [waters, uncontracted, countyFilter]);
}