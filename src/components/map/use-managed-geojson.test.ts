import { describe, expect, it } from 'vitest';
import { createFeatureWorkQueue } from './use-managed-geojson';

type Feature = { type: 'Feature'; properties: { slug: string }; geometry: { type: 'Point'; coordinates: [number, number] } };

const feature = (slug: string, x = 0): Feature => ({
  type: 'Feature',
  properties: { slug },
  geometry: { type: 'Point', coordinates: [x, 0] },
});

describe('managed GeoJSON reconciliation queue', () => {
  it('retains unchanged features and only adds, replaces, and removes changed slugs', () => {
    const queue = createFeatureWorkQueue(
      new Map([
        ['keep', feature('keep')],
        ['replace', feature('replace', 1)],
        ['remove', feature('remove')],
      ]),
      [feature('keep'), feature('replace', 2), feature('add')],
      (item) => item.properties.slug,
    );

    expect(queue.map((item) => item.kind)).toEqual(['update', 'replace', 'remove', 'add']);
    expect(queue.map((item) => item.id)).toEqual(['keep', 'replace', 'remove', 'add']);
  });

  it('cancels work from an obsolete generation before applying the next slice', () => {
    const queue = createFeatureWorkQueue(new Map(), [feature('a'), feature('b')], (item) => item.properties.slug);
    const applied: string[] = [];

    expect(queue.flush(0, () => false, (item) => applied.push(item.id))).toBe(true);
    expect(applied).toEqual([]);
    expect(queue.flush(performance.now() + 100, () => true, (item) => applied.push(item.id))).toBe(false);
    expect(applied).toEqual(['a', 'b']);
  });
});
