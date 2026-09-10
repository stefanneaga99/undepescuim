import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import type { Water } from '@/types/data';

let index: Map<string, Water> | undefined;
function getIndex(): Map<string, Water> {
  if (index) return index;
  const values = ['waters.json', 'uncontracted_rivers.json', 'uncontracted_lakes.json'].flatMap((file) => {
    try { const parsed: unknown = JSON.parse(readFileSync(join(process.cwd(), 'public/data', file), 'utf8')); return Array.isArray(parsed) ? parsed : []; }
    catch { return []; }
  }) as Water[];
  index = new Map(values.filter((water) => typeof water.slug === 'string').map((water) => [water.slug, water]));
  return index;
}
export function canonicalWater(slug: string, name: string): Water | null {
  const water = getIndex().get(slug);
  return water && water.name.normalize('NFC') === name.normalize('NFC') ? water : null;
}