/** Production panel/models/transports with scripted public peers; P4 uses actual owners. */
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { build } from 'esbuild';
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';

const output = resolve(process.argv[2] ?? '../.test-results/campaign-origin-browser-' + Date.now());
await mkdir(output, { recursive: true });
await build({ entryPoints: ['tests/browser/campaign_origin_entry.tsx'], bundle: true, format: 'esm', jsx: 'automatic', outfile: resolve(output, 'app.js') });
const fixture = JSON.parse(await readFile('tests/fixtures/campaign_origin/record.json', 'utf8'));
let mode = 'ready';
const requests = [], unexpected = [], errors = [];
const server = createServer(async (request, response) => {
  try {
    const path = new URL(request.url, 'http://localhost').pathname;
    requests.push([request.method, path]);
    let body = ''; for await (const chunk of request) body += chunk;
    const send = (value, status = 200) => { response.writeHead(status, { 'Content-Type': 'application/json' }); response.end(JSON.stringify(value)); };
    if (path === '/binding') return send(fixture.origin.origin.draft);
    if (path.startsWith('/api/planning/v1/campaign-origins/')) {
      assert.equal(request.method, 'GET');
      if (mode === 'denied') return send({ reason_code: 'planning_access_denied' }, 403);
      if (mode === 'missing') return send({ reason_code: 'campaign_origin_not_recorded' }, 404);
      if (mode === 'unavailable') return send({ error: 'owner_request_rejected' }, 404);
      const value = structuredClone(fixture.origin);
      if (mode === 'invalid') value.origin.proposal.rationale = 'Altered without a matching retained digest';
      return send(value);
    }
    if (path.startsWith('/api/runtime/v1/definition-drafts/')) { assert.equal(request.method, 'GET'); return send(fixture.draft); }
    if (path.startsWith('/api/runtime/v1/definition-commands/')) { assert.equal(request.method, 'GET'); return send(fixture.origin.origin.save.receipt); }
    if (path === '/api/research/v1/questions/read') { assert.equal(request.method, 'POST'); assert.deepEqual(JSON.parse(body), fixture.research[0].reference); return send(fixture.research[0]); }
    if (path === '/api/research/v1/evidence-needs/read') { assert.equal(request.method, 'POST'); assert.deepEqual(JSON.parse(body), fixture.research[1].reference); return send(fixture.research[1]); }
    if (path === '/app.js' || path === '/app.css') { response.setHeader('Content-Type', path.endsWith('js') ? 'text/javascript' : 'text/css'); return response.end(await readFile(resolve(output, path.slice(1)))); }
    if (path === '/favicon.ico') { response.writeHead(204); return response.end(); }
    if (path === '/') { response.setHeader('Content-Type', 'text/html'); return response.end('<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Campaign provenance fixture</title><link rel="stylesheet" href="/app.css"></head><body><div id="root"></div><script type="module" src="/app.js"></script></body></html>'); }
    unexpected.push([request.method, path]); send({ error: 'not_found' }, 404);
  } catch (error) { errors.push(error.message); response.writeHead(500); response.end('fixture failure'); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const browser = await chromium.launch({ headless: true });
const evidence = { profile: 'scripted-public-peers', screenshots: [], states: [], requests };
try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
  const page = await context.newPage();
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(`http://127.0.0.1:${server.address().port}`);
  await page.locator('.campaign-origin > summary').click();
  await page.getByRole('region', { name: 'Verified Research criteria' }).waitFor();
  await page.getByLabel('Inspect retained Research context').selectOption('1');
  await page.getByRole('region', { name: 'Verified Research criteria' }).waitFor();
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    const issues = (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()).violations;
    assert.deepEqual(issues.map(issue => issue.id), []);
    const name = `origin-${width}.png`; await page.screenshot({ path: resolve(output, name), fullPage: true }); evidence.screenshots.push(name);
  }
  for (const state of ['denied', 'missing', 'unavailable', 'invalid']) {
    mode = state;
    await page.getByRole('button', { name: state === 'denied' ? 'Refresh verified provenance' : 'Retry provenance read', exact: true }).click();
    const message = { denied: 'Campaign provenance is not available to this session.',
      missing: 'No Planning origin is recorded for this exact draft. This does not establish who authored it.',
      unavailable: 'Campaign provenance is temporarily unavailable.', invalid: 'The campaign provenance could not be verified.' }[state];
    await page.getByText(message, { exact: true }).waitFor();
    assert.equal(await page.getByRole('region', { name: 'Verified Research criteria' }).count(), 0); evidence.states.push(state);
  }
  assert.deepEqual(unexpected, []); assert.deepEqual(errors, []);
  await writeFile(resolve(output, 'evidence.json'), JSON.stringify(evidence, null, 2));
  console.log(JSON.stringify({ passed: true, output, states: evidence.states, screenshots: evidence.screenshots }));
} finally { await browser.close(); await new Promise(resolve => server.close(resolve)); }
