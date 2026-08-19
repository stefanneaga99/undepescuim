/**
 * UndePescuim.ro — core map UI domain types.
 * Canonical contract from docs/component_structure_plan.md §8.
 * Mirrors the probe data in data/raw/arebaltapeste_probe/snapshot_*.json.
 */

/** WGS84 longitude, latitude pair — GeoJSON convention ([lon, lat]) */
export type LngLat = [number, number];

/** Bounding box: [minLon, minLat, maxLon, maxLat] */
export type BBox = [number, number, number, number];

/** Water type discriminator */
export type WaterSubtype = 'lac' | 'rau';

/** Water type filter state */
export type WaterTypeFilter = 'all' | WaterSubtype;

/** Contract-status filter (t_471dad64): show everything / only contracted / only uncontracted. */
export type ContractFilter = 'all' | 'contractate' | 'necontractate';

/** County name as stored in water.judet (e.g. "Cluj", "Bihor") */
export type County = string;

export type AssociationLocationType =
  | 'headquarters'
  | 'registered_office'
  | 'branch'
  | 'office'
  | 'club_contact_point'
  | 'permit_pickup_point'
  | 'partner_location';
export type AssociationLocationFreshness = 'current' | 'needs_confirmation' | 'historical';

export interface AssociationLocationContact {
  kind: 'phone' | 'email' | 'url';
  value: string;
}

export interface AssociationLocationSource {
  url: string;
  publisher: string;
  sourceType: string;
  publishedAt?: string;
  retrievedAt: string;
}

export interface AssociationLocation {
  id: string;
  associationId: string;
  associationSlug: string;
  type: AssociationLocationType;
  label?: string;
  address: string;
  locality: string;
  county: County;
  country: 'RO';
  contacts?: AssociationLocationContact[];
  sources: AssociationLocationSource[];
  status: 'verified' | 'ambiguous' | 'stale' | 'unverified';
  confidence: 'high' | 'medium' | 'low';
  freshness: AssociationLocationFreshness;
  checkedAt: string;
  notes?: string;
  public: boolean;
  review: { status: 'approved' | 'needs_review'; approvedAt?: string };
}

/**
 * A county boundary feature from /data/counties.geojson (t_6c2ac870) —
 * simplified Nominatim polygons, one per county. Used by the nearby-waters
 * sheet to attribute a water's segment (geometry/bbox) to its own county,
 * instead of the contract county (which for multi-county rivers is the
 * association's seat).
 */
export interface CountyFeature {
  type: 'Feature';
  properties: { name: County };
  geometry: GeoJSON.Polygon | GeoJSON.MultiPolygon;
}

/** Who issues the permit for a water. Derived from association type at transform time (F1a). */
export type PermitIssuer = 'anadspa' | 'romsilva' | 'asociatie';

/** Permit duration type. NOT populated from upstream yet (F1a-part2 enrichment). */
export type PermitType = 'anual' | 'zi' | 'luna' | 'sezon' | 'altele';

/** A fishing association that manages waters */
export interface Association {
  slug: string;
  name: string;
  name_long: string;
  ape: number; // water count (computed from waters dataset at extract time)
  /** County names whose contracted waters this association manages (sorted, display-ready). */
  counties?: string[];
  /** Reciprocity status. 'neconfirmată' unless a public source confirms otherwise (F2a). */
  reciprocity?: 'confirmată' | 'neconfirmată';
  /** Optional contract reference (most recent ANPA contract_number). */
  contract_ref?: string;
  adresa?: string;
  telefon?: string;
  siteUrl?: string;
  /** URL to buy the association's permit online (arebaltapeste `link_permis`). */
  permitUrl?: string;
  /** Issuing body derived from association type at transform time. */
  permitIssuer?: PermitIssuer;
  /** Permit duration type — reserved; empty until enrichment lands (F1a-part2). */
  permitType?: PermitType;
  bbox: BBox;
  id: string;
  locations?: AssociationLocation[];
}

/** A public fishing water (lake or river section) */
export interface Water {
  slug: string;
  name: string;
  judet: County;
  type: 'ape'; // always "ape" for public waters
  subtype: WaterSubtype;
  limite?: string; // sector boundary description (absent for uncontracted)
  dimensiune?: string; // size with unit ("240 Ha" | "35 km")
  pescuit_interzis?: boolean;
  referinta?: string; // legal reference — MVP stand-in for "permit note"
  coordinates: LngLat;
  driving?: LngLat;
  bbox: BBox;
  asociatie: {
    name: string;
    name_long?: string | null;
    slug: string;
    telefon?: string;
    adresa?: string;
    siteUrl?: string;
    permitUrl?: string;
    permitIssuer?: PermitIssuer;
    permitType?: PermitType;
  } | null;
  // Real polygon/polyline geometry from the geocoding pipeline (t_04163c8f).
  // When present, the map renders the true shape of the water; otherwise
  // it falls back to the bbox rectangle.
  geometry?: {
    type: 'MultiLineString' | 'LineString' | 'Polygon' | 'MultiPolygon';
    coordinates: GeoJSON.Position[][][] | GeoJSON.Position[][] | GeoJSON.Position[];
  };
  /** Geocoded position of the contract along the river course (0=source, 1=mouth). */
  course_frac?: number;
  /**
   * True when a contract is a SECTOR of the river main course even though its
   * name starts with a tributary-looking prefix ('Pârâu X', 'Valea X').
   * E.g. 'Pârâu Buzăul Mijlociu' (Covasna headwater) and
   * 'Valea Buzăului superior/inferior' are sectors of the Râul Buzău and must
   * participate in click resolution alongside the 'Râul' contracts.
   */
  mainCourse?: boolean;
  /**
   * Exact river group key (t_ac697770). When present, click resolution groups
   * contracts by THIS key instead of the fuzzy 5-char waterKey prefix — fixes
   * collisions (Siret/Sirețel, Someș/Someșul Mic, Crișul Repede/Alb/Negru)
   * and the 'oltul'/'olt' mismatch. Set on every member of a multi-contract
   * river (and on collision-prone singletons).
   */
  riverGroup?: string;
  /**
   * Exact sector boundaries [0..1] along the river course (Olt contracts).
   * When present, click resolution prefers the smallest interval containing
   * the clicked fraction over the Voronoi fallback, and the focus highlight
   * covers exactly [sectorStart, sectorEnd].
   */
  sectorStart?: number;
  sectorEnd?: number;
  /**
   * True for OSM rivers with NO contract (t_471dad64) — rendered as a thin
   * teal overlay, click opens a 'Necontractat' card instead of an association.
   */
  uncontracted?: boolean;
  /** Simplified-course length in km (uncontracted rivers; used for zoom LOD). */
  lengthKm?: number;
  /** Surface area in hectares (uncontracted lakes/ponds; used for zoom LOD). */
  areaHa?: number;
  /**
   * Per-county render geometry (t_117f0b99). Key = normalized county name
   * (lowercase, diacritics stripped, separators removed — see
   * utils/county-clip.ts `countyClipKey`). When the county filter is active
   * the layer renders THIS instead of the full `geometry`, which spans the
   * whole river course across several counties. Only the water's OWN county
   * is ever stored (the filter includes a water iff its judet is selected).
   * `null` = the geometry does not touch the county — render nothing when the
   * county is selected (misattributed geometry can't leak outside anymore).
   */
  geometryByCounty?: Record<string, GeoJSON.Geometry | null>;
  /**
   * Single primary locality (UAT/comună) for the water (t_dd918db7).
   * Derived offline (scripts/build_locality_assignment.py): county-clip /
   * sector geometry centroid → line midpoint → coordinates → bbox center →
   * `limite`-text fallback (the 271 ungeocoded ANPA/Romsilva entries).
   * Null when nothing resolved — the water stays reachable via the county
   * filter but never appears under a locality.
   */
  locality?: string | null;
}

/** GeoJSON feature properties for Leaflet rendering */
export interface WaterFeatureProperties {
  slug: string;
  name: string;
  subtype: WaterSubtype;
  judet: County;
  asociatieSlug: string | null;
  /** exact river-group key (t_ac697770) — used to match focus slices */
  riverGroup?: string | null;
  /** marker for non-renderable waters (no geometry, no bbox) */
  _hidden?: boolean;
  /** bbox-fallback water rendered as a discreet point dot (t_cdb614de) —
   * a contracted water whose contract bbox is known but OSM has no real
   * geometry for it (unmapped/unmappable). Rendered as a small distinct
   * dot instead of a blue rectangle. */
  _bboxFallback?: boolean;
  /** uncontracted OSM river (t_471dad64) */
  uncontracted?: boolean;
  /** simplified-course length in km (uncontracted rivers; zoom LOD) */
  lengthKm?: number;
  /** surface area in ha (uncontracted lakes/ponds; zoom LOD) */
  areaHa?: number;
}

export type WaterFeature = GeoJSON.Feature<GeoJSON.Geometry, WaterFeatureProperties>;

export type WaterFeatureCollection = GeoJSON.FeatureCollection<GeoJSON.Geometry, WaterFeatureProperties>;

/** Report form submission reason (F3 — crowdsourced data maintenance). */
export type ReportReason =
  | 'data_correct'          // "Datele sunt corecte (am pescuit aici)"
  | 'water_invalid'         // "Această apă nu mai există / nu se poate pescui"
  | 'association_changed'   // "Asociația s-a schimbat"
  | 'wrong_coordinates'     // "Coordonatele sunt greșite"
  | 'other';                // "Altă problemă"

/** Report form submission payload (client → POST /api/report). */
export interface VerificationReport {
  waterSlug: string;
  waterName: string;
  reason: ReportReason;
  details?: string;         // optional free-text
  contactEmail?: string;    // optional, for follow-up
  submittedAt: string;      // ISO 8601 (set server-side)
}
