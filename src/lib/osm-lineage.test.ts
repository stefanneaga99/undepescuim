import { describe, expect, it } from 'vitest';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import ledger from '../../public/data/osm-lineage.json';

describe('OSM/ODbL source-lineage ledger', () => {
  it('is versioned and records every shipped OSM-derived artifact', () => {
    expect(ledger.schema_version).toBe(1);
    expect(ledger.license).toMatchObject({
      name: 'Open Database License (ODbL) 1.0',
      attribution_url: 'https://www.openstreetmap.org/copyright',
    });

    const paths = new Set(ledger.artifacts.map((artifact) => artifact.path));
    for (const path of [
      'public/data/waters.json',
      'public/data/uncontracted_rivers.json',
      'public/data/uncontracted_lakes.json',
      'public/data/uncontracted_majors.json',
      'public/data/waters_county_clips.json',
      'public/data/counties.geojson',
      'public/data/association_locations.json',
      'public/data/preview_class2_physical.json',
    ]) {
      expect(paths, path).toContain(path);
    }

    for (const artifact of ledger.artifacts) {
      expect(artifact.source_urls.length).toBeGreaterThan(0);
      expect(artifact.accessed_at).toMatch(/^2026-08-/);
      expect(artifact.sha256).toMatch(/^[a-f0-9]{64}$/);
      expect(artifact.transformations.length).toBeGreaterThan(0);
      expect(['odbl', 'mixed', 'unknown']).toContain(artifact.license_classification);
      expect(artifact.required_notice).toContain('OpenStreetMap');
      const digest = createHash('sha256')
        .update(readFileSync(resolve(process.cwd(), artifact.path)))
        .digest('hex');
      expect(digest, artifact.path).toBe(artifact.sha256);
    }
  });
});
