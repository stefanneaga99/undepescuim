// @vitest-environment node
import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  SECTOR_EVIDENCE_URL,
  loadSectorEvidence,
  osmDate,
  parseSectorEvidence,
  resetSectorEvidenceCache,
} from '@/lib/sector-evidence';

const ENTRY = {
  from: { kind: 'SOURCE', label: 'izvoare', anchor: null, confidence: 0.9 },
  to: { kind: 'CONFLUENCE', label: 'confluența cu Mureș', anchor: { type: 'course', id: 'rel:9' }, confidence: 0.95 },
  lengthKm: 11.4,
  contractKm: 12,
  status: 'resolved',
  confidence: 'high',
};
const FILE = { schema: 1, network_version: 'ro-water-20261016', osm_timestamp: '2026-10-16T20:21:21Z', sectors: { a: ENTRY } };

function response(status: number, body: unknown): Response {
  return { status, ok: status >= 200 && status < 300, json: async () => body } as Response;
}

afterEach(() => resetSectorEvidenceCache());

describe('parseSectorEvidence', () => {
  it('maps the file to the typed shape', () => {
    const ev = parseSectorEvidence(FILE);
    expect(ev.networkVersion).toBe('ro-water-20261016');
    expect(ev.sectors.a.to).toEqual({ kind: 'CONFLUENCE', label: 'confluența cu Mureș', anchor: { type: 'course', id: 'rel:9' }, confidence: 0.95 });
    expect(ev.sectors.a.from.anchor).toBeNull();
    expect(osmDate(ev)).toBe('2026-10-16');
  });

  it('rejects a wrong envelope and drops malformed entries only', () => {
    expect(() => parseSectorEvidence(null)).toThrow();
    expect(() => parseSectorEvidence({ schema: 2, sectors: {} })).toThrow();
    expect(() => parseSectorEvidence({ schema: 1, sectors: [] })).toThrow();
    const ev = parseSectorEvidence({
      schema: 1,
      sectors: {
        a: ENTRY,
        noLabel: { ...ENTRY, from: { kind: 'SOURCE', label: '' } },
        badStatus: { ...ENTRY, status: 'unresolved' },
        badConfidence: { ...ENTRY, confidence: 'certain' },
        notObject: 3,
        oddAnchor: { ...ENTRY, to: { ...ENTRY.to, anchor: { type: 'node', id: { x: 1 } } }, lengthKm: 'x', contractKm: null },
      },
    });
    expect(Object.keys(ev.sectors).sort()).toEqual(['a', 'oddAnchor']);
    expect(ev.sectors.oddAnchor.to.anchor).toEqual({ type: 'node', id: null });
    expect(ev.sectors.oddAnchor.lengthKm).toBeNull();
    expect(ev.networkVersion).toBe('');
    expect(osmDate(ev)).toBeNull();
    expect(osmDate(null)).toBeNull();
  });
});

describe('loadSectorEvidence', () => {
  it('fetches once and memoises', async () => {
    const fetcher = vi.fn(async () => response(200, FILE));
    const [a, b] = await Promise.all([loadSectorEvidence(fetcher as unknown as typeof fetch), loadSectorEvidence(fetcher as unknown as typeof fetch)]);
    expect(a?.sectors.a.status).toBe('resolved');
    expect(b).toBe(a);
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(fetcher).toHaveBeenCalledWith(SECTOR_EVIDENCE_URL);
  });

  it('a missing file (before cutover) is null and is not refetched', async () => {
    const fetcher = vi.fn(async () => response(404, null));
    expect(await loadSectorEvidence(fetcher as unknown as typeof fetch)).toBeNull();
    expect(await loadSectorEvidence(fetcher as unknown as typeof fetch)).toBeNull();
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it('a transient failure is null and retried on the next call', async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce(response(500, null))
      .mockRejectedValueOnce(new Error('offline'))
      .mockResolvedValueOnce(response(200, { schema: 9 }))
      .mockResolvedValueOnce(response(200, FILE));
    const f = fetcher as unknown as typeof fetch;
    expect(await loadSectorEvidence(f)).toBeNull();
    expect(await loadSectorEvidence(f)).toBeNull();
    expect(await loadSectorEvidence(f)).toBeNull();
    expect((await loadSectorEvidence(f))?.sectors.a).toBeTruthy();
    expect(fetcher).toHaveBeenCalledTimes(4);
  });
});
