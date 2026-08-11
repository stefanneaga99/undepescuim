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
function assocContact(a) {
  const addr = a.adrese?.[0]?.adresa ?? null;
  return {
    adresa: a.adresa ?? addr?.adresa ?? undefined,
    telefon: a.telefon ?? addr?.telefon ?? undefined,
    siteUrl: a.siteUrl ?? undefined,
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
        }
      : null,
  }))
  .sort((x, y) => x.name.localeCompare(y.name, 'ro'));

// --- write -----------------------------------------------------------------
const outDir = join(root, 'public/data');
mkdirSync(outDir, { recursive: true });
writeFileSync(join(outDir, 'associations.json'), JSON.stringify(associations));
writeFileSync(join(outDir, 'waters.json'), JSON.stringify(waters));

console.log(
  `associations: ${associations.length} (${associations.filter((a) => a.ape > 0).length} with waters)`,
);
console.log(`waters: ${waters.length} (${waters.filter((w) => w.asociatie).length} with association)`);
console.log(`output: ${outDir}`);
