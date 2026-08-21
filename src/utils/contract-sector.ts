import type { Water } from '@/types/data';
import { contractGroup, contractInterval, partLength, sliceMultiLine } from '@/utils/river-course';

export type SectorMeasurementMethod = 'explicit-interval' | 'voronoi-fallback' | 'unmeasurable';

export type SectorMeasurement = {
  selectedSlug: string;
  ownerSlug: string | null;
  interval: [number, number] | null;
  renderedKm: number | null;
  method: SectorMeasurementMethod;
};

/** Return true only when both contract endpoints were explicitly supplied. */
export function hasExplicitSectorInterval(water: Water): boolean {
  return typeof water.sectorStart === 'number' && typeof water.sectorEnd === 'number';
}

function lineParts(water: Water): [number, number][][] | null {
  if (!water.geometry) return null;
  if (water.geometry.type === 'LineString') {
    return [water.geometry.coordinates as [number, number][]];
  }
  if (water.geometry.type === 'MultiLineString') {
    return water.geometry.coordinates as [number, number][][];
  }
  return null;
}

/**
 * Measure the geometry the map would paint for a selected contract.
 *
 * A Voronoi interval is intentionally reported as diagnostic fallback only:
 * course_frac locates a contract but does not prove contractual endpoints.
 */
export function measureContractSector(selected: Water, allWaters: Water[]): SectorMeasurement {
  const group = contractGroup(selected, allWaters);
  const owner = group.find((w) => lineParts(w) !== null) ?? null;
  const method: SectorMeasurementMethod = hasExplicitSectorInterval(selected)
    ? 'explicit-interval'
    : group.length > 1
      ? 'voronoi-fallback'
      : 'explicit-interval';

  if (!owner) {
    return {
      selectedSlug: selected.slug,
      ownerSlug: null,
      interval: null,
      renderedKm: null,
      method: 'unmeasurable',
    };
  }

  const interval = contractInterval(selected, allWaters);
  const parts = lineParts(owner);
  if (!parts) {
    return {
      selectedSlug: selected.slug,
      ownerSlug: owner.slug,
      interval,
      renderedKm: null,
      method,
    };
  }

  const renderedKm = sliceMultiLine(parts, interval[0], interval[1])
    .reduce((total, part) => total + partLength(part), 0);
  return { selectedSlug: selected.slug, ownerSlug: owner.slug, interval, renderedKm, method };
}
