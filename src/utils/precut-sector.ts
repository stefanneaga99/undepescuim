import type { Water } from '@/types/data';
import type { MapSelectionFocus } from '@/utils/contract-sector';
import { contractAtFraction, fractionAtPoint, partLength } from '@/utils/river-course';

/**
 * Pre-cut river sectors (river geometry v2, docs/plans/river-geometry-v2.md
 * D7 / T4.1): the pipeline writes each resolved sector's OWN geometry with
 * `geometryKind: 'sector'`. Such a water is drawn and selected as itself —
 * never sliced out of a group owner's course by `sectorStart`/`course_frac`.
 */

type LineParts = [number, number][][];

/** A water whose geometry is its own pre-cut sector. */
export type PrecutWater = Water & { geometryKind: 'sector'; geometry: NonNullable<Water['geometry']> };

function lineParts(water: Water): LineParts | null {
  const g = water.geometry;
  if (!g) return null;
  if (g.type === 'LineString') return [g.coordinates as [number, number][]];
  if (g.type === 'MultiLineString') return g.coordinates as [number, number][][];
  return null;
}

/** True when the water carries its own pre-cut sector line geometry. */
export function isPrecutSector(water: Water | null | undefined): water is PrecutWater {
  if (!water || water.geometryKind !== 'sector') return false;
  const parts = lineParts(water);
  return parts !== null && parts.some((part) => part.length >= 2);
}

/** Point halfway along the geometry (by length), for the unverified marker. */
export function precutMidpoint(water: Water): [number, number] | null {
  const parts = lineParts(water);
  if (!parts) return null;
  const total = parts.reduce((sum, part) => sum + partLength(part), 0);
  let remaining = total / 2;
  for (const part of parts) {
    for (let i = 0; i < part.length - 1; i += 1) {
      const [x1, y1] = part[i];
      const [x2, y2] = part[i + 1];
      const seg = partLength([part[i], part[i + 1]]);
      if (remaining <= seg) {
        const t = seg === 0 ? 0 : remaining / seg;
        return [x1 + (x2 - x1) * t, y1 + (y2 - y1) * t];
      }
      remaining -= seg;
    }
  }
  const last = parts[parts.length - 1];
  return last && last.length ? last[last.length - 1] : null;
}

/**
 * Focus for a pre-cut sector, using the same union as
 * `resolveMapSelectionFocus`: a `resolved` sector is verified over its whole
 * own geometry; a `review` sector keeps the unverified presentation.
 */
export function precutFocus(water: Water): MapSelectionFocus {
  if (water.sectorStatus === 'resolved') {
    return { kind: 'verified-sector-focus', interval: [0, 1] };
  }
  return {
    kind: 'feature-selected-unverified-sector',
    referencePoint: precutMidpoint(water),
    accessibleLabel: `Locație de referință selectată pentru ${water.name}. Geometria exactă a sectorului nu este verificată.`,
  };
}

/** Rendered length of a pre-cut sector in km (0 for non-line geometry). */
export function precutLengthKm(water: Water): number {
  const parts = lineParts(water);
  return parts ? parts.reduce((sum, part) => sum + partLength(part), 0) : 0;
}

/**
 * Draw order for the base layer: legacy waters keep their order and come
 * first; pre-cut sectors follow, LONGEST first, so short sectors are drawn
 * last (on top) and win clicks where sectors overlap.
 */
export function orderForRender<T extends Water>(waters: T[]): T[] {
  const legacy: T[] = [];
  const precut: { water: T; km: number; index: number }[] = [];
  waters.forEach((water, index) => {
    if (isPrecutSector(water)) precut.push({ water, km: precutLengthKm(water), index });
    else legacy.push(water);
  });
  precut.sort((a, b) => b.km - a.km || a.index - b.index);
  return [...legacy, ...precut.map((p) => p.water)];
}

/**
 * The slug a click on a base-layer feature selects. A pre-cut sector selects
 * itself; a legacy water resolves the clicked fraction along its full course
 * to the contract owning that stretch (`contractAtFraction`), as before.
 */
export function clickSelection(
  feature: { slug: string; name: string },
  clicked: [number, number] | null,
  allWaters: Water[],
  fallbackGeometry?: Water['geometry'],
): string {
  const original = allWaters.find((w) => w.slug === feature.slug);
  if (isPrecutSector(original)) return feature.slug;
  if (clicked) {
    const g = original?.geometry ?? fallbackGeometry;
    if (g && (g.type === 'MultiLineString' || g.type === 'LineString')) {
      const parts = g.type === 'MultiLineString'
        ? (g.coordinates as [number, number][][])
        : [g.coordinates as [number, number][]];
      const frac = fractionAtPoint(parts, clicked);
      if (frac !== null) {
        const contract = contractAtFraction(feature, frac, allWaters);
        if (contract) return contract.slug;
      }
    }
  }
  return feature.slug;
}
