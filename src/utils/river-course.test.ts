// @vitest-environment node
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import {
  waterKey,
  groupKeyOf,
  sameRiver,
  haversineKm,
  partLength,
  orderParts,
  sliceMultiLine,
  fractionAtPoint,
  isMainCourse,
  courseRank,
  contractGroup,
  contractAtFraction,
  contractInterval,
} from '@/utils/river-course';
import type { Water } from '@/types/data';

function water(over: Partial<Water>): Water {
  return {
    slug: 'w',
    name: 'Râul Test',
    judet: 'Cluj',
    type: 'ape',
    subtype: 'rau',
    coordinates: [23.6, 46.77],
    bbox: [23.0, 46.0, 24.0, 47.0],
    asociatie: null,
    ...over,
  } as Water;
}

describe('waterKey / groupKeyOf / sameRiver', () => {
  it('strips generic river prefixes and diacritics', () => {
    expect(waterKey('Râul Oltul superior')).toBe('oltul');
    expect(waterKey('Pârâul Buzăielului')).toBe('buzaielului'); // waterKey strips diacritics
  });

  it('strips diacritics and lowercases', () => {
    expect(waterKey('Lacul Vidraru')).toBe('vidraru');
  });

  it('prefers the exact riverGroup over the fuzzy prefix', () => {
    expect(groupKeyOf({ riverGroup: 'siret', name: 'Râul Sirețel' })).toBe('siret');
    expect(groupKeyOf({ name: 'Râul Sirețel' })).toBe('siretel'); // diacritics stripped
  });

  it('sameRiver shares the 5-char prefix', () => {
    expect(sameRiver('oltul', 'oltul')).toBe(true);
    expect(sameRiver('buzaielului', 'buzaiel')).toBe(true);
    expect(sameRiver('', 'oltul')).toBe(false);
    expect(sameRiver('buzau', 'buzau')).toBe(true);
    expect(sameRiver('buzau', 'bistrita')).toBe(false);
    expect(sameRiver('olt', 'oltul')).toBe(false); // a 3-char key is not a 5-char prefix
  });
});

describe('haversineKm / partLength', () => {
  it('returns 0 for identical points', () => {
    expect(haversineKm([23.0, 46.0], [23.0, 46.0])).toBe(0);
  });

  it('1 degree of latitude ≈ 111.2 km', () => {
    expect(haversineKm([23.0, 46.0], [23.0, 47.0])).toBeCloseTo(111.19, 1);
  });

  it('partLength sums the segment distances', () => {
    const coords: [number, number][] = [[23.0, 46.0], [23.0, 47.0], [23.0, 48.0]];
    expect(partLength(coords)).toBeCloseTo(222.39, 0);
  });
});

describe('orderParts', () => {
  it('passes through a single part', () => {
    const p: [number, number][][] = [[[26.0, 45.0], [26.1, 45.1]]];
    expect(orderParts(p)).toBe(p);
  });

  it('orders scrambled multi-line parts source→mouth (N→S)', () => {
    // two parts, input order scrambled; river flows from lat 46 down to 45
    const mouth: [number, number][] = [[26.1, 45.0], [26.1, 45.1]];
    const source: [number, number][] = [[26.0, 45.9], [26.0, 46.0]];
    const ordered = orderParts([mouth, source]);
    expect(ordered[0][0]).toEqual([26.0, 45.9]); // source part first
    expect(ordered[1][0]).toEqual([26.1, 45.0]); // mouth part last
  });
});

describe('sliceMultiLine', () => {
  const course: [number, number][][] = [
    [[26.0, 46.0], [26.0, 45.9], [26.0, 45.8]],   // ~33 km
    [[26.0, 45.8], [26.0, 45.7], [26.0, 45.6]],   // ~22 km
  ];

  it('returns the whole geometry for [0, 1]', () => {
    const out = sliceMultiLine(course, 0, 1);
    expect(out.flat().length).toBeGreaterThanOrEqual(course.flat().length);
  });

  it('returns only the second half for [0.5, 1]', () => {
    const out = sliceMultiLine(course, 0.5, 1);
    expect(out.length).toBeGreaterThan(0);
    // first coordinate of the slice is at ~45.8+ lat (second half of the course)
    const first = out[0][0];
    expect(first[1]).toBeLessThanOrEqual(45.8);
  });

  it('returns [] for a zero-length geometry', () => {
    expect(sliceMultiLine([], 0, 1)).toEqual([]);
  });

  it('returns [] when the slice window is outside the course', () => {
    expect(sliceMultiLine(course, 2, 3)).toEqual([]);
  });
});

describe('fractionAtPoint', () => {
  const course: [number, number][][] = [
    [[26.0, 46.0], [26.0, 45.5]],  // 55.6 km
    [[26.0, 45.5], [26.0, 45.0]],  // 55.6 km
  ];

  it('returns ~0 at the source and ~1 at the mouth', () => {
    expect(fractionAtPoint(course, [26.0, 46.0])).toBeCloseTo(0, 3);
    expect(fractionAtPoint(course, [26.0, 45.0])).toBeCloseTo(1, 3);
  });

  it('returns ~0.5 mid-course', () => {
    expect(fractionAtPoint(course, [26.0, 45.5])).toBeCloseTo(0.5, 3);
  });

  it('returns null for an unmeasurable geometry', () => {
    expect(fractionAtPoint([], [26.0, 45.5])).toBeNull();
  });
});

describe('isMainCourse / courseRank', () => {
  it('rejects tributary-looking prefixes', () => {
    expect(isMainCourse('Râul Buzău')).toBe(true);
    expect(isMainCourse('Valea Pojorâtei')).toBe(false);
    expect(isMainCourse('Pârâul Buzăielului')).toBe(false);
    expect(isMainCourse('Pârâu Buzăul Mijlociu')).toBe(false);
  });

  it('ranks superior < mijlociu < inferior < plain', () => {
    expect(courseRank('Râul Oltul superior')).toBe(0);
    expect(courseRank('Râul Zăbala Superioară')).toBe(0);
    expect(courseRank('Râul Putna Mijlocie')).toBe(1);
    expect(courseRank('Pârâu Buzăul Mijlociu')).toBe(1);
    expect(courseRank('Râul Oltul inferior')).toBe(2);
    expect(courseRank('Râul Olt')).toBe(3);
  });
});

describe('contractGroup / contractAtFraction / contractInterval', () => {
  const all = [
    water({ slug: 'olt-sup', name: 'Râul Oltul superior', riverGroup: 'olt', course_frac: 0.1 }),
    water({ slug: 'olt-mij', name: 'Râul Oltul mijlociu', riverGroup: 'olt', course_frac: 0.5 }),
    water({ slug: 'olt-inf', name: 'Râul Oltul inferior', riverGroup: 'olt', course_frac: 0.9 }),
    water({ slug: 'alt', name: 'Râul Alt', riverGroup: 'alt', course_frac: 0.5 }),
    water({ slug: 'valea', name: 'Valea Oltului', riverGroup: 'olt' }), // prefix → excluded
  ];

  it('groups by exact riverGroup, excluding prefix-named tributaries', () => {
    const g = contractGroup(all[0], all);
    expect(g.map((w) => w.slug).sort()).toEqual(['olt-inf', 'olt-mij', 'olt-sup']);
  });

  it('resolves the owning contract by Voronoi fraction', () => {
    expect(contractAtFraction({ slug: 'olt-sup' }, 0.05, all)?.slug).toBe('olt-sup');
    expect(contractAtFraction({ slug: 'olt-mij' }, 0.3, all)?.slug).toBe('olt-mij');
    expect(contractAtFraction({ slug: 'olt-mij' }, 0.7, all)?.slug).toBe('olt-inf');
  });

  it('prefers exact sector intervals over Voronoi', () => {
    const withSectors = [
      water({ slug: 'a', name: 'Râul X', riverGroup: 'x', sectorStart: 0.0, sectorEnd: 1.0 }),
      water({ slug: 'b', name: 'Râul X sub', riverGroup: 'x', sectorStart: 0.0, sectorEnd: 0.5 }),
    ];
    expect(contractAtFraction({ slug: 'b' }, 0.1, withSectors)?.slug).toBe('b');
    expect(contractAtFraction({ slug: 'b' }, 0.8, withSectors)?.slug).toBe('a');
  });

  it('returns null for a single-contract river', () => {
    expect(contractAtFraction({ slug: 'alt' }, 0.5, all)).toBeNull();
  });

  it('contractInterval honors declared sectors', () => {
    const w = water({ slug: 'b', name: 'Râul X sub', riverGroup: 'x', sectorStart: 0.0, sectorEnd: 0.5 });
    expect(contractInterval(w, [w, water({ slug: 'a', name: 'Râul X', riverGroup: 'x' })])).toEqual([0, 0.5]);
  });

  it('contractInterval is the whole course for single-contract rivers', () => {
    expect(contractInterval(all[3], all)).toEqual([0, 1]);
  });

  it('contractInterval computes Voronoi midpoints for multi-contract rivers', () => {
    expect(contractInterval(all[0], all)[0]).toBeCloseTo(0, 5);
    expect(contractInterval(all[0], all)[1]).toBeCloseTo(0.3, 5); // mid(0.1, 0.5)
    expect(contractInterval(all[2], all)[0]).toBeCloseTo(0.7, 5);
    expect(contractInterval(all[2], all)[1]).toBeCloseTo(1, 5);
  });
});

// ---------------------------------------------------------------------------
// PARITY GOLDEN TEST (plan §3.6): the shared winding fixture must produce the
// SAME numbers as scripts/_mapping_common.py. Golden values live in
// tests/fixtures/parity_expectations.json — computed from the Python
// implementation and asserted equal on BOTH sides (see
// tests/test_parity_vs_frontend.py). Any TS↔Python drift fails here.
// ---------------------------------------------------------------------------
describe('parity with the Python pipeline (shared fixtures)', () => {
  const fixturePath = (name: string) => path.resolve(process.cwd(), 'tests', 'fixtures', name);

  it('matches the Python golden fractions on the winding MultiLineString', () => {
    const fc = JSON.parse(readFileSync(fixturePath('winding_river.geojson'), 'utf-8'));
    const golden = JSON.parse(readFileSync(fixturePath('parity_expectations.json'), 'utf-8'));
    const geom = fc.features[0].geometry as { type: 'MultiLineString'; coordinates: [number, number][][] };
    const parts = geom.coordinates;

    // ordered-course endpoints
    const ordered = orderParts(parts);
    expect(ordered[0][0]).toEqual(golden.ordered_course.first_point);
    expect(ordered[ordered.length - 1][ordered[ordered.length - 1].length - 1]).toEqual(
      golden.ordered_course.last_point,
    );
    expect(ordered.map((p) => p.length)).toEqual(golden.ordered_course.part_point_counts);

    // fraction_at_point parity
    for (const { point, fraction } of golden.fraction_at_point) {
      expect(fractionAtPoint(parts, point as [number, number])).toBeCloseTo(fraction, 6);
    }
  });
});
