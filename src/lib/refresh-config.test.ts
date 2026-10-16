import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import {
  DEFAULT_REFRESH_DIR,
  resolveRefreshOutputDir,
  safeOutputPath,
} from '../../scripts/lib/refresh-config.mjs';

const ROOT = process.cwd();

describe('refresh output dir', () => {
  it('defaults to the staging dir under data/raw/refresh', () => {
    expect(resolveRefreshOutputDir('/repo', {})).toBe(resolve('/repo', DEFAULT_REFRESH_DIR));
    expect(DEFAULT_REFRESH_DIR.replace(/\\/g, '/')).toBe('data/raw/refresh');
  });

  it('ignores a blank REFRESH_OUTPUT_DIR', () => {
    expect(resolveRefreshOutputDir('/repo', { REFRESH_OUTPUT_DIR: '   ' })).toBe(
      resolve('/repo', DEFAULT_REFRESH_DIR),
    );
  });

  it('honours a relative or absolute override outside public/', () => {
    expect(resolveRefreshOutputDir('/repo', { REFRESH_OUTPUT_DIR: 'tmp/out' })).toBe('/repo/tmp/out');
    expect(resolveRefreshOutputDir('/repo', { REFRESH_OUTPUT_DIR: '/var/out' })).toBe('/var/out');
  });

  it('refuses public/ and anything below it', () => {
    for (const bad of ['public', 'public/data', './public/data/x', '/repo/public/data']) {
      expect(() => resolveRefreshOutputDir('/repo', { REFRESH_OUTPUT_DIR: bad })).toThrow(/inside public/);
    }
  });

  it('does not treat a sibling that merely starts with "public" as public/', () => {
    expect(resolveRefreshOutputDir('/repo', { REFRESH_OUTPUT_DIR: 'public-staging' })).toBe(
      '/repo/public-staging',
    );
  });
});

describe('safeOutputPath', () => {
  const out = '/repo/data/raw/refresh';

  it('joins a normal relative path', () => {
    expect(safeOutputPath(out, 'waters.json')).toBe('/repo/data/raw/refresh/waters.json');
    expect(safeOutputPath(out, 'sub/dir/a.geojson')).toBe('/repo/data/raw/refresh/sub/dir/a.geojson');
  });

  it('rejects empty, non-string, absolute and escaping paths', () => {
    expect(() => safeOutputPath(out, '')).toThrow(/non-empty/);
    expect(() => safeOutputPath(out, undefined as unknown as string)).toThrow(/non-empty/);
    expect(() => safeOutputPath(out, '/etc/passwd')).toThrow(/relative/);
    expect(() => safeOutputPath(out, '../waters.json')).toThrow(/escapes/);
    expect(() => safeOutputPath(out, 'a/../../x.json')).toThrow(/escapes/);
    expect(() => safeOutputPath(out, '.')).toThrow(/escapes/);
  });
});

describe('refresh pipeline contract (static)', () => {
  it('refresh-data.mjs resolves its output dir through the guarded helper', () => {
    const src = readFileSync(resolve(ROOT, 'scripts/refresh-data.mjs'), 'utf8');
    expect(src).toContain('resolveRefreshOutputDir(ROOT)');
    expect(src).toContain('safeOutputPath(DATA_DIR, relPath)');
    expect(src).not.toMatch(/'public'\s*,\s*'data'/);
  });

  it('the monthly workflow never stages or commits public/data', () => {
    const wf = readFileSync(resolve(ROOT, '.github/workflows/data-refresh.yml'), 'utf8');
    expect(wf).not.toMatch(/public\/data/);
    expect(wf).not.toMatch(/git (add|commit|push)/);
    expect(wf).toContain('upload-artifact');
  });
});
