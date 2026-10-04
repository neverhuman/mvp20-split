import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import { startExploreHost } from './explore_host.mjs';

const output = resolve('../.test-results/studio-explore-browser', new Date().toISOString().replaceAll(/[:.]/g, '-'));
await mkdir(output, { recursive: true });
const host = await startExploreHost(), browser = await chromium.launch({ headless: true });
const evidence = { status: 'running', browser: browser.version(), scenarios: [], limits: ['Scripted public scientific HTTP; actual-owner model proof is separate', 'No scientific validity or screen-reader conformance claim'] };
let page;
const errors = [];
try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
  page = await context.newPage(); page.on('pageerror', error => errors.push(error.message));
  page.setDefaultTimeout(10000);
  await page.goto(host.url);
  const candidate = page.getByRole('button', { name: 'Candidate material', exact: true }).first();
  await candidate.focus(); await page.keyboard.press('Enter');
  await page.getByRole('region', { name: 'Domain graph neighborhood' }).waitFor();
  await page.getByRole('button', { name: 'Candidate material correlates with Target property', exact: true }).click();
  await page.getByText('The candidate material may correlate with the target property under the reported conditions.', { exact: true }).waitFor();
  await page.getByRole('button', { name: 'Read source passage 1', exact: true }).click();
  const source = page.getByRole('region', { name: 'Verified source passage', exact: true });
  await source.waitFor();
  assert.match(await source.textContent(), /<note>Source text is evidence/);
  assert.equal(await source.locator('note').count(), 0);
  await page.getByRole('button', { name: 'Inspect conversion 1', exact: true }).click();
  await page.getByRole('region', { name: 'Conversion history', exact: true }).waitFor();
  evidence.scenarios.push('keyboard concept -> bounded graph -> qualified claim -> verified inert source -> conversion');
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: width === 1440 ? 1000 : 844 });
    const scan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    assert.deepEqual(scan.violations.map(item => ({ id: item.id, nodes: item.nodes.map(node => node.target) })), []);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: resolve(output, `knowledge-${width}.png`), fullPage: true });
  }
  await page.getByRole('button', { name: 'Specimens', exact: true }).click();
  await page.getByRole('table', { name: 'Samples in the pinned experiment' }).waitFor();
  await page.getByRole('button', { name: 'Properties', exact: true }).click();
  await page.getByRole('table', { name: 'Observations under the pinned method' }).waitFor();
  await page.getByRole('button', { name: 'View measured series', exact: true }).click();
  await page.getByRole('region', { name: 'Measured series', exact: true }).waitFor();
  assert.equal(await page.getByRole('table', { name: 'Reported sequence' }).locator('tbody tr').count(), 2);
  assert.match(await page.getByRole('region', { name: 'Measured series', exact: true }).textContent(), /Missing: not_reported/);
  await page.getByRole('button', { name: 'Inspect result evidence', exact: true }).first().click();
  await page.getByRole('region', { name: 'Verified artifact', exact: true }).waitFor();
  evidence.scenarios.push('distinct specimen context -> lossless properties -> original repeated-coordinate series');
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: width === 1440 ? 1000 : 844 });
    const scan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    assert.deepEqual(scan.violations.map(item => ({ id: item.id, nodes: item.nodes.map(node => node.target) })), []);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: resolve(output, `properties-${width}.png`), fullPage: true });
  }
  await page.getByRole('button', { name: 'Question & feedback', exact: true }).click();
  await page.getByRole('region', { name: 'Selected research question', exact: true }).waitFor();
  await page.getByRole('button', { name: '02 Evidence need', exact: true }).focus(); await page.keyboard.press('Enter');
  await page.getByRole('region', { name: 'Predeclared evidence need', exact: true }).waitFor();
  await page.getByRole('button', { name: '03 Scoped answer', exact: true }).click();
  await page.getByRole('table', { name: 'Evidence need decisions' }).waitFor();
  assert.match(await page.getByRole('region', { name: 'Scoped evidence assessment' }).textContent(), /answer contradicted/);
  await page.getByRole('button', { name: '04 Next campaign', exact: true }).click();
  await page.getByRole('table', { name: 'Historical and corrected receipts' }).waitFor();
  assert.match(await page.getByRole('region', { name: 'Future campaign feedback' }).textContent(), /Current campaign pins and committed history stay unchanged/);
  await page.getByRole('button', { name: 'Read feedback source 1', exact: true }).click();
  await source.waitFor();
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: width === 1440 ? 1000 : 844 });
    const scan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    assert.deepEqual(scan.violations.map(item => ({ id: item.id, nodes: item.nodes.map(node => node.target) })), []);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: resolve(output, `feedback-${width}.png`), fullPage: true });
  }
  evidence.scenarios.push('keyboard question -> declared method -> qualified contradicted answer -> historical correction -> future proposal -> verified source');
  host.state.mode = 'feedback-denied'; await page.getByRole('button', { name: 'Refresh feedback', exact: true }).click();
  await page.getByText('Access denied. Evidence details have been cleared.', { exact: true }).waitFor();
  assert.equal(await page.getByRole('table', { name: 'Historical and corrected receipts' }).count(), 0);
  assert.equal(await source.count(), 0);
  evidence.scenarios.push('feedback denial clears qualified owner records');
  host.state.mode = 'feedback-pending';
  await page.evaluate(() => { const h = window.exploreHarness; h.feedback.bind({ ...h.feedbackPins, publication: null, corrections: null }); });
  await page.getByRole('button', { name: 'Refresh feedback', exact: true }).click();
  await page.getByRole('button', { name: '03 Scoped answer', exact: true }).click();
  await page.getByText('Assessment pending. No completed answer is being claimed.', { exact: true }).waitFor();
  evidence.scenarios.push('pending assessment remains inspectable without a publication');
  host.state.mode = 'feedback-long'; await page.getByRole('button', { name: 'Refresh feedback', exact: true }).click();
  await page.getByRole('table', { name: 'Evidence need decisions' }).waitFor();
  assert.equal(await page.getByRole('table', { name: 'Evidence need decisions' }).locator('tbody tr').count(), 20);
  await page.getByRole('button', { name: 'Next decisions', exact: true }).click();
  assert.equal(await page.getByRole('table', { name: 'Evidence need decisions' }).locator('tbody tr').count(), 12);
  await page.getByRole('button', { name: '01 Question', exact: true }).click();
  await page.getByText('A deliberately long research question about measurement context, processing history, confidence and independently repeatable evidence across prepared candidate materials', { exact: true }).waitFor();
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  await page.screenshot({ path: resolve(output, 'feedback-long-390.png'), fullPage: true });
  evidence.scenarios.push('long question and 32 need decisions remain bounded at 20 rows with explicit paging');

  host.state.mode = 'ready';
  await page.getByRole('button', { name: 'Knowledge graph', exact: true }).click();
  await candidate.click(); await page.getByRole('button', { name: 'Candidate material correlates with Target property', exact: true }).click();
  host.state.mode = 'denied'; await page.getByRole('button', { name: 'Read source passage 1', exact: true }).click();
  await page.waitForFunction(() => window.exploreHarness.model.snapshot.regions.source.phase === 'denied');
  assert.equal(await source.count(), 0); assert.equal(await page.getByText('The candidate material may correlate with the target property under the reported conditions.', { exact: true }).count(), 0);
  evidence.scenarios.push('current content denial clears every protected region');
  host.state.mode = 'ready'; await page.getByRole('button', { name: 'Refresh selected view', exact: true }).click();
  await candidate.click(); await page.getByRole('button', { name: 'Candidate material correlates with Target property', exact: true }).click();
  host.state.mode = 'corrupt'; await page.getByRole('button', { name: 'Read source passage 1', exact: true }).click();
  await page.waitForFunction(() => window.exploreHarness.model.snapshot.regions.source.phase === 'failed');
  assert.equal(await source.count(), 0);
  evidence.scenarios.push('altered source bytes never become a verified passage');
  for (const mode of ['empty', 'offline', 'paged', 'long']) {
    host.state.mode = mode; await page.getByRole('button', { name: 'Refresh selected view', exact: true }).click();
    await page.waitForFunction(() => window.exploreHarness.model.snapshot.regions.search.phase !== 'loading');
    const phase = await page.evaluate(() => window.exploreHarness.model.snapshot.regions.search.phase);
    assert.equal(phase, mode === 'empty' ? 'empty' : mode === 'offline' ? 'failed' : mode === 'paged' ? 'partial' : 'ready');
    if (mode === 'paged') { await page.getByRole('button', { name: 'Next concepts', exact: true }).click(); await page.getByText('10 of 30 matching concepts shown', { exact: true }).waitFor(); }
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    if (mode === 'long') await page.screenshot({ path: resolve(output, 'long-label-390.png'), fullPage: true });
    evidence.scenarios.push(mode + ' state remains explicit and bounded');
  }
  host.state.mode = 'ready';
  let enter, release;
  const entered = new Promise(done => { enter = done; });
  host.state.held = { enter, promise: new Promise(done => { release = done; }) };
  await page.getByRole('button', { name: 'Refresh selected view', exact: true }).click(); await entered;
  await page.getByRole('button', { name: 'Properties', exact: true }).click();
  await page.getByRole('table', { name: 'Observations under the pinned method' }).waitFor();
  release(); host.state.held = null;
  assert.equal(await page.evaluate(() => window.exploreHarness.model.snapshot.regions.search.phase), 'stale');
  assert.equal(await page.evaluate(() => window.exploreHarness.model.snapshot.regions.search.value), null);
  evidence.scenarios.push('hidden domain request cannot repopulate an inactive view');
  assert.equal(host.state.requests.some(request => request.ownerAuthorization), false);
  assert.deepEqual(errors, []); evidence.status = 'passed';
} catch (error) {
  evidence.status = 'failed'; evidence.error = String(error); evidence.page_errors = errors;
  if (page) { evidence.visible_text = (await page.locator('body').innerText()).slice(0, 1800); await page.screenshot({ path: resolve(output, 'failure.png'), fullPage: true }); }
  console.error(JSON.stringify({ page_errors: errors, visible_text: evidence.visible_text })); throw error;
}
finally {
  await writeFile(resolve(output, 'manifest.json'), JSON.stringify(evidence, null, 2));
  await browser.close(); host.server.closeAllConnections(); await new Promise(done => host.server.close(done));
  console.log(`Explore browser evidence: ${output}`);
}
