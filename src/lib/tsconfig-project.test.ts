import { readFileSync } from 'node:fs';
import path from 'node:path';
import ts from 'typescript';
import { describe, expect, it } from 'vitest';

describe('TypeScript project boundaries', () => {
  it('excludes local worktrees while retaining canonical source and tests', () => {
    const projectRoot = process.cwd();
    const configPath = path.join(projectRoot, 'tsconfig.json');
    const config = JSON.parse(readFileSync(configPath, 'utf8')) as ts.CompilerOptions & {
      include?: string[];
      exclude?: string[];
    };
    const parsed = ts.parseJsonConfigFileContent(config, ts.sys, projectRoot);
    const projectFiles = parsed.fileNames.map((file) => path.relative(projectRoot, file));

    expect(config.exclude).toEqual(
      expect.arrayContaining(['node_modules', 'batches', '.local-work', '.worktrees', 'test-results']),
    );
    expect(projectFiles.some((file) => file.startsWith('src/'))).toBe(true);
    expect(projectFiles.some((file) => file.startsWith('tests/'))).toBe(true);
    expect(projectFiles.some((file) => /^(batches|\.local-work|\.worktrees|test-results)\//.test(file))).toBe(false);
  });
});
