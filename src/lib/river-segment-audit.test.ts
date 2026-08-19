import parityFixture from '../../tests/fixtures/river_segment_parity.json';
import { describe, expect, it } from 'vitest';
import { connectedComponents, coverage, topology } from './river-segment-audit';

type Way = { osm_id: number; coordinates: [number, number][] };
const sectors: Way[] = parityFixture.multi_sector_ways as Way[];

const parityShape = (ways: Way[]) => {
  const report = topology(ways);
  return { components: report.components, ways: report.ways, branch_count: report.branch_nodes.length };
};

describe('offline river segment parity probes', () => {
  it('keeps deterministic multi-sector topology, duplicate-safe ordering and components', () => {
    expect(parityShape(sectors)).toEqual({ components: 2, ways: [101, 102, 103, 201], branch_count: 1 });
    expect(connectedComponents(sectors)).toEqual([[101, 102, 103], [201]]);
  });

  it.each([
    ['county overlay', [[25, 46], [25.01, 46]] as [number, number][], [[25, 46], [25.01, 46]] as [number, number][], true],
    ['missing contract', [[25, 46], [25.01, 46]] as [number, number][], [[27, 47], [27.01, 47]] as [number, number][], false],
    ['Târnava injected gap', [[24, 46], [24.01, 46]] as [number, number][], [[24, 46], [24.005, 46.004], [24.01, 46]] as [number, number][], false],
    ['truncated segment', [[24, 46], [24.02, 46]] as [number, number][], [[24, 46], [24.01, 46]] as [number, number][], false],
  ])('%s has stable bidirectional coverage', (_name, published, osm, fullyCovered) => {
    const result = coverage(published, osm, 1);
    expect(result.published_to_osm === 1).toBe(fullyCovered);
    if (_name !== 'truncated segment') expect(result.osm_to_published === 1).toBe(fullyCovered);
  });

  it('does not mutate fixture coordinates', () => {
    const before = JSON.stringify(sectors);
    coverage(sectors[0].coordinates, sectors[2].coordinates, 1);
    expect(JSON.stringify(sectors)).toBe(before);
  });

  it('keeps negative findings explicit for a multi-sector fixture', () => {
    const cases = (parityFixture as unknown as { cases: Array<{ id: string; status: string; finding_codes: string[] }> }).cases;
    expect(cases.find((item) => item.id === 'pass')).toMatchObject({ status: 'PASS_CONTRACTED', finding_codes: [] });
    for (const id of ['missing-segment', 'truncation', 'sector-mismatch', 'duplicate', 'tarnava-gap']) {
      const item = cases.find((candidate) => candidate.id === id);
      expect(item?.status, `${id} must remain blocking`).toBe('BLOCKED');
      expect(item?.finding_codes.length, `${id} must retain a finding`).toBeGreaterThan(0);
    }
  });
});
