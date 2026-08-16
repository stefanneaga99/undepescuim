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
  ],
  rivers: [uncontractedRiver],
  lakes: [uncontractedLake],
  counties,
};