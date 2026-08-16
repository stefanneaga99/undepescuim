import { chromium } from 'playwright';
const browser = await chromium.launch({ args: ['--no-sandbox'] });
for (const ctx of browser.contexts()) {
  for (const p of ctx.pages()) if (p.url() !== 'about:blank') await p.close().catch(() => {});
}
const p = await browser.newPage();
await p.setViewportSize({ width: 1280, height: 800 });
await p.route('**/api/report', async (route) => {
  const post = route.request().postDataJSON();
  await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, issueUrl: null }) });
});
console.log('setup done, goto...');
const r = await p.goto('http://localhost:3100/', { waitUntil: 'domcontentloaded', timeout: 30000 }).catch(e => 'ERR: ' + e.message.split('\n')[0]);
console.log('result:', r && r.status ? 'status=' + r.status() : r);
await browser.close();
