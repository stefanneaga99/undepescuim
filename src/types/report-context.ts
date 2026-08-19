export type ReportFormFactor = 'mobile' | 'tablet' | 'desktop' | 'unknown';
export type ReportContextV1 = {
  schemaVersion: 1;
  captureVersion: 'map-report-context-v1';
  subject: { water: { slug: string; name: string }; selection: { selectedWaterSlug: string; segment: { kind: 'whole-water' | 'river-interval'; riverGroup: string | null; startFraction: number | null; endFraction: number | null } | null; associationSlug: string | null; contractRef: string | null } };
  map: { center: { lat: number; lon: number } | null; zoom: number | null; bounds: { south: number; west: number; north: number; east: number } | null } | null;
  filters: { counties: string[]; localities: string[]; waterType: 'all' | 'lac' | 'rau'; contractStatus: 'all' | 'contractate' | 'necontractate'; selectedAssociationSlug: string | null };
  page: { pathname: '/' | '/permis' | '/specii' };
  client: { formFactor: ReportFormFactor };
  provenance: { appVersion: string | null; dataUpdatedAt: string | null; gitSha: string | null };
  consent: { approximateMap: true; preciseLocation: boolean; screenshot: boolean };
  preciseLocation?: { lat: number; lon: number };
};

export type ReportContextInput = Omit<ReportContextV1, 'schemaVersion' | 'captureVersion'> & { schemaVersion?: unknown; captureVersion?: unknown };
export const REPORT_CONTEXT_MAX_BYTES = 1500;
