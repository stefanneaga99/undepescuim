#!/usr/bin/env node
import { spawn } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import { setTimeout as delay } from 'node:timers/promises';
const port = process.env.E2E_PORT || '3100';
const base = process.env.PLAYWRIGHT_BASE_URL || `http://127.0.0.1:${port}`;
const outDir = process.env.MOBILE_MATRIX_OUTPUT || `test-results/mobile-matrix-${Date.now()}`;
const projects = ['iphone-current', 'iphone-previous', 'pixel-current', 'pixel-previous', 'samsung-current', 'samsung-previous'];
await mkdir(outDir, { recursive: true });
const run = (command, args, env = {}) => new Promise((resolve) => {
  const child = spawn(command, args, { env: { ...process.env, ...env }, stdio: ['ignore', 'pipe', 'pipe'] });
  let stdout = '', stderr = '';
  child.stdout.on('data', (chunk) => { stdout += chunk; process.stdout.write(chunk); });
  child.stderr.on('data', (chunk) => { stderr += chunk; process.stderr.write(chunk); });
  child.on('close', (code, signal) => resolve({ code: code ?? 1, signal, stdout, stderr }));
});
const build = await run('npm', ['run', 'build']);
if (build.code !== 0) process.exit(build.code);
const server = spawn('npm', ['run', 'start'], { env: { ...process.env, PORT: port }, stdio: ['ignore', 'pipe', 'pipe'] });
let serverLog = '';
server.stdout.on('data', (chunk) => { serverLog += chunk; });
server.stderr.on('data', (chunk) => { serverLog += chunk; });
try {
  let ready = false;
  for (let attempt = 0; attempt < 60 && !ready; attempt += 1) {
    const probe = await fetch(`${base}/`).catch(() => null);
    ready = Boolean(probe?.ok);
    if (!ready) await delay(1000);
  }
  if (!ready) throw new Error(`server did not become ready\n${serverLog}`);
  const e2e = await run('npx', ['playwright', 'test', ...projects.flatMap((project) => ['--project', project]), '--workers=1', '--reporter=line'], {
    E2E_MOBILE_MATRIX: '1', E2E_SERVER_READY: 'true', PLAYWRIGHT_BASE_URL: base,
    PLAYWRIGHT_OUTPUT_DIR: `${outDir}/playwright`, PLAYWRIGHT_REPORT_DIR: `${outDir}/report`,
  });
  const perf = await run('node', ['scripts/_perf_map.mjs', base], { PERF_THROTTLE: process.env.PERF_THROTTLE || '1' });
  await writeFile(`${outDir}/e2e.log`, e2e.stdout + e2e.stderr);
  await writeFile(`${outDir}/performance.log`, perf.stdout + perf.stderr);
  const summary = { base, projects, e2eExitCode: e2e.code, performanceExitCode: perf.code, output: outDir };
  await writeFile(`${outDir}/summary.json`, JSON.stringify(summary, null, 2) + '\n');
  process.exitCode = e2e.code || perf.code;
} finally { server.kill('SIGTERM'); }
