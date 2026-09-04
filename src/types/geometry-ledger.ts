import type { BBox, LngLat, WaterSubtype } from '@/types/data';

export type GeometryLedgerClassification = 'repaired' | 'preview-only' | 'unresolved';
export type GeometryLedgerState =
  | 'canonical-legal-sector'
  | 'physical-full-course-preview'
  | 'explicit-physical-segment'
  | 'unresolved';

export interface GeometryLedgerSummary {
  readonly geometryHash: string;
  readonly type: 'Point' | 'LineString' | 'MultiLineString' | 'Polygon' | 'MultiPolygon';
  readonly bbox: BBox;
  readonly coordinateCount: number;
  readonly valid: true;
  readonly validityEvidence: string;
}

interface GeometryLedgerResolvedVariantBase {
  readonly evidenceSourceId: string;
  readonly segmentId: string;
  readonly geometry: GeometryLedgerSummary;
}

export interface CanonicalLegalSectorVariant extends GeometryLedgerResolvedVariantBase {
  readonly state: 'canonical-legal-sector';
  readonly start: number | null;
  readonly end: number | null;
}

export interface PhysicalFullCoursePreviewVariant extends GeometryLedgerResolvedVariantBase {
  readonly state: 'physical-full-course-preview';
  readonly start: null;
  readonly end: null;
}

export interface ExplicitPhysicalSegmentVariant extends GeometryLedgerResolvedVariantBase {
  readonly state: 'explicit-physical-segment';
  readonly start: number;
  readonly end: number;
}

export interface UnresolvedGeometryVariant {
  readonly state: 'unresolved';
  readonly start: null;
  readonly end: null;
  readonly evidenceSourceId: string;
  readonly segmentId: null;
  readonly geometry: null;
  readonly reason: string;
}

export type GeometryLedgerVariant =
  | CanonicalLegalSectorVariant
  | PhysicalFullCoursePreviewVariant
  | ExplicitPhysicalSegmentVariant
  | UnresolvedGeometryVariant;

export interface GeometryLedgerRecord {
  readonly sourceSlug: string;
  readonly name: string;
  readonly county: string;
  readonly subtype: WaterSubtype;
  readonly aliases: readonly string[];
  readonly riverGroup: string | null;
  readonly classification: GeometryLedgerClassification;
  readonly geometryVariants: readonly GeometryLedgerVariant[];
}

export interface GeometryLedger {
  readonly artifact: 'public-geometry-ledger';
  readonly schemaVersion: 1;
  readonly lockedCommit: string;
  readonly records: readonly GeometryLedgerRecord[];
}

/** Runtime-only selection intent. It is never persisted as legal geometry. */
export type RuntimeSelectedFocus =
  | { readonly kind: 'none' }
  | { readonly kind: 'whole-feature-focus' }
  | {
      readonly kind: 'verified-sector-focus';
      readonly interval: readonly [number, number];
      readonly segmentId?: string;
      readonly geometryHash?: string;
    }
  | {
      readonly kind: 'feature-selected-unverified-sector';
      readonly referencePoint: LngLat | null;
      readonly accessibleLabel: string;
    };
