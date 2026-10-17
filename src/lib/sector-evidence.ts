/**
 * Lazy loader for `public/data/sector-evidence.json` (river geometry v2,
 * docs/plans/river-geometry-v2.md T4.3): how each pre-cut sector's two
 * endpoints were resolved from the contract `limite`.
 *
 * The file is fetched once, on first use (a water card for a pre-cut
 * sector), and the parsed result is memoised for the session — the same
 * fetch-once pattern map-store uses for the county clips. A missing file
 * (404, before the cutover) resolves to `null`; a network or parse failure
 * also resolves to `null` but clears the memo so a later card retries.
 */

export type SectorEndpointKind =
  | 'SOURCE' | 'MOUTH' | 'CONFLUENCE' | 'DAM' | 'LAKE_UPSTREAM' | 'LAKE_DOWNSTREAM' | 'BRIDGE'
  | 'ROAD' | 'LOCALITY' | 'COUNTY_LIMIT' | 'COUNTY' | 'BORDER' | 'WATERFALL';

export interface SectorEndpointEvidence {
  readonly kind: SectorEndpointKind | string;
  /** Short Romanian description, e.g. "confluența cu Mureș". */
  readonly label: string;
  readonly anchor: { readonly type: string; readonly id: string | number | null } | null;
  readonly confidence: number | null;
}

export interface SectorEvidenceEntry {
  readonly from: SectorEndpointEvidence;
  readonly to: SectorEndpointEvidence;
  readonly lengthKm: number | null;
  readonly contractKm: number | null;
  readonly status: 'resolved' | 'review';
  readonly confidence: 'high' | 'medium' | 'low';
}

export interface SectorEvidence {
  readonly schema: 1;
  readonly networkVersion: string;
  /** ISO timestamp of the OSM data the sectors were cut from. */
  readonly osmTimestamp: string | null;
  readonly sectors: Readonly<Record<string, SectorEvidenceEntry>>;
}

export const SECTOR_EVIDENCE_URL = '/data/sector-evidence.json';

const STATUSES = new Set(['resolved', 'review']);
const CONFIDENCES = new Set(['high', 'medium', 'low']);

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function numberOrNull(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function endpoint(value: unknown): SectorEndpointEvidence | null {
  if (!isObject(value) || typeof value.kind !== 'string' || typeof value.label !== 'string' || !value.label) return null;
  const a = value.anchor;
  const anchor = isObject(a) && typeof a.type === 'string'
    ? { type: a.type, id: typeof a.id === 'string' || typeof a.id === 'number' ? a.id : null }
    : null;
  return { kind: value.kind, label: value.label, anchor, confidence: numberOrNull(value.confidence) };
}

/**
 * Validate the raw file. Throws on a wrong envelope; drops (does not throw
 * on) individual malformed sector entries so one bad record cannot hide the
 * rest.
 */
export function parseSectorEvidence(raw: unknown): SectorEvidence {
  if (!isObject(raw) || raw.schema !== 1 || !isObject(raw.sectors)) {
    throw new Error('sector-evidence: unsupported envelope');
  }
  const sectors: Record<string, SectorEvidenceEntry> = {};
  for (const [slug, value] of Object.entries(raw.sectors)) {
    if (!isObject(value)) continue;
    const from = endpoint(value.from);
    const to = endpoint(value.to);
    if (!from || !to || !STATUSES.has(value.status as string) || !CONFIDENCES.has(value.confidence as string)) continue;
    sectors[slug] = {
      from,
      to,
      lengthKm: numberOrNull(value.lengthKm),
      contractKm: numberOrNull(value.contractKm),
      status: value.status as SectorEvidenceEntry['status'],
      confidence: value.confidence as SectorEvidenceEntry['confidence'],
    };
  }
  return {
    schema: 1,
    networkVersion: typeof raw.network_version === 'string' ? raw.network_version : '',
    osmTimestamp: typeof raw.osm_timestamp === 'string' ? raw.osm_timestamp : null,
    sectors,
  };
}

/** `YYYY-MM-DD` of the OSM snapshot, or null. */
export function osmDate(evidence: SectorEvidence | null): string | null {
  const ts = evidence?.osmTimestamp;
  return ts && /^\d{4}-\d{2}-\d{2}/.test(ts) ? ts.slice(0, 10) : null;
}

let memo: Promise<SectorEvidence | null> | null = null;

/** Fetch + parse once per session; see the module comment for failure handling. */
export function loadSectorEvidence(fetcher: typeof fetch = fetch): Promise<SectorEvidence | null> {
  if (!memo) {
    memo = (async () => {
      const response = await fetcher(SECTOR_EVIDENCE_URL);
      if (response.status === 404) return null;
      if (!response.ok) throw new Error(`sector-evidence: HTTP ${response.status}`);
      return parseSectorEvidence(await response.json());
    })().catch(() => {
      memo = null; // transient failure: let the next card retry
      return null;
    });
  }
  return memo;
}

/** Test hook: forget the memoised file. */
export function resetSectorEvidenceCache(): void {
  memo = null;
}
