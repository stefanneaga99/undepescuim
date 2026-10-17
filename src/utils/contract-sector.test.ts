// @vitest-environment node
import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { hasExplicitSectorInterval, measureContractSector, resolveMapSelectionFocus } from '@/utils/contract-sector';
import { pointAtFraction } from '@/utils/river-course';
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

describe('measureContractSector', () => {
  it('only treats the documented Buzău/Covasna and Brașov endpoints as explicit', () => {
    const waters = JSON.parse(readFileSync('public/data/waters.json', 'utf8')) as Water[];
    expect(hasExplicitSectorInterval(waters.find((w) => w.slug === 'anpa-anpa-0261')!)).toBe(true);
    expect(hasExplicitSectorInterval(waters.find((w) => w.slug === 'romsilva-brasov-buzaul-superior')!)).toBe(true);
    for (const slug of ['anpa-anpa-0207', 'anpa-anpa-0210', 'anpa-anpa-0211', 'anpa-anpa-0214']) {
      expect(hasExplicitSectorInterval(waters.find((w) => w.slug === slug)!)).toBe(false);
    }
  });
  it('reports the current Târnava Mare fallback as inferred, not source-backed', () => {
    const waters = JSON.parse(readFileSync('public/data/waters.json', 'utf8')) as Water[];
    const selected = waters.find((w) => w.slug === 'anpa-anpa-0333');
    expect(selected).toBeTruthy();

    const result = measureContractSector(selected!, waters);

    expect(result).toMatchObject({
      selectedSlug: 'anpa-anpa-0333',
      ownerSlug: 'ks2vsbaf',
      interval: [0, 0.1343],
      method: 'voronoi-fallback',
    });
    expect(result.renderedKm).toBeGreaterThan(29);
    expect(result.renderedKm).toBeLessThan(31);
  });

  it('resolves the real Târnava member to one unverified reference marker', () => {
    const waters = JSON.parse(readFileSync('public/data/waters.json', 'utf8')) as Water[];
    const selected = waters.find((w) => w.slug === 'anpa-anpa-0333')!;
    const focus = resolveMapSelectionFocus(selected, waters);
    expect(focus).toMatchObject({ kind: 'feature-selected-unverified-sector' });
    if (focus.kind !== 'feature-selected-unverified-sector') throw new Error('expected unverified focus');
    expect(focus.referencePoint).toBeTruthy();
    expect(focus.accessibleLabel).toContain('Geometria exactă a sectorului nu este verificată');
    expect(selected.sectorStart).toBeUndefined();
    expect(selected.sectorEnd).toBeUndefined();
  });

  it('resolves only explicit sector endpoints to verified focus', () => {
    const owner = water({ slug: 'owner', riverGroup: 'x', geometry: { type: 'LineString', coordinates: [[25, 47], [25, 46]] } });
    const selected = water({ slug: 'selected', name: 'Râul X mijlociu', riverGroup: 'x', sectorStart: 0.25, sectorEnd: 0.5 });
    expect(resolveMapSelectionFocus(selected, [owner, selected])).toEqual({
      kind: 'verified-sector-focus', interval: [0.25, 0.5],
    });
  });

  it('uses the deduplicated physical preview as the reference course', () => {
    const selected = water({ slug: '0207', riverGroup: 'buzau', course_frac: 0.25 });
    const sibling = water({ slug: '0211', riverGroup: 'buzau', course_frac: 0.75 });
    const preview = water({
      slug: 'class2-preview-buzau',
      riverGroup: 'buzau',
      physicalPreview: true,
      physicalAliases: ['0207', '0211'],
      geometry: { type: 'LineString', coordinates: [[25, 47], [25, 46]] },
    });
    const focus = resolveMapSelectionFocus(selected, [selected, sibling], [preview]);
    expect(focus.kind).toBe('feature-selected-unverified-sector');
    if (focus.kind === 'feature-selected-unverified-sector') expect(focus.referencePoint).toEqual([25, 46.75]);
  });

  it('uses only the ledger-backed explicit physical projection as selected focus', () => {
    const selected = water({ slug: '0261', riverGroup: 'buzau', course_frac: 0.12 });
    const sibling = water({ slug: '0214', riverGroup: 'buzau', course_frac: 0.8 });
    const preview = water({
      slug: 'preview-buzau', riverGroup: 'buzau', physicalPreview: true,
      geometry: { type: 'LineString', coordinates: [[25, 47], [25, 46]] },
      physicalAliases: ['0214', '0261'],
      physicalSegments: [{
        sourceSlug: '0261', segmentId: 'c'.repeat(64), geometryHash: 'a'.repeat(64),
        start: 0.0774, end: 0.1641,
      }],
    });

    expect(resolveMapSelectionFocus(selected, [selected, sibling], [preview])).toEqual({
      kind: 'verified-sector-focus', interval: [0.0774, 0.1641], segmentId: 'c'.repeat(64),
      geometryHash: 'a'.repeat(64),
    });
    expect(resolveMapSelectionFocus(sibling, [selected, sibling], [preview]).kind).toBe(
      'feature-selected-unverified-sector',
    );
  });

  it('does not verify an alias spanning multiple physical courses without an exact selected identity', () => {
    const selected = water({ slug: 'selected', riverGroup: 'x', course_frac: 0.5 });
    const sibling = water({ slug: 'sibling', riverGroup: 'x', course_frac: 0.8 });
    const course = (fullId: string, segment: string, hash: string): Water => water({
      slug: `preview-${hash[0]}`, riverGroup: 'x', physicalPreview: true,
      physicalSegmentId: fullId, physicalGeometryHash: hash, physicalAliases: ['selected'],
      physicalSegments: [{ sourceSlug: 'selected', segmentId: segment, geometryHash: hash, start: 0.2, end: 0.4 }],
      geometry: { type: 'LineString', coordinates: [[25, 47], [25, 46]] },
    });
    const first = course('1'.repeat(64), 'a'.repeat(64), 'c'.repeat(64));
    const second = course('2'.repeat(64), 'b'.repeat(64), 'd'.repeat(64));
    second.physicalSegments = [];

    expect(resolveMapSelectionFocus(selected, [selected, sibling], [first, second]).kind).toBe(
      'feature-selected-unverified-sector',
    );
    expect(resolveMapSelectionFocus(selected, [selected, sibling], [first, second], first.physicalSegmentId)).toEqual({
      kind: 'verified-sector-focus', interval: [0.2, 0.4], segmentId: 'a'.repeat(64), geometryHash: 'c'.repeat(64),
    });
  });

  it('interpolates a reference point on the measured course', () => {
    expect(pointAtFraction([[[0, 0], [10, 0]]], 0.25)).toEqual([2.5, 0]);
    expect(pointAtFraction([], 0.5)).toBeNull();
    expect(pointAtFraction([[[0, 0], [0, 0]]], 0.5)).toBeNull();
  });

  it('uses an explicit interval instead of the Voronoi position', () => {
    const owner = water({
      slug: 'owner',
      name: 'Râul X',
      riverGroup: 'x',
      geometry: { type: 'LineString', coordinates: [[25, 47], [25, 46], [25, 45]] },
    });
    const selected = water({
      slug: 'selected',
      name: 'Râul X mijlociu',
      riverGroup: 'x',
      course_frac: 0.9,
      sectorStart: 0.25,
      sectorEnd: 0.5,
    });

    expect(measureContractSector(selected, [owner, selected])).toMatchObject({
      selectedSlug: 'selected',
      ownerSlug: 'owner',
      interval: [0.25, 0.5],
      method: 'explicit-interval',
    });
  });

  it('returns a structured non-measurement when no geometry owner exists', () => {
    const selected = water({ slug: 'missing', riverGroup: 'missing', course_frac: 0.4 });
    expect(measureContractSector(selected, [selected])).toEqual({
      selectedSlug: 'missing',
      ownerSlug: null,
      interval: null,
      renderedKm: null,
      method: 'unmeasurable',
    });
  });
});

describe('pre-cut sectors (river geometry v2, T4.1)', () => {
  const line: [number, number][] = [[25, 46], [25.1, 46], [25.2, 46]];
  const precut = (over: Partial<Water>) => water({
    slug: 'pre',
    riverGroup: 'test',
    geometry: { type: 'LineString', coordinates: line },
    geometryKind: 'sector',
    sectorStatus: 'resolved',
    sectorStart: 0.2,
    sectorEnd: 0.3,
    course_frac: 0.25,
    ...over,
  });
  // another member of the same group, so the legacy path would treat it as multi-contract
  const sibling = water({ slug: 'sib', riverGroup: 'test', geometry: { type: 'LineString', coordinates: line } });

  it('resolved → verified focus over its own geometry, whatever sectorStart/End say', () => {
    const w = precut({});
    expect(resolveMapSelectionFocus(w, [w, sibling])).toEqual({ kind: 'verified-sector-focus', interval: [0, 1] });
  });

  it('review → unverified focus with the reference marker on its own geometry', () => {
    const w = precut({ sectorStatus: 'review' });
    const focus = resolveMapSelectionFocus(w, [w, sibling]);
    expect(focus.kind).toBe('feature-selected-unverified-sector');
    if (focus.kind !== 'feature-selected-unverified-sector') throw new Error('unreachable');
    expect(focus.referencePoint![0]).toBeCloseTo(25.1, 6);
  });

  it('legacy members of the same group are unchanged', () => {
    const legacy = water({ slug: 'leg', riverGroup: 'test', sectorStart: 0.4, sectorEnd: 0.6 });
    expect(resolveMapSelectionFocus(legacy, [legacy, sibling])).toEqual({
      kind: 'verified-sector-focus',
      interval: [0.4, 0.6],
    });
  });

  it('measureContractSector reports the sector as its own explicit owner', () => {
    const w = precut({});
    const m = measureContractSector(w, [w, sibling]);
    expect(m).toMatchObject({ selectedSlug: 'pre', ownerSlug: 'pre', interval: [0, 1], method: 'explicit-interval' });
    expect(m.renderedKm).toBeGreaterThan(15);
    expect(m.renderedKm).toBeLessThan(16);
  });
});

describe('D8 partial switch: legacy members keep slicing the legacy owner', () => {
  const ownerLine: [number, number][] = [[25, 46], [25.5, 46], [26, 46]];
  const owner = water({ slug: 'owner', name: 'Râul Test', riverGroup: 'g', geometry: { type: 'LineString', coordinates: ownerLine } });
  // a pre-cut member listed BEFORE the owner: it must never be taken as the shared course
  const precut = water({
    slug: 'pre', name: 'Râul Test superior', riverGroup: 'g', geometryKind: 'sector', sectorStatus: 'resolved',
    geometry: { type: 'LineString', coordinates: [[25.1, 46.2], [25.2, 46.2]] }, course_frac: 0.2,
  });
  const legacy = water({ slug: 'leg', name: 'Râul Test inferior', riverGroup: 'g', sectorStart: 0.5, sectorEnd: 1 });

  it('measures a legacy member against the legacy owner, not a pre-cut sibling', () => {
    const m = measureContractSector(legacy, [precut, owner, legacy]);
    expect(m.ownerSlug).toBe('owner');
    expect(m.renderedKm).toBeGreaterThan(35); // half of the ~78 km owner line, not of the 7.7 km sector
  });

  it('places a legacy member\'s reference marker on the legacy owner', () => {
    const voronoi = water({ slug: 'vor', name: 'Râul Test mijlociu', riverGroup: 'g', course_frac: 0.5 });
    const focus = resolveMapSelectionFocus(voronoi, [precut, owner, voronoi]);
    expect(focus.kind).toBe('feature-selected-unverified-sector');
    if (focus.kind !== 'feature-selected-unverified-sector') throw new Error('unreachable');
    expect(focus.referencePoint![1]).toBeCloseTo(46, 6); // on the owner line (lat 46), not the sector (46.2)
  });
});
