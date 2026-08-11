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

/** County name as stored in water.judet (e.g. "Cluj", "Bihor") */
export type County = string;

/** A fishing association that manages waters */
export interface Association {
  slug: string;
  name: string;
  name_long: string;
  ape: number; // water count (computed from waters dataset at extract time)
  adresa?: string;
  telefon?: string;
  siteUrl?: string;
  bbox: BBox;
  id: string;
}

/** A public fishing water (lake or river section) */
export interface Water {
  slug: string;
  name: string;
  judet: County;
  type: 'ape'; // always "ape" for public waters
  subtype: WaterSubtype;
  limite: string; // sector boundary description
  dimensiune: string; // size with unit ("240 Ha" | "35 km")
  pescuit_interzis: boolean;
  referinta: string; // legal reference — MVP stand-in for "permit note"
  coordinates: LngLat;
  driving: LngLat;
  bbox: BBox;
  asociatie: {
    name: string;
    name_long?: string | null;
    slug: string;
    telefon?: string;
    adresa?: string;
    siteUrl?: string;
  } | null;
  // FUTURE: true polygon/polyline geometry (geocoding pipeline t_04163c8f)
  // geojson?: GeoJSON.Geometry;
}

/** GeoJSON feature properties for Leaflet rendering */
export interface WaterFeatureProperties {
  slug: string;
  name: string;
  subtype: WaterSubtype;
  judet: County;
  asociatieSlug: string | null;
}

export type WaterFeature = GeoJSON.Feature<GeoJSON.Geometry, WaterFeatureProperties>;

export type WaterFeatureCollection = GeoJSON.FeatureCollection<GeoJSON.Geometry, WaterFeatureProperties>;
