#!/usr/bin/env node
import { rm, mkdir } from 'node:fs/promises';

const output = process.env.MOBILE_MATRIX_OUTPUT;
const targets = [output, 'test-results/mobile-matrix', 'playwright-report'].filter(Boolean);
for (const target of targets) await rm(target, { recursive: true, force: true });
await mkdir('test-results', { recursive: true });
console.log(JSON.stringify({ reset: true, removed: targets, note: 'Browser site data, IndexedDB, service workers and Cache Storage are reset per Playwright context by resetBrowserState().' }, null, 2));
