import { describe, expect, it } from 'vitest';
import { parseReportContext, sanitizeReportContext } from './report-context';

const input = {
  subject: { water: { slug: 'b', name: 'Bâsca' }, selection: { selectedWaterSlug: 'b', segment: null, associationSlug: null, contractRef: null } },
  map: { center: { lat: 45.12345, lon: 25.98765 }, zoom: 12, bounds: { south: 45, west: 25, north: 45.2, east: 26 } },
  filters: { counties: ['Cluj', 'Cluj'], localities: ['Test'], waterType: 'rau', contractStatus: 'contractate', selectedAssociationSlug: null },
  page: { pathname: '/' }, client: { formFactor: 'desktop' }, provenance: { appVersion: null, dataUpdatedAt: '2026-01-01', gitSha: null }, consent: { approximateMap: true, preciseLocation: false, screenshot: false },
};

describe('report context v1', () => {
  it('normalizes a valid context and rounds map values', () => {
    const result = parseReportContext(input);
    expect(result?.map?.center).toEqual({ lat: 45.123, lon: 25.988 });
    expect(result?.filters.counties).toEqual(['Cluj']);
  });
  it('rejects mismatched selection and forbidden payloads', () => {
    expect(parseReportContext({ ...input, subject: { ...input.subject, selection: { ...input.subject.selection, selectedWaterSlug: 'a' } } })).toBeNull();
    expect(sanitizeReportContext({ ...input, details: 'github_pat_test' })).toBeNull();
  });
  it('only includes rounded GPS with explicit consent', () => {
    const result = parseReportContext({ ...input, preciseLocation: { lat: 45.1234, lon: 25.9876 }, consent: { ...input.consent, preciseLocation: true } });
    expect(result?.preciseLocation).toEqual({ lat: 45.12, lon: 25.99 });
    expect(parseReportContext({ ...input, preciseLocation: { lat: 45.1234, lon: 25.9876 } })?.preciseLocation).toBeUndefined();
  });
  it('omits oversized optional fields deterministically', () => {
    const result = parseReportContext({ ...input, filters: { ...input.filters, localities: Array.from({ length: 256 }, (_, i) => `Localitate ${i} ${'x'.repeat(120)}`) } });
    expect(result).not.toBeNull();
    expect(result?.filters.localities).toEqual([]);
  });
});
