/**
 * UndePescuim.ro — shared domain types.
 *
 * Placeholder module. Concrete types (water bodies, fishing spots,
 * associations, verification reports) will be defined here by the
 * architecture design (parent task t_13c53320) and data pipeline work.
 */

/** Placeholder: a named geographic feature (county / water body / spot). */
export interface NamedGeoFeature {
  id: string;
  name: string;
  /** RO name; optional EN translation for the bilingual UI. */
  nameEn?: string;
}

/** Placeholder: source metadata for a static data record. */
export interface SourceRef {
  /** e.g. "ANPA 2026 contracted list" */
  source: string;
  url?: string;
  updatedAt: string; // ISO date
}
