/** Actual installed-owner browser acceptance. Credentials arrive only on stdin. */
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import { startHost } from './explore_live_host.mjs';

let raw = '';
for await (const chunk of process.stdin) { raw += chunk; if (Buffer.byteLength(raw) > 1048576) throw new Error('input_limit'); }
const { owners, records, output } = JSON.parse(raw); raw = '';
await mkdir(output, { recursive: true });
const pins = { graph: records.head.snapshot, experiment: records.comparison.properties.request.experiment,
  observations: records.comparison.properties.request.observations };
const host = await startHost(owners, pins, resolve(output, 'assets'));
let browser;
const evidence = { status: 'running', scenarios: [], screenshots: [], requests: [] };
try {
  browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
  const page = await context.newPage();
  const errors = [], authorizations = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', req => { if (req.headers().authorization) authorizations.push(req.url()); });
  page.setDefaultTimeout(15000);
  await page.goto(host.url);
  const concept = page.getByRole('button', { name: 'A', exact: true }).first();
  await concept.focus(); await page.keyboard.press('Enter');
  await page.getByRole('button', { name: 'A correlates with B', exact: true }).click();
  await page.getByText('A correlates with B under synthetic conditions.', { exact: true }).waitFor();
  await page.getByRole('button', { name: 'Read source passage 1', exact: true }).click();
  const source = page.getByRole('region', { name: 'Verified source passage', exact: true });
  await source.waitFor();
  assert.match(await source.textContent(), /Synthetic claims are not scientifically accepted\./);
  const span = await page.evaluate(() => window.liveExplore.model.snapshot.regions.source.value);
  assert.deepEqual(span.span, records.span);
  evidence.scenarios.push('keyboard concept -> exact pinned claim -> hash-verified source span');
  await page.getByRole('button', { name: 'Inspect conversion 1', exact: true }).click();
  await page.getByRole('region', { name: 'Conversion history', exact: true }).waitFor();
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: width === 1440 ? 1000 : 844 });
    const scan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    assert.deepEqual(scan.violations.map(v => ({ id: v.id, targets: v.nodes.map(n => n.target) })), []);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await source.scrollIntoViewIfNeeded();
    const conversion = page.getByRole('region', { name: 'Conversion history', exact: true });
    await conversion.scrollIntoViewIfNeeded();
    await page.evaluate(() => new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done))));
    assert.equal(await source.isVisible(), true); assert.equal(await conversion.isVisible(), true);
    assert.match(await source.textContent(), /Synthetic claims are not scientifically accepted\./);
    const image = `actual-source-${width}.png`;
    await page.screenshot({ path: resolve(output, image), fullPage: true }); evidence.screenshots.push(image);
  }
  await page.evaluate(query => window.liveExplore.model.search(query), records.windows.graph_pages[0].request);
  await page.getByRole('button', { name: 'Next concepts', exact: true }).click();
  await page.waitForFunction(() => window.liveExplore.model.snapshot.regions.search.phase === 'ready' && window.liveExplore.model.snapshot.regions.search.value.request.position !== null);
  assert.deepEqual(await page.evaluate(() => window.liveExplore.model.snapshot.regions.search.value), records.windows.graph_pages[1]);
  await page.getByRole('button', { name: 'Specimens', exact: true }).click();
  await page.getByRole('table', { name: 'Samples in the pinned experiment' }).waitFor();
  await page.evaluate(query => window.liveExplore.model.specimens(query), records.windows.specimen_pages[0].request);
  await page.getByRole('button', { name: 'Next specimens', exact: true }).click();
  await page.waitForFunction(() => window.liveExplore.model.snapshot.regions.specimens.phase === 'ready' && window.liveExplore.model.snapshot.regions.specimens.value.request.position !== null);
  assert.deepEqual(await page.evaluate(() => window.liveExplore.model.snapshot.regions.specimens.value), records.windows.specimen_pages[1]);
  await page.getByRole('button', { name: 'Properties', exact: true }).click();
  await page.getByRole('table', { name: 'Observations under the pinned method' }).waitFor();
  await page.evaluate(query => window.liveExplore.model.properties(query), records.windows.property_pages[0].request);
  await page.getByRole('button', { name: 'Next observations', exact: true }).click();
  await page.waitForFunction(() => window.liveExplore.model.snapshot.regions.properties.phase === 'ready' && window.liveExplore.model.snapshot.regions.properties.value.request.position !== null);
  assert.deepEqual(await page.evaluate(() => window.liveExplore.model.snapshot.regions.properties.value), records.windows.property_pages[1]);
  evidence.scenarios.push('explicit size-one windows and visible next controls preserve owner graph/specimen/property pages');
  const foreign = structuredClone(pins); foreign.graph = null; foreign.experiment.scope.project_id = 'unowned-project';
  for (const ref of foreign.observations) ref.scope.project_id = 'unowned-project';
  await page.evaluate(context => window.liveExplore.model.bind(context), foreign);
  await page.waitForFunction(() => window.liveExplore.model.snapshot.regions.properties.phase === 'denied');
  assert.equal(await page.getByRole('table', { name: 'Observations under the pinned method' }).count(), 0);
  assert.equal(await page.getByRole('region', { name: 'Conversion history', exact: true }).count(), 0);
  evidence.scenarios.push('foreign experiment denied by actual owner and prior protected detail cleared');
  assert.equal((await fetch(host.url + '/api/knowledge/v1/graph-proposals', { method: 'POST', body: '{}' })).status, 403);
  assert.deepEqual(errors, []); assert.deepEqual(authorizations, []);
  const content = await page.content();
  for (const owner of Object.values(owners)) assert.equal(content.includes(owner.token), false);
  evidence.status = 'passed'; evidence.browser = browser.version(); evidence.requests = host.requests;
  await writeFile(resolve(output, 'evidence.json'), JSON.stringify(evidence, null, 2) + '\n');
  process.stdout.write(JSON.stringify(evidence));
} finally { if (browser) await browser.close(); await host.close(); }
