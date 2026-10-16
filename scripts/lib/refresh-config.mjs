/**
 * Output-location rules for scripts/refresh-data.mjs.
 *
 * The monthly refresh must never write into `public/data/`: the scrapers emit
 * `{generatedAt, count, items}` wrappers and extra files that the frontend
 * cannot read (it parses a bare `Water[]`). Refresh output goes to a staging
 * directory (default `data/raw/refresh/`) and is only inspected / uploaded as a
 * workflow artifact. Promoting data into `public/data/` is a separate,
 * reviewed step (see docs/plans/river-geometry-v2.md, T0.2).
 */
import path from 'node:path';

/** Default staging directory, relative to the repository root. */
export const DEFAULT_REFRESH_DIR = path.join('data', 'raw', 'refresh');

/** True when `child` is `parent` itself or lies inside it. */
function isInside(parent, child) {
  const rel = path.relative(parent, child);
  return rel === '' || (!rel.startsWith('..') && !path.isAbsolute(rel));
}

/**
 * Resolve the directory refresh outputs are written to.
 * Honours `REFRESH_OUTPUT_DIR` (absolute, or relative to `root`). Throws if the
 * result is `public/` or anywhere below it.
 */
export function resolveRefreshOutputDir(root, env = process.env) {
  const configured = env.REFRESH_OUTPUT_DIR;
  const dir = path.resolve(root, configured && configured.trim() ? configured : DEFAULT_REFRESH_DIR);
  if (isInside(path.resolve(root, 'public'), dir)) {
    throw new Error(
      `refresh output dir "${dir}" is inside public/ — refresh must not publish data directly`,
    );
  }
  return dir;
}

/**
 * Join a source-provided relative path onto the output dir, refusing anything
 * that would escape it (absolute paths, `..` segments).
 */
export function safeOutputPath(outputDir, relPath) {
  if (typeof relPath !== 'string' || relPath.length === 0) {
    throw new Error('output path must be a non-empty string');
  }
  if (path.isAbsolute(relPath)) {
    throw new Error(`output path "${relPath}" must be relative`);
  }
  const target = path.resolve(outputDir, relPath);
  if (!isInside(outputDir, target) || target === path.resolve(outputDir)) {
    throw new Error(`output path "${relPath}" escapes the refresh output dir`);
  }
  return target;
}
