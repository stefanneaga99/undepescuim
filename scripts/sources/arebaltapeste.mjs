/**
 * Source: arebaltapeste.ro backend API (api.arebaltapeste.ro).
 *
 * Romanian public fishing waters ("ape publice") contracted to angling
 * associations, plus the association directory. The site's Vue SPA paginates
 * this REST API; full dataset fits in a handful of requests (426 waters,
 * 82 associations as of 2026-08).
 *
 * Endpoints (discovered in probe 2026-08-11, see data/raw/arebaltapeste_probe_report.md):
 *   GET /api/search?type=ape&limit&skip -> { metadata:{count}, items:[{type,item}] }
 *        THE primary listing endpoint; paginates correctly (~20/page cap).
 *   GET /api/asociatii?limit&skip        -> { docs, totalDocs, ... } (returns all docs in one call)
 *   NOTE: /api/ape?limit&skip IGNORES skip and always returns the same first page — do not use.
 *
 * Outputs:
 *   waters.json       — normalized contracted-waters records
 *   associations.json — normalized association records
 *   waters.geojson    — FeatureCollection (Point) for the Leaflet map
 */
const BASE = 'https://api.arebaltapeste.ro';
const USER_AGENT =
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 undepescuim-refresh/1.0';

async function fetchJson(url) {
  const res = await fetch(url, {
    headers: { 'User-Agent': USER_AGENT, Accept: 'application/json' },
    signal: AbortSignal.timeout(30000),
  });
  if (!res.ok) {
    throw new Error(`${url} -> HTTP ${res.status}`);
  }
  return res.json();
}

/** Fetch every water via /api/search?type=ape (the only endpoint that honors skip). */
async function fetchAllWaters() {
  const items = [];
  let skip = 0;
  const PAGE = 100; // server caps ~20/page; loop until we have them all
  let total = null;
  for (let guard = 0; guard < 100; guard++) {
    const body = await fetchJson(`${BASE}/api/search?type=ape&limit=${PAGE}&skip=${skip}`);
    const batch = body.items || [];
    if (total === null) {
      total = body.metadata?.count ?? batch.length;
    }
    for (const entry of batch) {
      if (entry && entry.item) items.push(entry.item);
    }
    skip = items.length;
    if (items.length >= total || batch.length === 0) break;
  }
  if (items.length !== total) {
    console.warn(`[arebaltapeste] expected ${total} waters, collected ${items.length}`);
  }
  return items;
}

/** Associations: one call returns the whole directory. */
async function fetchAssociations() {
  const body = await fetchJson(`${BASE}/api/asociatii?limit=200&skip=0`);
  if (!Array.isArray(body.docs)) {
    throw new Error('arebaltapeste: asociatii response has no docs array');
  }
  return body.docs;
}

function normalizeWater(raw) {
  const a = raw.asociatie || {};
  return {
    id: raw.id,
    slug: raw.slug,
    name: raw.name,
    judet: raw.judet,
    subtype: raw.subtype, // lac | rau
    dimensiune: raw.dimensiune,
    limite: raw.limite,
    referinta: raw.referinta,
    pescuit_interzis: Boolean(raw.pescuit_interzis),
    coordinates: raw.coordinates, // [lng, lat]
    bbox: raw.bbox,
    asociatie: {
      id: a.id,
      name: a.name,
      name_long: a.name_long,
      slug: a.slug,
      telefon: a.telefon,
      siteUrl: a.siteUrl,
      link_permis: a.link_permis,
    },
  };
}

function normalizeAssociation(raw) {
  return {
    id: raw.id,
    slug: raw.slug,
    name: raw.name,
    name_long: raw.name_long,
    adresa: raw.adresa,
    telefon: raw.telefon,
    siteUrl: raw.siteUrl,
    link_permis: raw.link_permis,
    adrese: Array.isArray(raw.adrese)
      ? raw.adrese.map((e) => ({
          adresa: e?.adresa?.adresa,
          telefon: e?.adresa?.telefon,
          coordinates: e?.adresa?.coordinates,
        }))
      : [],
    bbox: raw.bbox,
  };
}

export const name = 'arebaltapeste';

export async function collect() {
  const [rawWaters, rawAssociations] = await Promise.all([
    fetchAllWaters(),
    fetchAssociations(),
  ]);

  if (rawWaters.length === 0) {
    throw new Error('arebaltapeste: zero waters fetched — refusing to write empty dataset');
  }
  if (rawAssociations.length === 0) {
    throw new Error('arebaltapeste: zero associations fetched — refusing to write empty dataset');
  }

  const waters = rawWaters.map(normalizeWater);
  const associations = rawAssociations.map(normalizeAssociation);

  const uniqueWaterIds = new Set(waters.map((w) => w.id));
  if (uniqueWaterIds.size !== waters.length) {
    throw new Error(
      `arebaltapeste: duplicate water records after dedup check (${waters.length} records, ${uniqueWaterIds.size} unique ids)`
    );
  }

  const generatedAt = new Date().toISOString();
  const geojson = {
    type: 'FeatureCollection',
    generatedAt,
    features: waters
      .filter((w) => Array.isArray(w.coordinates) && w.coordinates.length >= 2)
      .map((w) => ({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: w.coordinates },
        properties: { id: w.id, name: w.name, judet: w.judet, subtype: w.subtype, asociatie: w.asociatie.name },
      })),
  };

  return {
    'waters.json': { generatedAt, count: waters.length, items: waters },
    'associations.json': { generatedAt, count: associations.length, items: associations },
    'waters.geojson': geojson,
  };
}
