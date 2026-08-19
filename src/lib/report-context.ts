import type { ReportContextInput, ReportContextV1 } from '@/types/report-context';
import { REPORT_CONTEXT_MAX_BYTES } from '@/types/report-context';

const forbidden = /(ghp_[A-Za-z0-9_\-]+|github_pat_[A-Za-z0-9_\-]+|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]+PRIVATE KEY-----|(?:token|secret|password|apiKey|authorization|cookie|session|csrf)\s*[:=])/i;
const safeText = (value: unknown, max: number) => typeof value === 'string' ? value.normalize('NFC').replace(/[\u0000-\u001f\u007f]/g, '').slice(0, max) : '';
const finite = (value: unknown) => typeof value === 'number' && Number.isFinite(value) ? value : null;
const round = (value: unknown, digits: number) => { const n = finite(value); return n === null ? null : Number(n.toFixed(digits)); };
const list = (value: unknown, maxItems: number, maxLen: number) => Array.isArray(value) ? [...new Set(value.filter((v): v is string => typeof v === 'string').map(v => safeText(v, maxLen)).filter(Boolean))].sort().slice(0, maxItems) : [];
const jsonBytes = (value: unknown) => new TextEncoder().encode(JSON.stringify(value)).length;

function normalize(input: ReportContextInput): ReportContextV1 | null {
  if (input.schemaVersion !== undefined && input.schemaVersion !== 1) return null;
  if (input.captureVersion !== undefined && input.captureVersion !== 'map-report-context-v1') return null;
  const subject = input.subject;
  if (!subject || typeof subject !== 'object' || !subject.water || !subject.selection || typeof subject.water !== 'object' || typeof subject.selection !== 'object') return null;
  if (!subject || subject.water?.slug !== subject.selection?.selectedWaterSlug) return null;
  const center = input.map?.center;
  const bounds = input.map?.bounds;
  const map = input.map === null ? null : {
    center: center ? { lat: round(center.lat, 3)!, lon: round(center.lon, 3)! } : null,
    zoom: round(input.map?.zoom, 0) === null ? null : Math.max(0, Math.min(22, Math.round(input.map!.zoom as number))),
    bounds: bounds ? { south: round(bounds.south, 3)!, west: round(bounds.west, 3)!, north: round(bounds.north, 3)!, east: round(bounds.east, 3)! } : null,
  };
  if (map?.bounds && (map.bounds.south > map.bounds.north || map.bounds.west > map.bounds.east)) map.bounds = null;
  const precise = input.consent?.preciseLocation && input.preciseLocation ? { lat: round(input.preciseLocation.lat, 2)!, lon: round(input.preciseLocation.lon, 2)! } : undefined;
  const context: ReportContextV1 = {
    schemaVersion: 1, captureVersion: 'map-report-context-v1',
    subject: { water: { slug: safeText(subject.water.slug, 128), name: safeText(subject.water.name, 256) }, selection: {
      selectedWaterSlug: safeText(subject.selection.selectedWaterSlug, 128),
      segment: subject.selection.segment ? { kind: subject.selection.segment.kind === 'river-interval' ? 'river-interval' : 'whole-water', riverGroup: subject.selection.segment.riverGroup ? safeText(subject.selection.segment.riverGroup, 128) : null, startFraction: round(subject.selection.segment.startFraction, 6), endFraction: round(subject.selection.segment.endFraction, 6) } : null,
      associationSlug: subject.selection.associationSlug ? safeText(subject.selection.associationSlug, 128) : null, contractRef: subject.selection.contractRef ? safeText(subject.selection.contractRef, 128) : null,
    } },
    map, filters: { counties: list(input.filters?.counties, 42, 80), localities: list(input.filters?.localities, 256, 120), waterType: ['all','lac','rau'].includes(input.filters?.waterType) ? input.filters.waterType : 'all', contractStatus: ['all','contractate','necontractate'].includes(input.filters?.contractStatus) ? input.filters.contractStatus : 'all', selectedAssociationSlug: input.filters?.selectedAssociationSlug ? safeText(input.filters.selectedAssociationSlug, 128) : null },
    page: { pathname: ['/', '/permis', '/specii'].includes(input.page?.pathname) ? input.page.pathname as '/' | '/permis' | '/specii' : '/' },
    client: { formFactor: ['mobile','tablet','desktop'].includes(input.client?.formFactor) ? input.client.formFactor : 'unknown' },
    provenance: { appVersion: input.provenance?.appVersion ? safeText(input.provenance.appVersion, 64) : null, dataUpdatedAt: input.provenance?.dataUpdatedAt ? safeText(input.provenance.dataUpdatedAt, 64) : null, gitSha: input.provenance?.gitSha && /^[0-9a-f]{7,64}$/i.test(input.provenance.gitSha) ? input.provenance.gitSha : null },
    consent: { approximateMap: true, preciseLocation: !!input.consent?.preciseLocation, screenshot: false },
    ...(precise ? { preciseLocation: precise } : {}),
  };
  return context;
}

export function sanitizeReportContext(input: unknown): ReportContextV1 | null {
  if (!input || typeof input !== 'object' || Array.isArray(input)) return null;
  const raw = input as ReportContextInput;
  const allowed = new Set(['schemaVersion', 'captureVersion', 'subject', 'map', 'filters', 'page', 'client', 'provenance', 'consent', 'preciseLocation']);
  if (Object.keys(raw as object).some(key => !allowed.has(key))) return null;
  if (JSON.stringify(raw).match(forbidden)) return null;
  let context = normalize(raw);
  if (!context) return null;
  const shrinkers: Array<(c: ReportContextV1) => ReportContextV1> = [
    c => ({ ...c, subject: { ...c.subject, selection: { ...c.subject.selection, contractRef: null } } }),
    c => ({ ...c, filters: { ...c.filters, localities: [] } }),
    c => ({ ...c, map: c.map ? { ...c.map, bounds: null } : null }),
  ];
  for (const shrink of shrinkers) {
    if (jsonBytes(context) <= REPORT_CONTEXT_MAX_BYTES) break;
    context = shrink(context);
  }
  return jsonBytes(context) <= REPORT_CONTEXT_MAX_BYTES ? context : null;
}

export function parseReportContext(input: unknown): ReportContextV1 | null { return sanitizeReportContext(input); }
export function canonicalReportContext(context: ReportContextV1): string { return JSON.stringify(context); }
