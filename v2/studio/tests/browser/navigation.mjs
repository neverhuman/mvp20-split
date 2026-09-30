import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { startObservationHost } from './host.mjs';
import { scopes, topology } from '../../dist/tests/fixtures/navigation.js';

const output = resolve('../.test-results/studio-navigation', new Date().toISOString().replace(/[:.]/g, '-'));
await mkdir(output, { recursive: true });
const host = await startObservationHost();
let failure = null;
host.state.hook = async (url, json) => {
  if (!url.pathname.includes('/scopes')) return false;
  if (failure) { json(failure, { detail: 'private diagnostics' }); return true; }
  if (url.pathname.endsWith('/topology')) {
    const page = topology();
    if (!url.searchParams.has('cursor')) json(200, { ...page, nodes: page.nodes.slice(0, 1), next_cursor: 'next' });
    else json(200, { ...page, nodes: page.nodes.slice(1), edges: [] });
  } else json(200, scopes());
  return true;
};
const browser = await chromium.launch({ headless: true });
const evidence = { status: 'running', browser: browser.version(), scenarios: [],
  limits: ['Scripted public HTTP contracts; not actual Runtime integration or scientific acceptance.'] };
try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
  const page = await context.newPage();
  const errors = []; page.on('pageerror', error => errors.push(error.message));
  await page.goto(host.url + '/?navigation=1');
  await page.getByRole('button', { name: 'Authored graph', exact: true }).click();
  const root = page.getByRole('button', { name: 'Root graph active · 2 nodes', exact: true });
  await root.focus(); await page.keyboard.press('Enter');
  await page.waitForFunction(() => window.observationHarness.navigation.snapshot.topology?.unresolvedEdges === 1);
  assert.equal(await page.locator('.react-flow__edge').count(), 0);
  await page.getByRole('button', { name: 'Load topology page', exact: true }).click();
  await page.waitForFunction(() => window.observationHarness.navigation.snapshot.topology?.visibleEdges.length === 1);
  assert.equal(await page.locator('.react-flow__edge').count(), 1);
  const selected = page.getByRole('list', { name: 'Topology nodes', exact: true }).getByRole('button', { name: 'node-2 issued', exact: true });
  await selected.focus(); await page.keyboard.press('Enter');
  await page.getByRole('region', { name: 'Selected node', exact: true }).getByRole('heading', { name: 'node-2', exact: true }).waitFor();
  evidence.scenarios.push('partial target omission', 'authored edge after pagination', 'keyboard node-to-detail selection');
  for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
    await page.setViewportSize(viewport);
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    const scan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    assert.deepEqual(scan.violations.map(item => ({ id: item.id, nodes: item.nodes.map(node => node.target) })), []);
    await page.screenshot({ path: resolve(output, `navigation-${viewport.width}.png`), fullPage: true });
  }
  failure = 409;
  await page.getByRole('button', { name: 'Neighborhood of node-2', exact: true }).click();
  await page.waitForFunction(() => window.observationHarness.navigation.snapshot.phase === 'stale');
  assert.equal(await page.locator('.react-flow__node').count(), 0);
  evidence.scenarios.push('stale topology cleared');
  failure = null;
  await page.getByRole('button', { name: 'Refresh observation', exact: true }).click();
  await root.waitFor(); failure = 403; await root.click();
  await page.waitForFunction(() => window.observationHarness.navigation.snapshot.phase === 'denied');
  assert.equal(await page.getByRole('list', { name: 'Occurrence groups', exact: true }).getByRole('button').count(), 0);
  assert.equal((await page.locator('body').textContent()).includes('private diagnostics'), false);
  evidence.scenarios.push('denied navigation clears both regions');
  assert.deepEqual(errors, []); evidence.status = 'passed';
} catch (error) { evidence.status = 'failed'; evidence.error = String(error); throw error; }
finally {
  await writeFile(resolve(output, 'manifest.json'), JSON.stringify(evidence, null, 2));
  await browser.close(); host.server.closeAllConnections(); await new Promise(resolve => host.server.close(resolve));
  console.log(`Navigation browser evidence: ${output}`);
}
