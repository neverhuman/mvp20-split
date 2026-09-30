import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { startObservationHost } from './host.mjs';
import { artifact, completion, evidenceDetail, values } from '../../dist/tests/fixtures/evidence.js';
import { id } from '../../dist/tests/fixtures/observations.js';

const output = resolve('../.test-results/studio-evidence', new Date().toISOString().replace(/[:.]/g, '-'));
await mkdir(output, { recursive: true });
const host = await startObservationHost();
let mode = 'ready', held = null;
host.state.hook = async (url, json) => {
  if (url.pathname.endsWith('/nodes/' + id(1))) { json(200, evidenceDetail()); return true; }
  if (url.pathname.includes('/completions/')) { json(200, completion()); return true; }
  if (url.pathname.endsWith('/outputs/result')) { json(mode === 'stale' ? 409 : 200, values()); return true; }
  if (url.pathname.startsWith('/api/artifacts/')) {
    if (held) { held.enter(); await held.promise; }
    json(mode === 'missing' ? 404 : mode === 'denied' ? 403 : 200,
      mode === 'conflict' ? { ...artifact(), sha256: id(999) } : artifact()); return true;
  }
  return false;
};
const browser = await chromium.launch({ headless: true });
const evidence = { status: 'running', browser: browser.version(), scenarios: [],
  limits: ['Scripted public Runtime/Artifact HTTP contracts; no actual-owner integration or scientific acceptance claim.'] };
try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
  const page = await context.newPage(), errors = []; page.on('pageerror', error => errors.push(error.message));
  await page.goto(host.url + '/?evidence=1');
  const choose = async index => { const button = page.locator(`button[data-node-id="${id(index)}"]`); await button.focus(); await page.keyboard.press('Enter'); };
  await choose(1);
  const inspectArtifact = page.getByRole('button', { name: 'Inspect artifact artifact-1', exact: true });
  await page.getByRole('button', { name: 'Inspect attempt attempt-1', exact: true }).click();
  await page.getByRole('region', { name: 'Retained completion', exact: true }).waitFor();
  await page.getByRole('button', { name: 'Inspect output result', exact: true }).click();
  await page.getByRole('region', { name: 'Output members', exact: true }).waitFor();
  await inspectArtifact.click(); await page.getByRole('region', { name: 'Verified artifact metadata', exact: true }).waitFor();
  assert.equal(host.state.requests.some(request => request.path.endsWith('/content')), false);
  evidence.scenarios.push('attempt to retained completion', 'output members to exact artifact metadata');
  for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
    await page.setViewportSize(viewport);
    const scan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    assert.deepEqual(scan.violations.map(item => ({ id: item.id, nodes: item.nodes.map(node => node.target) })), []);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: resolve(output, `evidence-${viewport.width}.png`), fullPage: true });
  }
  for (const failure of ['missing', 'conflict', 'denied']) {
    mode = failure; await inspectArtifact.click();
    await page.waitForFunction(() => ['failed', 'denied'].includes(window.observationHarness.evidence.snapshot.artifact.phase));
    assert.equal(await page.getByRole('region', { name: 'Verified artifact metadata', exact: true }).count(), 0);
    assert.equal(await page.evaluate(() => window.observationHarness.evidence.snapshot.artifact.error.kind),
      failure === 'missing' ? 'unavailable' : failure === 'conflict' ? 'invalid_response' : 'denied');
    evidence.scenarios.push(failure + ' artifact stays unverified');
  }
  mode = 'ready'; await choose(1);
  let release, enter;
  const entered = new Promise(resolve => { enter = resolve; });
  held = { promise: new Promise(resolve => { release = resolve; }), enter };
  await inspectArtifact.click(); await entered; await choose(2); release(); held = null;
  await page.waitForFunction(() => window.observationHarness.model.snapshot.detail?.node.path.node_id === 'node-2');
  assert.equal(await page.getByRole('region', { name: 'Verified artifact metadata', exact: true }).count(), 0);
  evidence.scenarios.push('late artifact cannot replace newer activation');
  await choose(1); mode = 'stale'; await page.getByRole('button', { name: 'Inspect output result', exact: true }).click();
  await page.waitForFunction(() => window.observationHarness.evidence.snapshot.values.phase === 'stale');
  assert.equal(await page.getByRole('button', { name: 'Inspect output result', exact: true }).isDisabled(), true);
  evidence.scenarios.push('stale output requires refreshed selection');
  assert.deepEqual(errors, []); evidence.status = 'passed';
} catch (error) { evidence.status = 'failed'; evidence.error = String(error); throw error; }
finally {
  await writeFile(resolve(output, 'manifest.json'), JSON.stringify(evidence, null, 2));
  await browser.close(); host.server.closeAllConnections(); await new Promise(resolve => host.server.close(resolve));
  console.log(`Evidence browser manifest: ${output}`);
}
