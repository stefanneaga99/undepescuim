import type { Water } from '@/types/data';

/**
 * Keep one rendered line for each physical candidate. Preview artifacts retain
 * every record for provenance, but repeated candidates (especially the shared
 * Buzău course) must not be painted on top of one another.
 */
export function dedupePhysicalPreview(waters: Water[]): Water[] {
  const seen = new Set<string>();
  return waters.filter((water) => {
    const hash = water.physicalProvenance?.geometryHash;
    const key = hash ? `${water.riverGroup ?? 'ungrouped'}:${hash}` : water.slug;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

/**
 * A preview candidate is never a legal sector. Only explicit intervals copied
 * from the artifact may be used by callers; this helper deliberately does not
 * derive bounds from names, counties, localities, or course position.
 */
export function isUnverifiedPhysicalPreview(water: Water): boolean {
  return water.physicalPreview === true && water.legalStatus === 'legal sector unverified';
}
