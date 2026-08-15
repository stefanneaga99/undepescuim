#!/usr/bin/env node
/**
 * Extract public map data from the arebaltapeste.ro probe snapshots.
 *
 * Inputs:  data/raw/arebaltapeste_probe/snapshot_asociatii.json (82)
 *          data/raw/arebaltapeste_probe/snapshot_waters.json   (426)
 * Outputs: public/data/associations.json
 *          public/data/waters.json
 *
 * Shape contract: src/types/data.ts (Association / Water).
 * - `ape` (water count per association) is computed from the waters dataset.
 * - Association contact is flattened from adrese[] (source keeps it nested).
 */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const probeDir = join(root, 'data/raw/arebaltapeste_probe');

const assocRaw = JSON.parse(readFileSync(join(probeDir, 'snapshot_asociatii.json'), 'utf8'));
const watersRaw = JSON.parse(readFileSync(join(probeDir, 'snapshot_waters.json'), 'utf8'));

// --- water count per association slug -------------------------------------
const countBySlug = new Map();
for (const w of watersRaw) {
  const slug = w.asociatie?.slug;
  if (slug) countBySlug.set(slug, (countBySlug.get(slug) ?? 0) + 1);
}

// --- associations ----------------------------------------------------------
// F1a: derive the permit issuer from the association name the same way the
// pipeline does (fetch_arebaltapeste.py association_type()): anpa -> anadspa
// (national portal), silvica/romsilva -> romsilva, everything else -> asociatie.
function assocTypeToIssuer(a) {
  const n = (a.name || '').toLowerCase();
  if (n.startsWith('anpa')) return 'anadspa';
  if (n.includes('silvica') || n.includes('romsilva')) return 'romsilva';
  return 'asociatie';
}

function assocContact(a) {
  const addr = a.adrese?.[0]?.adresa ?? null;
  return {
    adresa: a.adresa ?? addr?.adresa ?? undefined,
    telefon: a.telefon ?? addr?.telefon ?? undefined,
    siteUrl: a.siteUrl ?? undefined,
    permitUrl: a.link_permis ?? undefined,
    permitIssuer: assocTypeToIssuer(a),
  };
}

const associations = assocRaw
  .map((a) => ({
    slug: a.slug,
    name: a.name,
    name_long: a.name_long ?? a.name,
    ape: countBySlug.get(a.slug) ?? 0,
    ...assocContact(a),
    bbox: a.bbox,
    id: a.id,
  }))
  .sort((x, y) => x.name.localeCompare(y.name, 'ro'));

// --- waters ----------------------------------------------------------------
const waters = watersRaw
  .map((w) => ({
    slug: w.slug,
    name: w.name,
    judet: w.judet,
    type: w.type,
    subtype: w.subtype,
    limite: w.limite ?? '',
    dimensiune: w.dimensiune ?? '',
    pescuit_interzis: !!w.pescuit_interzis,
    referinta: w.referinta ?? '',
    coordinates: w.coordinates,
    driving: w.driving,
    bbox: w.bbox,
    asociatie: w.asociatie
      ? {
          name: w.asociatie.name,
          name_long: w.asociatie.name_long ?? null,
          slug: w.asociatie.slug,
          telefon: w.asociatie.telefon ?? undefined,
          adresa: w.asociatie.adresa ?? undefined,
          siteUrl: w.asociatie.siteUrl ?? undefined,
          permitUrl: w.asociatie.link_permis ?? undefined,
          permitIssuer: assocTypeToIssuer(w.asociatie),
        }
      : null,
  }))
  .sort((x, y) => x.name.localeCompare(y.name, 'ro'));

// --- write -----------------------------------------------------------------
const outDir = join(root, 'public/data');
mkdirSync(outDir, { recursive: true });

// F1a: merge manual/curated permit enrichment (data/processed/permit_enrichment.json
// + permit_overrides.json, produced by scripts/backfill_permit_urls.py) on top of
// whatever the source carried. Overrides win; known fills gaps. This makes the
// field survive re-extraction even if the upstream probe later drops link_permis.
function mergePermitEnrichment(list, bySlugKey) {
  const enrichPath = join(root, 'data/processed/permit_enrichment.json');
  const overridesPath = join(root, 'data/processed/permit_overrides.json');
  const known = new Map();
  const overrides = new Map();
  try {
    const e = JSON.parse(readFileSync(enrichPath, 'utf8'));
    for (const r of e.known ?? []) known.set(r.slug, r);
    for (const r of e.overrides ?? []) overrides.set(r.slug, r);
  } catch {
    // no enrichment file yet — passthrough from the source is all we have
    return;
  }
  for (const item of list) {
    const rec = overrides.get(item[bySlugKey]) ?? known.get(item[bySlugKey]);
    if (!rec?.permit_url) continue;
    item.permitUrl = rec.permit_url;
    if (rec.permit_issuer) item.permitIssuer = rec.permit_issuer;
  }
}

mergePermitEnrichment(associations, 'slug');
for (const w of waters) {
  if (w.asociatie) mergePermitEnrichment([w.asociatie], 'slug');
}

writeFileSync(join(outDir, 'associations.json'), JSON.stringify(associations));
writeFileSync(join(outDir, 'waters.json'), JSON.stringify(waters));

console.log(
  `associations: ${associations.length} (${associations.filter((a) => a.ape > 0).length} with waters)`,
);
console.log(`waters: ${waters.length} (${waters.filter((w) => w.asociatie).length} with association)`);
console.log(`output: ${outDir}`);
