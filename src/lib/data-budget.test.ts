import { afterEach, describe, expect, it } from 'vitest';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import {
  ALLOWED_DATA_FILES,
  LAZY_DATA_FILES,
  findUnexpectedFiles,
} from '../../scripts/lib/data-budget.mjs';

const dirs: string[] = [];
function makeDir(files: string[]): string {
  const dir = mkdtempSync(join(tmpdir(), 'data-budget-'));
  dirs.push(dir);
  for (const f of files) writeFileSync(join(dir, f), '[]');
  return dir;
}

afterEach(() => {
  while (dirs.length) rmSync(dirs.pop()!, { recursive: true, force: true });
});

describe('public/data allowlist', () => {
  it('accepts a directory that only holds allowed files', () => {
    const dir = makeDir(['waters.json', 'associations.json', '.gitkeep', 'meta.json']);
    expect(findUnexpectedFiles(dir)).toEqual([]);
  });

  it('reports backups, scraper wrappers and unknown files, sorted', () => {
    const dir = makeDir([
      'waters.json',
      'waters.json.audit-backup.json',
      'waters.geojson',
      'waters_geocoded.geojson',
      'reciprocity.json',
    ]);
    expect(findUnexpectedFiles(dir)).toEqual([
      'reciprocity.json',
      'waters.geojson',
      'waters.json.audit-backup.json',
      'waters_geocoded.geojson',
    ]);
  });

  it('treats sub-directories as unexpected', () => {
    const dir = makeDir(['waters.json']);
    mkdirSync(join(dir, 'extra'));
    expect(findUnexpectedFiles(dir)).toEqual(['extra']);
  });

  it('returns an empty list for a missing directory but rethrows other errors', () => {
    expect(findUnexpectedFiles(join(tmpdir(), 'does-not-exist-data-budget'))).toEqual([]);
    const dir = makeDir(['waters.json']);
    // readdir on a regular file fails with ENOTDIR, which must not be swallowed
    expect(() => findUnexpectedFiles(join(dir, 'waters.json'))).toThrow();
  });

  it('honours a custom allowlist', () => {
    const dir = makeDir(['a.json', 'b.json']);
    expect(findUnexpectedFiles(dir, ['a.json'])).toEqual(['b.json']);
  });

  it('keeps the lazy-file list a subset of the allowlist', () => {
    for (const file of LAZY_DATA_FILES) expect(ALLOWED_DATA_FILES).toContain(file);
  });

  it('the committed public/data holds nothing outside the allowlist', () => {
    expect(findUnexpectedFiles(resolve(process.cwd(), 'public', 'data'))).toEqual([]);
  });
});
