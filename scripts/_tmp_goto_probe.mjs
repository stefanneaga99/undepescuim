import { chromium } from 'playwright';
const b = await chromium.launch({ args: ['--no-sandbox'] });
const p = await b.newPage();
console.log('launched, goto...');
const resp = await p.goto('http://localhost:3100/', { waitUntil: 'domcontentloaded', timeout: 30000 }).catch(e => 'GOTO-ERR: ' + e.message.split('\n')[0]);
console.log('result:', resp && resp.status ? 'status=' + resp.status() : resp);
await b.close();
