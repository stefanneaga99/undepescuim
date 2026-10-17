import { afterEach, describe, expect, it, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import type { Water } from '@/types/data';

const load = vi.fn();
vi.mock('@/lib/sector-evidence', async (orig) => ({
  ...(await orig<typeof import('@/lib/sector-evidence')>()),
  loadSectorEvidence: () => load(),
}));

import { useSectorEvidence } from '@/hooks/use-sector-evidence';

const ENTRY = {
  from: { kind: 'SOURCE', label: 'izvoare', anchor: null, confidence: 0.9 },
  to: { kind: 'MOUTH', label: 'vărsare', anchor: null, confidence: 0.95 },
  lengthKm: 10, contractKm: 10, status: 'resolved', confidence: 'high',
};
const EVIDENCE = { schema: 1, networkVersion: 'v', osmTimestamp: '2026-10-16T20:21:21Z', sectors: { pre: ENTRY } };

function water(over: Partial<Water>): Water {
  return {
    slug: 'pre', name: 'Râul Test', judet: 'Alba', type: 'ape', subtype: 'rau', coordinates: [25, 46],
    bbox: [24, 45, 26, 47], asociatie: null,
    geometry: { type: 'LineString', coordinates: [[25, 46], [25.1, 46]] }, geometryKind: 'sector', sectorStatus: 'resolved',
    ...over,
  } as Water;
}

afterEach(() => load.mockReset());

describe('useSectorEvidence', () => {
  it('returns the entry of a pre-cut sector with the OSM date', async () => {
    load.mockResolvedValue(EVIDENCE);
    const { result } = renderHook(() => useSectorEvidence(water({})));
    await waitFor(() => expect(result.current).not.toBeNull());
    expect(result.current).toEqual({ entry: ENTRY, osmDate: '2026-10-16' });
  });

  it('never fetches for a legacy water and is null for a sector missing from the file', async () => {
    load.mockResolvedValue(EVIDENCE);
    const legacy = renderHook(() => useSectorEvidence(water({ geometryKind: undefined })));
    expect(legacy.result.current).toBeNull();
    expect(load).not.toHaveBeenCalled();
    const missing = renderHook(() => useSectorEvidence(water({ slug: 'other' })));
    await waitFor(() => expect(load).toHaveBeenCalled());
    expect(missing.result.current).toBeNull();
    expect(renderHook(() => useSectorEvidence(null)).result.current).toBeNull();
  });

  it('does not show a stale entry after switching water', async () => {
    load.mockResolvedValue(EVIDENCE);
    const { result, rerender } = renderHook(({ w }) => useSectorEvidence(w), { initialProps: { w: water({}) } });
    await waitFor(() => expect(result.current).not.toBeNull());
    rerender({ w: water({ slug: 'other' }) });
    expect(result.current).toBeNull();
  });
});
