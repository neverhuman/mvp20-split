import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { startObservationHost } from './host.mjs';
import { scopes, topology, catalog, lineage } from '../../dist/tests/fixtures/navigation.js';
import { snapshot } from '../../dist/tests/fixtures/observations.js';

const output = resolve('../.test-results/studio-navigation', new Date().toISOString().replace(/[:.]/g, '-'));
await mkdir(output, { recursive: true });
const host = await startObservationHost();
let failure = null;
host.state.hook = async (url, json) => {
  const cut = snapshot({ revision: host.state.revision }).snapshot.cut;
  if (url.pathname.endsWith('/views')) { json(200, { ...catalog(), cut }); return true; }
  if (url.pathname.endsWith('/lineage')) { json(200, lineage()); return true; }
  if (!url.pathname.includes('/scopes')) return false;
  if (failure) { json(failure, { detail: 'private diagnostics' }); return true; }
  if (url.pathname.endsWith('/topology')) {
    const page = topology();
    page.cut = cut;
    page.query = { focus_activation_id: url.searchParams.get('focus_activation_id'), radius: Number(url.searchParams.get('radius') ?? 1) };
    if (!url.searchParams.has('cursor')) json(200, { ...page, nodes: page.nodes.slice(0, 1), next_cursor: 'next' });
    else json(200, { ...page, nodes: page.nodes.slice(1), edges: [] });
  } else json(200, { ...scopes(), cut });
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
  await page.waitForFunction(() => document.querySelectorAll('.react-flow__edge').length === 1);
  assert.equal(await page.locator('.react-flow__edge').count(), 1);
  const selected = page.getByRole('list', { name: 'Topology nodes', exact: true }).getByRole('button', { name: 'node-2 issued', exact: true });
  await selected.focus(); await page.keyboard.press('Enter');
  await page.getByRole('region', { name: 'Selected node', exact: true }).getByRole('heading', { name: 'node-2', exact: true }).waitFor();
  evidence.scenarios.push('partial target omission', 'authored edge after pagination', 'keyboard node-to-detail selection');
  await page.getByText('Named research views', { exact: true }).click();
  await page.getByRole('button', { name: 'Inspect predecessor lineage', exact: true }).click();
  await page.getByRole('region', { name: 'Retained predecessor lineage', exact: true }).waitFor();
  await page.getByText('Property history — owned by Research; not supplied by this execution view.', { exact: true }).waitFor();
  evidence.scenarios.push('named lineage uses public owner route', 'scientific projection ownership is explicit');
  for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
    await page.setViewportSize(viewport);
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    const scan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    assert.deepEqual(scan.violations.map(item => ({ id: item.id, nodes: item.nodes.map(node => node.target) })), []);
    await page.screenshot({ path: resolve(output, `navigation-${viewport.width}.png`), fullPage: true });
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  const beforePan = await page.evaluate(() => window.observationHarness.navigation.snapshot.viewport.x);
  await page.getByRole('button', { name: 'Pan right', exact: true }).click();
  await page.waitForFunction(x => window.observationHarness.navigation.snapshot.viewport.x === x - 100, beforePan);
  const viewport = await page.evaluate(() => window.observationHarness.navigation.snapshot.viewport);
  await page.getByRole('button', { name: 'Activation inventory', exact: true }).click();
  const navigationReads = () => host.state.requests.filter(item => /scopes|views/.test(item.path)).length;
  const beforeHidden = navigationReads(); host.state.revision = 2;
  await page.getByRole('button', { name: 'Refresh observation', exact: true }).click();
  await page.waitForFunction(() => window.observationHarness.model.snapshot.window?.snapshot.cut.revision === 2 && window.observationHarness.model.snapshot.detailPhase === 'ready');
  assert.equal(navigationReads(), beforeHidden);
  await page.getByRole('button', { name: 'Authored graph', exact: true }).click();
  await page.waitForFunction(() => window.observationHarness.navigation.snapshot.topology?.page.cut.revision === 2);
  assert.deepEqual(await page.evaluate(() => window.observationHarness.navigation.snapshot.viewport), viewport);
  assert.equal(await page.evaluate(() => window.observationHarness.model.snapshot.detail.node.path.node_id), 'node-2');
  evidence.scenarios.push('hidden pane performs no reads; reopening restores occurrence, selection and viewport at new cut');
  await page.getByRole('button', { name: 'Pin loaded inspection', exact: true }).click();
  const pinned = page.getByRole('region', { name: 'Pinned inspection', exact: true }); await pinned.waitFor();
  host.state.revision = 3;
  await page.getByRole('button', { name: 'Refresh observation', exact: true }).click();
  await page.waitForFunction(() => window.observationHarness.model.snapshot.window?.snapshot.cut.revision === 3);
  assert.match(await pinned.textContent(), /Historical pin · revision 2/);
  assert.match(await pinned.textContent(), /1 outside this capture/);
  for (const size of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
    await page.setViewportSize(size);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    assert.deepEqual((await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()).violations.map(item => item.id), []);
    await page.screenshot({ path: resolve(output, `history-${size.width}.png`), fullPage: true });
  }
  evidence.scenarios.push('bounded historical capture stays at revision 2 while live advances to 3');
  await page.getByRole('button', { name: 'Remove pin', exact: true }).click();
  await page.waitForFunction(() => window.observationHarness.navigation.snapshot.topology?.page.cut.revision === 3);
  await page.evaluate(() => { Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'hidden' }); document.dispatchEvent(new Event('visibilitychange')); });
  await page.waitForFunction(() => window.observationHarness.model.snapshot.phase === 'stale');
  const hiddenReads = host.state.requests.length; host.state.revision = 4;
  assert.equal(host.state.requests.length, hiddenReads);
  await page.evaluate(() => { Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'visible' }); document.dispatchEvent(new Event('visibilitychange')); });
  await page.waitForFunction(() => window.observationHarness.navigation.snapshot.topology?.page.cut.revision === 4);
  evidence.scenarios.push('controlled visibility event restores fresh cut; no real browser throttling claim');
  await page.getByRole('button', { name: 'Load topology page', exact: true }).click();
  await page.waitForFunction(() => window.observationHarness.navigation.snapshot.topology?.visibleEdges.length === 1);
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
