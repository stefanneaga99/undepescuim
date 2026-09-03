import type { Water } from '@/types/data';

/**
 * Collapse exact physical candidates to one painted line without losing the
 * source records that may select it. Legal sectors are intentionally not
 * inferred here: the representative always retains the complete candidate.
 */
export function dedupePhysicalPreviewWaters(waters: Water[]): Water[] {
  const byKey = new Map<string, Water>();
  for (const water of waters) {
    const sourceSlug = water.physicalSourceSlug ?? water.slug;
    const geometryKey = water.physicalGeometryHash ?? water.slug;
    const key = `${water.physicalRiverGroup ?? 'ungrouped'}|${geometryKey}`;
    const existing = byKey.get(key);
    if (!existing) {
      byKey.set(key, { ...water, physicalAliases: [sourceSlug] });
      continue;
    }
    const aliases = existing.physicalAliases ?? [];
    if (!aliases.includes(sourceSlug)) {
      byKey.set(key, { ...existing, physicalAliases: [...aliases, sourceSlug] });
    }
  }
  return [...byKey.values()];
}

export function physicalPreviewSelection(water: Water, selectedSlug: string | null): boolean {
  if (!selectedSlug) return false;
  return (water.physicalAliases ?? [water.physicalSourceSlug ?? water.slug]).includes(selectedSlug);
}