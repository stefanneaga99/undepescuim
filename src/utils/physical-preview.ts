import type { Water } from '@/types/data';

interface PhysicalPreviewArtifact {
  schemaVersion?: number;
  records?: Array<Record<string, unknown>>;
}

function geometryBbox(geometry: NonNullable<Water['geometry']>): Water['bbox'] {
  const points: [number, number][] = [];
  const visit = (value: unknown): void => {
    if (!Array.isArray(value)) return;
    if (value.length >= 2 && typeof value[0] === 'number' && typeof value[1] === 'number') {
      points.push([value[0], value[1]]);
      return;
    }
    value.forEach(visit);
  };
  visit(geometry.coordinates);
  if (points.length === 0) return [25, 46, 25, 46];
  return [
    Math.min(...points.map(([lon]) => lon)),
    Math.min(...points.map(([, lat]) => lat)),
    Math.max(...points.map(([lon]) => lon)),
    Math.max(...points.map(([, lat]) => lat)),
  ];
}

/** Convert the isolated artifact to map waters without mutating canonical data. */
export function physicalPreviewWaters(artifact: PhysicalPreviewArtifact): Water[] {
  if (artifact.schemaVersion !== 1 || !Array.isArray(artifact.records)) return [];
  return artifact.records.flatMap((record) => {
    const candidates = Array.isArray(record.physicalCandidates) ? record.physicalCandidates : [];
    const candidate = candidates[0];
    if (!candidate || typeof candidate !== 'object') return [];
    const c = candidate as { geometry?: Water['geometry']; geometryHash?: string };
    if (!c.geometry?.coordinates?.length) return [];
    const bbox = geometryBbox(c.geometry);
    return [{
      slug: String(record.slug),
      name: String(record.name),
      judet: String(record.county),
      type: 'ape',
      subtype: record.subtype === 'lac' ? 'lac' : 'rau',
      coordinates: [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2] as [number, number],
      bbox,
      asociatie: null,
      geometry: c.geometry,
      riverGroup: typeof record.riverGroup === 'string' ? record.riverGroup : undefined,
      physicalPreview: true,
      legalStatus: 'legal sector unverified',
      physicalProvenance: {
        sourceBranch: String(record.sourceBranch),
        sourceCommit: String(record.sourceCommit),
        geometryHash: c.geometryHash,
      },
    } satisfies Water];
  });
}

/** Keep one rendered line per shared physical candidate while retaining provenance. */
export function dedupePhysicalPreview(waters: Water[]): Water[] {
  const seen = new Set<string>();
  return waters.filter((water) => {
    const hash = water.physicalProvenance?.geometryHash;
    const key = hash ? `${water.riverGroup ?? 'ungrouped'}:${hash}` : water.slug;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

/** A physical preview is never a legal-sector claim. */
export function isUnverifiedPhysicalPreview(water: Water): boolean {
  return water.physicalPreview === true && water.legalStatus === 'legal sector unverified';
}
