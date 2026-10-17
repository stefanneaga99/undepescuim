'use client';

import { useEffect, useState } from 'react';
import type { Water } from '@/types/data';
import { isPrecutSector } from '@/utils/precut-sector';
import { loadSectorEvidence, osmDate, type SectorEvidenceEntry } from '@/lib/sector-evidence';

export interface SectorEvidenceView {
  readonly entry: SectorEvidenceEntry;
  /** `YYYY-MM-DD` of the OSM snapshot, or null. */
  readonly osmDate: string | null;
}

/**
 * Evidence for a pre-cut sector's card block (T4.3). Only a pre-cut water
 * triggers the lazy fetch; anything else — or a water missing from the file —
 * yields null, which hides the block.
 */
export function useSectorEvidence(water: Water | null | undefined): SectorEvidenceView | null {
  const precut = isPrecutSector(water);
  const slug = water?.slug ?? null;
  const [state, setState] = useState<{ slug: string; view: SectorEvidenceView | null } | null>(null);

  useEffect(() => {
    if (!precut || !slug) return;
    let alive = true;
    loadSectorEvidence().then((evidence) => {
      if (!alive) return;
      const entry = evidence?.sectors[slug];
      setState({ slug, view: entry ? { entry, osmDate: osmDate(evidence) } : null });
    });
    return () => {
      alive = false;
    };
  }, [precut, slug]);

  return precut && state?.slug === slug ? state.view : null;
}
