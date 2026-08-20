#!/usr/bin/env node
import { spawn, execFileSync } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import { setTimeout as delay } from 'node:timers/promises';
const port = process.env.E2E_PORT || '3100';
const base = process.env.PLAYWRIGHT_BASE_URL || `http://127.0.0.1:${port}`;
const outDir = process.env.MOBILE_MATRIX_OUTPUT || `test-results/mobile-matrix-${Date.now()}`;
const projects = ['iphone-current', 'iphone-previous', 'pixel-current', 'pixel-previous', 'samsung-current', 'samsung-previous'];

function summarizeE2e(output) {
  const counts = {
    passed: Number(output.match(/(?:^|\n)\s*(\d+) passed(?:\s|$)/m)?.[1] || 0),
    failed: Number(output.match(/(?:^|\n)\s*(\d+) failed(?:\s|$)/m)?.[1] || 0),
    skipped: Number(output.match(/(?:^|\n)\s*(\d+) skipped(?:\s|$)/m)?.[1] || 0),
    flaky: Number(output.match(/(?:^|\n)\s*(\d+) flaky(?:\s|$)/m)?.[1] || 0),
    total: 0,
  };
  counts.total = counts.passed + counts.failed + counts.skipped;
  const actionableFailures = output
    .split('\n')
    .filter((line) => /^\s*[✘✗×]\s+\d+/.test(line) || /Error:|failed/i.test(line))
    .map((line) => line.trim())
    .filter((line, index, lines) => lines.indexOf(line) === index)
    .slice(0, 20);
  return { counts, actionableFailures };
}

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
const server = spawn('npm', ['run', 'start'], {
  env: { ...process.env, PORT: port },
  stdio: ['ignore', 'pipe', 'pipe'],
  // npm launches a shell and Next launches another child. Use a process group
  // so cleanup cannot leave a server (and its inherited pipes) behind.
  detached: process.platform !== 'win32',
});
let serverLog = '';
let serverExit = null;
server.stdout.on('data', (chunk) => { serverLog += chunk; });
server.stderr.on('data', (chunk) => { serverLog += chunk; });
server.on('exit', (code, signal) => { serverExit = { code, signal }; });
try {
  let ready = false;
  for (let attempt = 0; attempt < 60 && !ready; attempt += 1) {
    if (serverExit) {
      throw new Error(`server exited before becoming ready (code=${serverExit.code}, signal=${serverExit.signal})\n${serverLog}`);
    }
    const probe = await fetch(`${base}/`).catch(() => null);
    // A successful probe alone can hit an unrelated process already bound to
    // the port. Require the child we spawned to announce Next readiness too.
    ready = Boolean(probe?.ok && /Ready in/.test(serverLog));
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
  const e2eSummary = summarizeE2e(e2e.stdout + e2e.stderr);
  const gitSha = (() => { try { return execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(); } catch { return null; } })();
  const summary = {
    schemaVersion: 2,
    runAt: new Date().toISOString(),
    gitSha,
    base,
    projects,
    browserMode: 'chromium-emulation',
    networkProfile: 'fast-3g (scripts/_perf_map.mjs)',
    e2eExitCode: e2e.code,
    e2e: e2eSummary,
    performanceExitCode: perf.code,
    output: outDir,
    artifacts: { e2eLog: `${outDir}/e2e.log`, performanceLog: `${outDir}/performance.log`, report: `${outDir}/report` },
  };
  await writeFile(`${outDir}/summary.json`, JSON.stringify(summary, null, 2) + '\n');
  process.exitCode = e2e.code || perf.code;
} finally {
  // Kill the whole detached group; killing npm alone can orphan Next and keep
  // stdout/stderr pipes open, leaving this runner stuck after artifacts exist.
  if (server.pid && process.platform !== 'win32') {
    try { process.kill(-server.pid, 'SIGTERM'); } catch {}
  } else {
    server.kill('SIGTERM');
  }
}
