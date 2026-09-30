import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { startSpike } from '../server.mjs';

const output = resolve('../.test-results/studio-interaction', new Date().toISOString().replace(/[:.]/g, '-'));
await mkdir(output, { recursive: true });
const fixture = await startSpike();
const browser = await chromium.launch({ headless: true });
const evidence = { verified_at: new Intl.DateTimeFormat('sv-SE', { timeZone: 'America/Chicago', dateStyle: 'short', timeStyle: 'medium' }).format(new Date()), timezone: 'America/Chicago', status: 'running', browser: browser.version(), platform: process.platform,
  dataset: { logical: 10000, window: 200, synthetic: true }, candidates: [], limits: ['Local headless Chromium only; not DGX/Threadripper or scientific evidence.', 'Fixture transport, not live Runtime.', 'Automated accessibility and keyboard proof does not replace screen-reader user evaluation.'] };
try {
  for (const renderer of ['reactflow', 'cytoscape']) {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    const errors = []; page.on('pageerror', error => errors.push(error.message));
    const result = { renderer, mounts_ms: [], updates_ms: [], scenarios: [], screenshots: [], axe: [] };
    const settled = async () => {
      await page.waitForFunction(() => window.spike?.ready);
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    };
    for (let i = 0; i < 5; i++) {
      const start = performance.now(); await page.goto(`${fixture.url}/?renderer=${renderer}`); await settled();
      result.mounts_ms.push(Math.round((performance.now() - start) * 100) / 100);
    }
    assert.equal(await page.locator('.node-list button').count(), 200);
    assert.equal(await page.evaluate(() => window.spike.scene.omitted), 9800);
    if (renderer === 'reactflow') {
      assert.equal(await page.locator('.react-flow__node').count(), 200);
      const long = await page.locator('.react-flow__node[data-id="n37"]').boundingBox();
      const following = await page.locator('.react-flow__node[data-id="n42"]').boundingBox();
      assert.ok(long.y + long.height < following.y, 'long labels must not overlap the next row');
      await page.locator('.react-flow__node').nth(1).focus(); await page.keyboard.press('Enter');
      await page.waitForFunction(() => window.spike.scene.selected?.id === 'n1');
      result.scenarios.push('Native graph node keyboard selection reaches shared inspector');
    }
    result.scenarios.push('200 scene records / 9800 omitted; bounded HTTP source');
    const first = page.locator('.node-list button').first(); await first.focus(); await page.keyboard.press('Enter');
    assert.equal(await page.evaluate(() => window.spike.scene.selected?.id), 'n0');
    await page.getByRole('button', { name: 'Pan right', exact: true }).focus(); await page.keyboard.press('Enter');
    const viewport = await page.evaluate(() => ({ ...window.spike.scene.viewport }));
    for (let i = 0; i < 5; i++) {
      const prior = await page.evaluate(() => window.spike.revision);
      const start = performance.now(); await page.getByRole('button', { name: 'Next 200', exact: true }).click();
      await page.waitForFunction(prior => window.spike.ready && window.spike.revision > prior, prior); await settled();
      result.updates_ms.push(Math.round((performance.now() - start) * 100) / 100);
    }
    assert.equal(await page.evaluate(() => window.spike.scene.selected?.id), 'n0');
    assert.equal(await page.evaluate(() => window.spike.scene.selectionOutsideWindow), true);
    assert.deepEqual(await page.evaluate(() => ({ ...window.spike.scene.viewport })), viewport);
    result.scenarios.push('Keyboard selection/panning; selection and viewport preserved over five page updates');
    await page.getByLabel('Find a node', { exact: true }).fill('09999');
    await page.getByLabel('Find a node', { exact: true }).press('Enter'); await page.waitForFunction(() => window.spike.scene.total === 1); await settled();
    await page.locator('.node-list button').first().focus(); await page.keyboard.press('Enter');
    assert.equal(await page.evaluate(() => window.spike.scene.selected?.id), 'n9998');
    await page.getByRole('button', { name: 'Show selected node', exact: true }).focus(); await page.keyboard.press('Enter');
    assert.ok(await page.evaluate(() => window.spike.scene.viewport.y < -100000));
    result.scenarios.push('Server-side search reaches node 9999 through keyboard list without downloading all nodes');
    await page.getByLabel('Find a node', { exact: true }).fill('no such synthetic node');
    await page.getByLabel('Find a node', { exact: true }).press('Enter'); await page.waitForFunction(() => window.spike.scene.total === 0); await settled();
    assert.equal(await page.getByRole('heading', { name: 'No matching nodes' }).count(), 1);
    assert.equal(await page.evaluate(() => window.spike.scene.selected?.id), 'n9998');
    result.scenarios.push('Empty search explicitly labeled; selection retained outside window');
    await page.getByRole('button', { name: 'Reset', exact: true }).click(); await page.waitForFunction(() => window.spike.scene.total === 10000); await settled();
    await page.locator('.node-list button').first().click();
    await page.getByRole('button', { name: 'Show window', exact: true }).click();
    for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
      await page.setViewportSize(viewport); await settled();
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, 'page must not overflow horizontally');
      const scan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
      result.axe.push({ viewport, violations: scan.violations.map(v => ({ id: v.id, impact: v.impact, nodes: v.nodes.map(n => n.target) })) });
      const path = resolve(output, `${renderer}-${viewport.width}.png`); await page.screenshot({ path, fullPage: true }); result.screenshots.push(path);
    }
    await page.getByLabel('Find a node', { exact: true }).fill('00038');
    await page.getByLabel('Find a node', { exact: true }).press('Enter'); await page.waitForFunction(() => window.spike.scene.total === 1); await settled();
    await page.locator('.node-list button').first().click();
    await page.getByRole('button', { name: 'Show selected node', exact: true }).click();
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: resolve(output, `${renderer}-long-label.png`), fullPage: true });
    result.scenarios.push('Long label remains readable in narrow inspector/list without document overflow');
    let release;
    const held = new Promise(resolve => { release = resolve; });
    await page.route('**/fixture/scene?**', async route => { await held; await route.continue(); });
    await page.getByRole('button', { name: 'Reset', exact: true }).click();
    await page.getByRole('status').filter({ hasText: 'Loading graph' }).waitFor();
    await page.screenshot({ path: resolve(output, `${renderer}-loading.png`), fullPage: true });
    release(); await page.waitForFunction(() => window.spike.scene.total === 10000); await settled();
    await page.unroute('**/fixture/scene?**');
    await page.route('**/fixture/scene?**', route => route.fulfill({ status: 503, body: 'unavailable' }));
    await page.getByRole('button', { name: 'Search', exact: true }).click();
    await page.getByRole('status').filter({ hasText: 'Graph unavailable' }).waitFor();
    await page.screenshot({ path: resolve(output, `${renderer}-unavailable.png`), fullPage: true });
    await page.unroute('**/fixture/scene?**');
    result.scenarios.push('Loading and unavailable states rendered explicitly; retained scene is not labeled fresh');
    assert.deepEqual(errors, []);
    evidence.candidates.push(result); await context.close();
  }
  evidence.requests = fixture.counts;
  assert.equal(fixture.counts.maxNodes, 200);
  evidence.status = evidence.candidates.some(c => c.axe.some(a => a.violations.length)) ? 'accessibility_findings' : 'passed';
  await writeFile(resolve(output, 'manifest.json'), JSON.stringify(evidence, null, 2));
  console.log(JSON.stringify({ status: evidence.status, manifest: resolve(output, 'manifest.json'), candidates: evidence.candidates.map(c => ({ renderer: c.renderer, mounts_ms: c.mounts_ms, updates_ms: c.updates_ms, axe: c.axe })) }, null, 2));
  if (evidence.status !== 'passed') process.exitCode = 1;
} catch (error) {
  evidence.status = 'failed'; evidence.error = String(error);
  await writeFile(resolve(output, 'manifest.json'), JSON.stringify(evidence, null, 2)); throw error;
} finally { await browser.close(); await new Promise(resolve => fixture.server.close(resolve)); }
