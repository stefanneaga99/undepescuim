/**
 * UndePescuim.ro — pipeline-layer TypeScript types.
 *
 * Mirrors the unified data model in data/raw/data_model_proposal.md §3.4.
 * These are the shapes used by the ingestion pipeline scripts BEFORE the
 * transform to the frontend format defined in docs/ARCHITECTURE.md §3.
 */

export type WaterType = "river" | "lake" | "canal" | "stream" | "pond" | "accumulation";
export type SectorUnit = "km" | "ha";
export type AssociationType = "ajvps" | "avps" | "aps" | "ds" | "anpa" | "other";
export type PermitIssuer = "anadspa" | "romsilva" | "asociatie";
export type CanonicalSource = "anpa" | "arebaltapeste" | "locuri";
export type SourceName = "anpa" | "arebaltapeste" | "locuri";

export interface County {
  id: string;
  name: string;
  name_ascii: string;
  region?: string;
  has_contracted_waters: boolean;
  anpa_section_order?: number;
}

export interface Association {
  id: string;
  name: string;
  name_long?: string;
  name_normalized: string;
  type: AssociationType;
  home_county_id?: string;
  address?: string;
  phone?: string;
  email?: string;
  website?: string;
  permit_url?: string;
  permit_issuer?: PermitIssuer;
  slug: string;
  bbox?: [number, number, number, number];
  source_ids: string[];
  raw_data?: Record<string, unknown>;
}

export interface Water {
  id: string;
  name: string;
  name_normalized: string;
  name_alt?: string[];
  county_id: string;
  water_type: WaterType;
  sector_description?: string;
  sector_km?: number;
  sector_ha?: number;
  sector_unit?: SectorUnit;
  limits_text?: string;
  coordinates_lat?: number;
  coordinates_lon?: number;
  bbox?: [number, number, number, number];
  is_contracted: boolean;
  prohibition_flag?: boolean;
  contract_number?: string;
  contract_date?: string;
  canonical_source: CanonicalSource;
  source_ids: string[];
  raw_data?: Record<string, unknown>;
}

export interface WaterAssociation {
  water_id: string;
  association_id: string;
  contract_number?: string;
  contract_date?: string;
  is_primary: boolean;
  source: CanonicalSource;
  source_row?: number;
}

export interface SourceReference {
  id: string;
  source_name: SourceName;
  raw_file_path: string;
  raw_file_url?: string;
  source_date?: string;
  ingested_at: string;
  record_count?: number;
  schema_version: string;
}
