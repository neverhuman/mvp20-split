import assert from 'node:assert/strict';
import { mkdir, writeFile, readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import { startExploreHost } from './explore_host.mjs';

const output = resolve('../.test-results/studio-quality-browser', new Date().toISOString().replaceAll(/[:.]/g, '-'));
await mkdir(output, { recursive: true });
const host = await startExploreHost(), browser = await chromium.launch({ headless: true });
const evidence = { status: 'running', browser: browser.version(), scenarios: [],
  limits: ['Scripted public owner HTTP, not actual owner acceptance', 'No scientific calibration or screen-reader conformance claim'] };
let page;
try {
  host.state.mode = 'quality-mixed';
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
  page = await context.newPage();
  const errors = []; page.on('pageerror', error => errors.push(error.message));
  page.setDefaultTimeout(10000); await page.goto(host.url);
  await page.evaluate(() => { const h = window.exploreHarness;
    h.feedback.bind({ ...h.feedbackPins, publication: null, corrections: null, proposal: null }); });
  await page.getByRole('button', { name: 'Question & feedback', exact: true }).click();
  await page.getByRole('button', { name: 'Quality points', exact: true }).click();
  const region = page.getByRole('region', { name: 'Scientific quality points', exact: true });
  await region.waitFor(); assert.match(await region.textContent(), /20 of 32 matching points/);
  await region.getByRole('button', { name: /Independent synthetic criterion 1 / }).focus(); await page.keyboard.press('Enter');
  const detail = page.getByRole('complementary', { name: 'Selected quality point' });
  assert.match(await detail.textContent(), /Supporting and contradicting evidence remain in conflict/);
  assert.match(await detail.textContent(), /Calibrated accuracyNot provided/);
  assert.match(await detail.textContent(), /Demonstrated error verdictNot provided/);
  await detail.getByLabel('Intended improvement', { exact: true }).fill('Resolve the conflicting evidence using a new test.');
  await detail.getByLabel('What do you expect to learn?', { exact: true }).fill('Which observation applies to the next campaign context.');
  await detail.getByRole('button', { name: 'Save focus', exact: true }).click();
  assert.match(await region.textContent(), /1 points in local focus \/ 24 unresolved points retained/);
  const downloadEvent = page.waitForEvent('download');
  await region.getByRole('button', { name: 'Export next-campaign focus', exact: true }).click();
  const download = await downloadEvent;
  const exported = JSON.parse(await readFile(await download.path(), 'utf8'));
  assert.equal(exported.authority, 'unsubmitted_human_draft');
  assert.equal(exported.selected.length, 1); assert.equal(exported.unresolved.length, 24);
  assert.equal(exported.expected_information_gain.numerical_estimate, null);
  evidence.scenarios.push('human focus draft export preserves exact selected point and all24 unresolved points without owner mutation');
  await region.getByRole('combobox', { name: 'Show quality' }).selectOption('contradictory');
  assert.match(await region.textContent(), /8 of 8 matching points/);
  await region.getByRole('combobox', { name: 'Show quality' }).selectOption('unassessed');
  await region.getByText('No points match this filter.', { exact: true }).waitFor();
  await region.getByRole('combobox', { name: 'Show quality' }).selectOption('all');
  await region.getByRole('button', { name: 'Next points', exact: true }).click();
  assert.match(await region.textContent(), /12 of 32 matching points/);
  await region.getByRole('button', { name: 'Previous points', exact: true }).click();
  await region.getByRole('button', { name: /Independent synthetic criterion 1 / }).click();
  await page.getByRole('region', { name: 'Quality-marked execution point' }).waitFor();
  await page.getByText('Quality: 24 unresolved criteria', { exact: true }).waitFor();
  await region.getByRole('button', { name: 'Inspect linked execution point', exact: true }).click();
  await page.getByRole('region', { name: 'Pinned execution point' }).waitFor();
  assert.match(await page.getByRole('region', { name: 'Pinned execution point' }).textContent(), /succeeded/);
  await page.getByRole('button', { name: 'Return to quality points', exact: true }).click();
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: width === 1440 ? 1000 : 844 });
    const scan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    assert.deepEqual(scan.violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => n.target) })), []);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    assert.equal(await detail.evaluate(element => element.scrollHeight <= element.clientHeight), true, 'Quality inspector must not clip the graph link inside a nested sidebar scroll');
    await page.getByRole('region', { name: 'Quality-marked execution point' }).scrollIntoViewIfNeeded();
    await page.getByRole('region', { name: 'Quality-marked execution point' }).screenshot({ path: resolve(output, `quality-link-${width}.png`) });
    await page.screenshot({ path: resolve(output, `quality-${width}.png`), fullPage: true });
  }
  evidence.scenarios.push('32 mixed points, keyboard inspection, bounded pagination, filters/empty state, desktop/mobile accessibility');
  evidence.scenarios.push('exact Runtime output graph marker and pinned execution navigation coexist with24 unresolved criteria');
  host.state.mode = 'quality-link-denied'; await page.getByRole('button', { name: 'Refresh feedback', exact: true }).click();
  await page.getByText('The selected execution link is unavailable. Scientific assessment details remain separate.', { exact: true }).waitFor();
  assert.equal(await page.getByRole('region', { name: 'Quality-marked execution point' }).count(), 0);
  assert.match(await region.textContent(), /20 of 32 matching points/);
  evidence.scenarios.push('Runtime denial removes graph link while separately authorized scientific points remain');
  host.state.mode = 'feedback-denied'; await page.getByRole('button', { name: 'Refresh feedback', exact: true }).click();
  await page.getByText('Access denied. Evidence details have been cleared.', { exact: true }).waitFor();
  assert.equal(await region.count(), 0); evidence.scenarios.push('denial clears selected quality and evidence');
  assert.deepEqual(errors, []); evidence.status = 'passed';
} catch (error) {
  evidence.status = 'failed'; evidence.error = String(error);
  if (page) await page.screenshot({ path: resolve(output, 'failure.png'), fullPage: true });
  throw error;
} finally {
  await writeFile(resolve(output, 'evidence.json'), JSON.stringify(evidence, null, 2) + '\n');
  await browser.close(); host.server.closeAllConnections(); await new Promise(done => host.server.close(done));
  console.log(output);
}
