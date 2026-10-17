// @vitest-environment node
import { describe, expect, it } from 'vitest';
import {
  clickSelection,
  isPrecutSector,
  orderForRender,
  precutFocus,
  precutLengthKm,
  precutMidpoint,
} from '@/utils/precut-sector';
import { partLength } from '@/utils/river-course';
import type { Water } from '@/types/data';

function water(over: Partial<Water>): Water {
  return {
    slug: 'water',
    name: 'Râul Test',
    judet: 'Harghita',
    type: 'ape',
    subtype: 'rau',
    coordinates: [25, 46],
    bbox: [24, 45, 26, 47],
    asociatie: null,
    ...over,
  } as Water;
}

const LINE: [number, number][] = [[25, 46], [25.1, 46], [25.2, 46]];

function sector(slug: string, coords: [number, number][], over: Partial<Water> = {}): Water {
  return water({
    slug,
    geometry: { type: 'LineString', coordinates: coords },
    geometryKind: 'sector',
    sectorStatus: 'resolved',
    riverGroup: 'test',
    ...over,
  });
}

describe('isPrecutSector', () => {
  it('needs geometryKind sector and a drawable line', () => {
    expect(isPrecutSector(sector('a', LINE))).toBe(true);
    expect(isPrecutSector(sector('a', LINE, { geometry: { type: 'MultiLineString', coordinates: [LINE] } }))).toBe(true);
    expect(isPrecutSector(water({ geometry: { type: 'LineString', coordinates: LINE } }))).toBe(false);
    expect(isPrecutSector(sector('a', LINE, { geometry: undefined }))).toBe(false);
    expect(isPrecutSector(sector('a', [[25, 46]]))).toBe(false);
    expect(isPrecutSector(sector('a', LINE, {
      geometry: { type: 'Polygon', coordinates: [[[25, 46], [25.1, 46], [25, 46.1], [25, 46]]] },
    }))).toBe(false);
    expect(isPrecutSector(null)).toBe(false);
    expect(isPrecutSector(undefined)).toBe(false);
  });
});

describe('precutFocus', () => {
  it('resolved sector → verified focus over its whole own geometry', () => {
    expect(precutFocus(sector('a', LINE))).toEqual({ kind: 'verified-sector-focus', interval: [0, 1] });
  });

  it('review sector → the existing unverified variant, marker at the geometry midpoint', () => {
    const focus = precutFocus(sector('a', LINE, { sectorStatus: 'review', name: 'Râul Geoagiu' }));
    expect(focus.kind).toBe('feature-selected-unverified-sector');
    if (focus.kind !== 'feature-selected-unverified-sector') throw new Error('unreachable');
    expect(focus.referencePoint![0]).toBeCloseTo(25.1, 6);
    expect(focus.referencePoint![1]).toBeCloseTo(46, 6);
    expect(focus.accessibleLabel).toBe(
      'Locație de referință selectată pentru Râul Geoagiu. Geometria exactă a sectorului nu este verificată.',
    );
  });
});

describe('precutMidpoint / precutLengthKm', () => {
  it('walks multi-part lines by length', () => {
    const w = sector('a', LINE, {
      geometry: { type: 'MultiLineString', coordinates: [[[25, 46], [25.1, 46]], [[25.1, 46], [25.3, 46]]] },
    });
    const mid = precutMidpoint(w)!;
    expect(mid[0]).toBeCloseTo(25.15, 4);
    expect(precutLengthKm(w)).toBeCloseTo(partLength([[25, 46], [25.1, 46], [25.3, 46]]), 6);
  });

  it('degenerate geometry', () => {
    expect(precutMidpoint(water({}))).toBeNull();
    expect(precutLengthKm(water({}))).toBe(0);
    expect(precutMidpoint(sector('a', [[25, 46], [25, 46]]))).toEqual([25, 46]);
    expect(precutMidpoint(sector('a', LINE, { geometry: { type: 'MultiLineString', coordinates: [] } }))).toBeNull();
  });
});

describe('orderForRender', () => {
  it('keeps legacy order first, then pre-cut sectors longest first (short ones on top)', () => {
    const legacy1 = water({ slug: 'l1' });
    const legacy2 = water({ slug: 'l2' });
    const short = sector('short', [[25, 46], [25.01, 46]]);
    const long = sector('long', [[25, 46], [25.5, 46]]);
    const mid = sector('mid', [[25, 46], [25.2, 46]]);
    const tie = sector('tie', [[25, 46], [25.2, 46]]);
    expect(orderForRender([short, legacy1, long, mid, legacy2, tie]).map((w) => w.slug))
      .toEqual(['l1', 'l2', 'long', 'mid', 'tie', 'short']);
  });
});

describe('clickSelection', () => {
  // a legacy shared course owned by 'owner' with two explicit contracts
  const course: [number, number][] = [[25, 46], [25.5, 46], [26, 46]];
  const owner = water({ slug: 'owner', name: 'Râul Olt', riverGroup: 'olt', geometry: { type: 'LineString', coordinates: course } });
  const upper = water({ slug: 'upper', name: 'Râul Olt superior', riverGroup: 'olt', sectorStart: 0, sectorEnd: 0.5 });
  const lower = water({ slug: 'lower', name: 'Râul Olt inferior', riverGroup: 'olt', sectorStart: 0.5, sectorEnd: 1 });

  it('a pre-cut sector selects itself, without fraction or owner lookup', () => {
    const pre = sector('pre', [[25.7, 46], [25.9, 46]], { name: 'Râul Olt', riverGroup: 'olt', sectorStart: 0, sectorEnd: 0.1 });
    const all = [owner, upper, lower, pre];
    expect(clickSelection({ slug: 'pre', name: pre.name }, [25.8, 46], all)).toBe('pre');
  });

  it('legacy behaviour is unchanged: the clicked fraction picks the owning contract', () => {
    const all = [owner, upper, lower];
    expect(clickSelection({ slug: 'owner', name: owner.name }, [25.9, 46], all)).toBe('lower');
    expect(clickSelection({ slug: 'owner', name: owner.name }, [25.1, 46], all)).toBe('upper');
  });

  it('falls back to the clicked feature without a point, geometry, or a contract', () => {
    expect(clickSelection({ slug: 'owner', name: owner.name }, null, [owner, upper])).toBe('owner');
    const lake = water({ slug: 'lake', subtype: 'lac', geometry: { type: 'Polygon', coordinates: [[[25, 46], [25.1, 46], [25, 46.1], [25, 46]]] } });
    expect(clickSelection({ slug: 'lake', name: 'Lac' }, [25.01, 46.01], [lake])).toBe('lake');
    // unknown slug: the rendered feature geometry is used
    expect(clickSelection({ slug: 'ghost', name: 'Ghost' }, [25.1, 46], [], { type: 'LineString', coordinates: course }))
      .toBe('ghost');
  });
});
