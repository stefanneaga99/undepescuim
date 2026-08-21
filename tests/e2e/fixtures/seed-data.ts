/**
 * Deterministic seed dataset for the logic/UI e2e tier (docs/e2e-test-plan.md §6.1).
 *
 * Every spec in `specs/smoke`, `specs/flows`, `specs/regression` runs against
 * THIS data (intercepted in `routes.ts`), never against the 38 MB live
 * `waters.json` — fast, deterministic, refresh-proof. The shape is typed
 * against `src/types/data.ts` so seed drift is caught at compile time.
 *
 * The seed deliberately contains one instance of every edge case the suite
 * needs (plan §6.1):
 *  - contracted river (LineString) with association permitUrl
 *  - contracted lake (Polygon) whose association has NO permitUrl → "Permis:
 *    verifică cu asociația" row
 *  - uncontracted river + uncontracted lake (teal overlay, Necontractat card)
 *  - a water with `locality: null` (locality-filter edge: hidden by any
 *    locality filter)
 *  - a deliberately long name (card truncation edge)
 *  - associations with reciprocity 'confirmată' and 'neconfirmată'
 *  - two fixed position clusters (Bucharest → default 25 km / ≥3 nearby;
 *    Iași → adaptive 50 km / <3 nearby)
 *  - a multi-county river with `geometryByCounty` clips (county-clip render path)
 */
import type {
  Association,
  AssociationLocation,
  Water,
} from '../../../src/types/data';

export interface SeedData {
  associations: Association[];
  /** contracted pool — served as public/data/waters.json */
  waters: Water[];
  /** uncontracted rivers — served as public/data/uncontracted_rivers.json */
  rivers: Water[];
  /** uncontracted lakes — served as public/data/uncontracted_lakes.json */
  lakes: Water[];
  /** county polygons — served as public/data/counties.geojson */
  counties: GeoJSON.FeatureCollection<GeoJSON.Polygon, { name: string }>;
}

const alpha: Association = {
  slug: 'asociatia-alpha',
  name: 'Asociația Alpha',
  name_long: 'Asociația Județeană a Vânătorilor și Pescarilor Sportivi Alpha',
  ape: 3,
  counties: ['Brașov', 'Cluj'],
  reciprocity: 'confirmată',
  contract_ref: 'ANPA 123/2025',
  adresa: 'Str. Testului 1, Cluj-Napoca',
  telefon: '0264 123 456',
  siteUrl: 'https://alpha.example.ro',
  permitUrl: 'https://permis.alpha.example.ro',
  permitIssuer: 'asociatie',
  bbox: [22.5, 45.4, 26.3, 47.6],
  id: 'asociatia-alpha',
};

const alphaLocations: AssociationLocation[] = [{
  id: 'alpha-office-test',
  associationId: alpha.id,
  associationSlug: alpha.slug,
  type: 'office',
  label: 'Sediu test',
  address: 'Str. Locației 1',
  locality: 'Cluj-Napoca',
  county: 'Cluj',
  country: 'RO',
  contacts: [
    { kind: 'phone', value: '0264 111 222' },
    { kind: 'email', value: 'contact@alpha.example.ro' },
    { kind: 'url', value: 'https://office.alpha.example.ro' },
    { kind: 'url', value: 'javascript:alert(1)' },
  ],
  sources: [{
    url: 'https://source.alpha.example.ro/locations',
    publisher: 'Alpha',
    sourceType: 'official',
    retrievedAt: '2026-08-19',
  }],
  status: 'verified',
  confidence: 'high',
  freshness: 'current',
  checkedAt: '2026-08-19',
  public: true,
  review: { status: 'approved' },
}];
alpha.locations = alphaLocations;

const beta: Association = {
  slug: 'asociatia-beta',
  name: 'Asociația Beta',
  name_long: 'Asociația Beta de Pescuit Sportiv',
  ape: 6,
  counties: ['Iași', 'Ilfov'],
  reciprocity: 'neconfirmată',
  contract_ref: 'ANPA 456/2025',
  adresa: 'Str. Testului 2, București',
  telefon: '021 987 654',
  siteUrl: 'https://beta.example.ro',
  // no permitUrl → the card shows "Permis: verifică cu asociația"
  bbox: [26.0, 44.3, 27.8, 47.3],
  id: 'asociatia-beta',
};

const alphaEmbedded = {
  name: alpha.name,
  name_long: alpha.name_long,
  slug: alpha.slug,
  telefon: alpha.telefon,
  adresa: alpha.adresa,
  siteUrl: alpha.siteUrl,
  permitUrl: alpha.permitUrl,
  permitIssuer: alpha.permitIssuer,
};

const betaEmbedded = {
  name: beta.name,
  name_long: beta.name_long,
  slug: beta.slug,
  telefon: beta.telefon,
  adresa: beta.adresa,
  siteUrl: beta.siteUrl,
  permitIssuer: 'asociatie' as const,
};

/** Contracted river — full metadata, association permitUrl, county clips. */
const raulSomesulTest: Water = {
  slug: 'raul-somesul-test',
  name: 'Râul Someșul Test',
  judet: 'Cluj',
  type: 'ape',
  subtype: 'rau',
  limite: 'De la podul din comuna Test până la confluența cu râul Testăuț',
  dimensiune: '35 km',
  referinta: 'Contract ANPA nr. 123/2025',
  coordinates: [23.7, 47.0],
  bbox: [23.4, 46.9, 24.0, 47.1],
  asociatie: alphaEmbedded,
  geometry: {
    type: 'LineString',
    coordinates: [
      [23.4, 46.9],
      [23.55, 46.95],
      [23.7, 47.0],
      [23.85, 47.05],
      [24.0, 47.1],
    ],
  },
  course_frac: 0.5,
  riverGroup: 'somesul-test',
  // multi-county river: the county filter renders ONLY the county's clip
  geometryByCounty: {
    cluj: {
      type: 'LineString',
      coordinates: [
        [23.4, 46.9],
        [23.55, 46.95],
        [23.7, 47.0],
      ],
    },
    maramures: {
      type: 'LineString',
      coordinates: [
        [23.7, 47.0],
        [23.85, 47.05],
        [24.0, 47.1],
      ],
    },
  },
  locality: 'Comuna Test',
};

/** Multi-contract course: only the owner has geometry; sectors are resolved
 * from shared course fractions and rendered by the focus slice layer. */
export const MULTI_CONTRACT_SELECTED_SLUG = 'sector-test-downstream';
export const UNVERIFIED_FOCUS_SELECTED_SLUG = 'tarnava-like-unverified';
const multiContractOwner: Water = {
  ...raulSomesulTest,
  slug: 'raul-multi-contract-test',
  name: 'Râul Multi Contract Test',
  riverGroup: 'multi-contract-test',
  course_frac: 0.1,
};
const multiContractMiddle: Water = {
  ...raulSomesulTest,
  slug: 'sector-test-middle',
  name: 'Sector Test Mijlociu',
  riverGroup: 'multi-contract-test',
  course_frac: 0.5,
  sectorStart: 0.25,
  sectorEnd: 0.75,
  geometry: undefined,
};
const multiContractSelected: Water = {
  ...raulSomesulTest,
  slug: MULTI_CONTRACT_SELECTED_SLUG,
  name: 'Sector Test Aval',
  riverGroup: 'multi-contract-test',
  course_frac: 0.9,
  sectorStart: 0.75,
  sectorEnd: 1,
  asociatie: alphaEmbedded,
  geometry: undefined,
};

export const REPORT_MULTI_CONTRACT_WATERS: Water[] = [
  multiContractOwner,
  multiContractMiddle,
  multiContractSelected,
];

export const UNVERIFIED_FOCUS_WATERS: Water[] = [
  {
    ...raulSomesulTest,
    slug: 'tarnava-like-owner',
    name: 'Râul Târnava Mare test',
    riverGroup: 'tarnava-like-test',
    course_frac: 0.1,
    geometry: { type: 'LineString', coordinates: [[23.4, 46.9], [23.7, 47.0], [24.0, 47.1]] },
  },
  {
    ...raulSomesulTest,
    slug: UNVERIFIED_FOCUS_SELECTED_SLUG,
    name: 'Râul Târnava Mare mijlocie test',
    riverGroup: 'tarnava-like-test',
    course_frac: 0.5,
    dimensiune: '5 Km',
    limite: 'Aval baraj lac test – pod test',
    geometry: undefined,
    coordinates: undefined as unknown as [number, number],
    bbox: undefined as unknown as [number, number, number, number],
  },
];

/** Non-overlapping A → B transition fixtures. These stay test-only so pointer
 * transitions do not depend on the production dataset's current geometry. */
const transitionSingleA: Water = {
  ...raulSomesulTest,
  slug: 'transition-single-a',
  name: 'Râu Tranziție A',
  coordinates: [24.0, 46.1],
  bbox: [23.8, 46.02, 24.2, 46.18],
  geometry: { type: 'LineString', coordinates: [[23.8, 46.02], [24.0, 46.1], [24.2, 46.18]] },
  riverGroup: 'transition-single-a',
};
const transitionSingleB: Water = {
  ...transitionSingleA,
  slug: 'transition-single-b',
  name: 'Râu Tranziție B',
  coordinates: [24.0, 46.35],
  bbox: [23.8, 46.27, 24.2, 46.43],
  geometry: { type: 'LineString', coordinates: [[23.8, 46.27], [24.0, 46.35], [24.2, 46.43]] },
  riverGroup: 'transition-single-b',
};
const transitionMultiOwner: Water = {
  ...transitionSingleA,
  slug: 'transition-multi-owner',
  name: 'Râu Tranziție Comun',
  coordinates: [24.0, 46.6],
  bbox: [23.8, 46.5, 24.2, 46.7],
  geometry: { type: 'LineString', coordinates: [[23.8, 46.5], [24.0, 46.6], [24.2, 46.7]] },
  riverGroup: 'transition-multi',
  course_frac: 0.1,
};
const transitionMultiA: Water = {
  ...transitionMultiOwner,
  slug: 'transition-multi-a',
  name: 'Sector Tranziție A',
  geometry: undefined,
  course_frac: 0.25,
  sectorStart: 0.1,
  sectorEnd: 0.45,
};
const transitionMultiB: Water = {
  ...transitionMultiOwner,
  slug: 'transition-multi-b',
  name: 'Sector Tranziție B',
  // Dedicated non-overlapping pointer target; the owner remains the shared
  // course source used to build the focus slices.
  bbox: [23.8, 46.72, 24.2, 46.88],
  geometry: { type: 'LineString', coordinates: [[23.8, 46.8], [24.0, 46.8], [24.2, 46.8]] },
  // This pointer target is deliberately outside the shared geometry so the
  // first sector's focus stroke cannot intercept the second real tap.
  riverGroup: 'transition-multi-pointer',
  course_frac: 0.75,
  sectorStart: 0.55,
  sectorEnd: 0.9,
};
const transitionMultiC: Water = {
  ...transitionMultiA,
  slug: 'transition-multi-c',
  name: 'Sector Tranziție C',
  course_frac: 0.95,
  sectorStart: 0.9,
  sectorEnd: 1,
};

export const TRANSITION_WATERS: Water[] = [
  transitionSingleA,
  transitionSingleB,
  transitionMultiOwner,
  transitionMultiA,
  transitionMultiB,
  transitionMultiC,
];

/** Contracted lake — association (alpha) HAS permitUrl, so permit rows = 2. */
const laculTestBrasov: Water = {
  slug: 'lacul-test-brasov',
  name: 'Lacul Test',
  judet: 'Brașov',
  type: 'ape',
  subtype: 'lac',
  limite: 'Tot luciul de apă',
  dimensiune: '240 Ha',
  coordinates: [25.6, 45.65],
  bbox: [25.5, 45.6, 25.7, 45.7],
  asociatie: alphaEmbedded,
  geometry: {
    type: 'Polygon',
    coordinates: [
      [
        [25.5, 45.6],
        [25.7, 45.6],
        [25.7, 45.7],
        [25.5, 45.7],
        [25.5, 45.6],
      ],
    ],
  },
  locality: 'Orașul Test',
};

/** Contracted lake under beta (NO association permitUrl) — lake without
 * geometry, tests the bbox→point-fallback render + "verifică cu asociația". */
const laculBetaFaraPermis: Water = {
  slug: 'lacul-beta-fara-permis',
  name: 'Lacul Beta Fără Permis Online',
  judet: 'Ilfov',
  type: 'ape',
  subtype: 'lac',
  dimensiune: '12 Ha',
  coordinates: [26.1, 44.46],
  bbox: [26.05, 44.41, 26.15, 44.51],
  asociatie: betaEmbedded,
  // no geometry → bbox-fallback violet dot (t_cdb614de path)
  locality: 'Comuna Buftea Test',
};

/** Bucharest cluster — 4 lakes all within 25 km of (44.43, 26.10). */
const bucharestLakes: Water[] = [
  { slug: 'lacul-buc-1', name: 'Lacul București 1', coordinates: [26.1, 44.43] },
  { slug: 'lacul-buc-2', name: 'Lacul București 2', coordinates: [26.15, 44.45] },
  { slug: 'lacul-buc-3', name: 'Lacul București 3', coordinates: [26.05, 44.4] },
  { slug: 'lacul-buc-4', name: 'Lacul București 4', coordinates: [26.2, 44.5] },
].map((w, i) => {
  const [lon, lat] = w.coordinates;
  const half = 0.02;
  return {
    slug: w.slug,
    name: w.name,
    judet: 'Ilfov' as const,
    type: 'ape' as const,
    subtype: 'lac' as const,
    dimensiune: '8 Ha',
    coordinates: [lon, lat],
    bbox: [lon - half, lat - half, lon + half, lat + half],
    asociatie: betaEmbedded,
    geometry: {
      type: 'Polygon',
      coordinates: [
        [
          [lon - half, lat - half],
          [lon + half, lat - half],
          [lon + half, lat + half],
          [lon - half, lat + half],
          [lon - half, lat - half],
        ],
      ],
    },
    locality: i % 2 === 0 ? 'Comuna Buftea Test' : 'Comuna Otopeni Test',
  } satisfies Water;
});

/** Iași cluster — exactly 2 rivers within 25 km of (47.16, 27.59) → the
 * adaptive-radius branch expands 25 → 50 km. */
const iasiRivers: Water[] = [
  {
    slug: 'raul-bahlui-test',
    name: 'Râul Bahlui Test',
    judet: 'Iași',
    type: 'ape',
    subtype: 'rau',
    dimensiune: '20 km',
    coordinates: [27.59, 47.16],
    bbox: [27.54, 47.13, 27.64, 47.19],
    asociatie: betaEmbedded,
    geometry: {
      type: 'LineString',
      coordinates: [
        [27.54, 47.13],
        [27.59, 47.16],
        [27.64, 47.19],
      ],
    },
    locality: 'Municipiul Iași',
  },
  {
    slug: 'raul-nicolina-test',
    name: 'Râul Nicolina Test',
    judet: 'Iași',
    type: 'ape',
    subtype: 'rau',
    dimensiune: '15 km',
    coordinates: [27.65, 47.2],
    bbox: [27.6, 47.17, 27.7, 47.23],
    asociatie: betaEmbedded,
    geometry: {
      type: 'LineString',
      coordinates: [
        [27.6, 47.17],
        [27.65, 47.2],
        [27.7, 47.23],
      ],
    },
    locality: 'Municipiul Iași',
  },
  {
    // 3rd river ~43 km from the Iași point (47.16, 27.59) — outside the
    // default 25 km but inside the expanded 50 km, so the adaptive branch
    // stops exactly at EXPANDED_RADIUS_KM ("Rază: 50 km") instead of falling
    // through to the nearest-few fallback (t_ac6bc110 F7).
    slug: 'raul-jijia-test',
    name: 'Râul Jijia Test',
    judet: 'Iași',
    type: 'ape',
    subtype: 'rau',
    dimensiune: '10 km',
    coordinates: [28.0, 47.45],
    bbox: [27.95, 47.42, 28.05, 47.48],
    asociatie: betaEmbedded,
    geometry: {
      type: 'LineString',
      coordinates: [
        [27.95, 47.42],
        [28.0, 47.45],
        [28.05, 47.48],
      ],
    },
    locality: 'Comuna Jijia Test',
  },
];

/** Long-name water + locality:null in one (both edge cases). */
const longNameWater: Water = {
  slug: 'raul-cu-nume-lung',
  name: 'Râul cu un nume foarte lung pentru verificarea trunchierii textului în cartela de detalii la diferite lățimi de ecran și în lista de asociații',
  judet: 'Cluj',
  type: 'ape',
  subtype: 'rau',
  dimensiune: '9 km',
  coordinates: [23.6, 46.85],
  bbox: [23.5, 46.8, 23.7, 46.9],
  asociatie: alphaEmbedded,
  geometry: {
    type: 'LineString',
    coordinates: [
      [23.5, 46.8],
      [23.6, 46.85],
      [23.7, 46.9],
    ],
  },
  locality: null, // never appears under any locality filter
};

/** Uncontracted overlay entries (teal). */
const uncontractedRiver: Water = {
  slug: 'valea-testului-necontractata',
  name: 'Valea Testului',
  judet: 'Cluj',
  type: 'ape',
  subtype: 'rau',
  uncontracted: true,
  lengthKm: 12.3,
  coordinates: [23.2, 47.0],
  bbox: [23.1, 46.95, 23.3, 47.05],
  asociatie: null,
  geometry: {
    type: 'LineString',
    coordinates: [
      [23.1, 46.95],
      [23.2, 47.0],
      [23.3, 47.05],
    ],
  },
  locality: 'Comuna Test',
};

const uncontractedLake: Water = {
  slug: 'balta-test-necontractata',
  name: 'Balta Privată Test',
  judet: 'Brașov',
  type: 'ape',
  subtype: 'lac',
  uncontracted: true,
  areaHa: 42,
  coordinates: [25.7, 45.7],
  bbox: [25.65, 45.65, 25.75, 45.75],
  asociatie: null,
  geometry: {
    type: 'Polygon',
    coordinates: [
      [
        [25.65, 45.65],
        [25.75, 45.65],
        [25.75, 45.75],
        [25.65, 45.75],
        [25.65, 45.65],
      ],
    ],
  },
  locality: 'Orașul Test',
};

const counties: SeedData['counties'] = {
  type: 'FeatureCollection',
  features: [
    polygonFeature('Cluj', [22.8, 46.5, 24.5, 47.3]),
    polygonFeature('Brașov', [25.2, 45.4, 26.0, 46.0]),
    polygonFeature('Ilfov', [25.9, 44.3, 26.4, 44.6]),
    polygonFeature('Iași', [27.2, 46.9, 28.0, 47.5]),
  ],
};

function polygonFeature(name: string, b: [number, number, number, number]): GeoJSON.Feature<GeoJSON.Polygon, { name: string }> {
  const [minLon, minLat, maxLon, maxLat] = b;
  return {
    type: 'Feature',
    properties: { name },
    geometry: {
      type: 'Polygon',
      coordinates: [
        [
          [minLon, minLat],
          [maxLon, minLat],
          [maxLon, maxLat],
          [minLon, maxLat],
          [minLon, minLat],
        ],
      ],
    },
  };
}

/** Fixed geolocation test points (plan §6.1). */
export const GEO_POINTS = {
  bucharest: { lat: 44.43, lon: 26.1 },
  iasi: { lat: 47.16, lon: 27.59 },
} as const;

export const seed: SeedData = {
  associations: [alpha, beta],
  waters: [
    raulSomesulTest,
    laculTestBrasov,
    laculBetaFaraPermis,
    ...bucharestLakes,
    ...iasiRivers,
    longNameWater,
    ...UNVERIFIED_FOCUS_WATERS,
  ],
  rivers: [uncontractedRiver],
  lakes: [uncontractedLake],
  counties,
};