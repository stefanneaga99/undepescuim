import type { BBox, WaterSubtype } from '@/types/data';

export const CLASS2_LEGAL_STATUS = 'legal sector unverified';

export interface Class2PhysicalCandidate {
  id: string;
  kind: string | null;
  rating: string | null;
  source: string | null;
  sourceId: string | null;
  physicalSourceUrl: string | null;
  osmId: string | number | null;
  geofabrikId: string | number | null;
  geometryHash: string;
  geometry: GeoJSON.Geometry;
  measuredLengthKm: number | null;
  componentCount: number | null;
  componentIds: (string | number)[];
  confidence: string;
  countyMatch: { status?: string; rationale?: string } | null;
  topology: unknown;
}

export interface Class2PreviewRecord {
  slug: string;
  name: string;
  county: string;
  locality: string | null;
  association: string | null;
  associationSlug: string | null;
  riverGroup: string | null;
  subtype: WaterSubtype | null;
  physicalCandidates: Class2PhysicalCandidate[];
  legalStatus: typeof CLASS2_LEGAL_STATUS;
  disclosure: string;
  canonicalMutation: false;
}

export interface Class2PreviewArtifact {
  schemaVersion: number;
  artifact: 'class2-physical-preview';
  class: 2;
  chunkId: string | null;
  slugs: string[] | null;
  recordCount: number;
  candidateCount: number;
  sourceInventorySha256: string;
  records: Class2PreviewRecord[];
}

export function previewFeatures(artifact: Class2PreviewArtifact): GeoJSON.Feature[] {
  return artifact.records.flatMap((record) =>
    record.physicalCandidates.map((candidate) => ({
      type: 'Feature' as const,
      geometry: candidate.geometry,
      properties: {
        slug: record.slug,
        name: record.name,
        county: record.county,
        association: record.association,
        candidateId: candidate.id,
        geometryHash: candidate.geometryHash,
        confidence: candidate.confidence,
        legalStatus: record.legalStatus,
      },
    })),
  );
}

export function previewBounds(artifact: Class2PreviewArtifact): BBox {
  const points: [number, number][] = [];
  const visit = (value: unknown): void => {
    if (!Array.isArray(value)) return;
    if (value.length >= 2 && typeof value[0] === 'number' && typeof value[1] === 'number') {
      points.push([value[0], value[1]]);
      return;
    }
    value.forEach(visit);
  };
  artifact.records.forEach((record) => record.physicalCandidates.forEach((candidate) => {
    if ('coordinates' in candidate.geometry) visit(candidate.geometry.coordinates);
  }));
  if (points.length === 0) return [20, 43.5, 30, 48.5];
  return points.reduce<BBox>(
    (bounds, [lon, lat]) => [Math.min(bounds[0], lon), Math.min(bounds[1], lat), Math.max(bounds[2], lon), Math.max(bounds[3], lat)],
    [180, 90, -180, -90],
  );
}
