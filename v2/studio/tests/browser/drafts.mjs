import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { startDraftHost } from './draft_host.mjs';
import { revision } from '../../dist/tests/fixtures/authoring.js';

const output = resolve('../.test-results/studio-drafts', new Date().toISOString().replace(/[:.]/g, '-'));
await mkdir(output, { recursive: true });
const host = await startDraftHost(), browser = await chromium.launch({ headless: true });
const evidence = { verified_at: new Intl.DateTimeFormat('sv-SE', { timeZone: 'America/Chicago', dateStyle: 'short', timeStyle: 'medium' }).format(new Date()),
  timezone: 'America/Chicago', status: 'running', scenarios: [], screenshots: [], limits: ['Scripted public HTTP peer; validation replies are fixtures, not actual Runtime compilation or authority.', 'No deployed gateway, scientific or target-host acceptance.'] };
let releaseSave;
try {
  for (const name of ['compose', 'compose-narrow', 'dense', 'lost-ack', 'conflict', 'pending-edit', 'save-denied', 'catalog-denied']) {
    Object.assign(host.state, { mode: 'ready', head: revision(), records: new Map([[1, revision()]]), receipts: new Map(), validations: new Map(), requests: [], saveGate: null });
    if (name === 'dense') {
      host.state.head.definition.body.nodes = Array.from({ length: 256 }, (_, index) => ({ kind: 'finish', node_id: `node-${index}-${'long-label-'.repeat(8)}`, outputs: [] }));
      host.state.records.set(1, structuredClone(host.state.head));
    }
    const composing = name.startsWith('compose');
    const context = await browser.newContext({ viewport: name === 'compose-narrow' ? { width: 390, height: 844 } : { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
    const page = await context.newPage(), errors = []; page.on('pageerror', error => errors.push(error.message));
    await page.goto(host.url);
    await page.waitForFunction(() => window.draftHarness?.catalog.snapshot.phase === 'ready');
    if (composing) {
      await page.getByLabel('New node ID', { exact: true }).fill('calculate');
      await page.getByLabel('Reviewed tool', { exact: true }).selectOption(host.descriptor);
      await page.getByRole('button', { name: 'Add tool', exact: true }).focus(); await page.keyboard.press('Enter');
      await page.getByRole('button', { name: 'Create parameter node for parameters', exact: true }).click();
      await page.getByRole('button', { name: 'Load parameter fields', exact: true }).click();
      const gain = page.getByLabel('gain (required)', { exact: true }); await gain.fill('1.25');
      await page.getByRole('button', { name: 'Apply gain', exact: true }).click();
      await gain.fill('1e-9999'); await page.getByRole('button', { name: 'Apply gain', exact: true }).click();
      await page.getByRole('alert').getByText(/too small/).waitFor(); assert.equal(await gain.inputValue(), '1e-9999');
      assert.equal(await page.evaluate(() => window.draftHarness.commands.session.snapshot.local.definition.body.nodes.find(node => node.node_id === 'parameters').fields[0].source.value), 1.25);
      await gain.fill('1.5'); await page.getByRole('button', { name: 'Apply gain', exact: true }).click();
      await page.getByRole('button', { name: 'Compare with saved revision', exact: true }).click();
      await page.getByRole('region', { name: 'Draft comparison', exact: true }).getByText(/do not establish scientific/).waitFor();
      const filename = `${name}-comparison.png`; await page.screenshot({ path: resolve(output, filename), fullPage: true }); evidence.screenshots.push(filename);
      await page.getByRole('button', { name: 'Compare with saved revision', exact: true }).click();
    } else await page.getByLabel('Draft title', { exact: true }).fill('Local work to retain');
    if (name === 'dense') {
      assert.equal(await page.locator('.react-flow__node').count(), 200);
      assert.equal(await page.getByRole('navigation', { name: 'Draft nodes', exact: true }).getByRole('button').count(), 256);
      await page.getByRole('navigation', { name: 'Draft nodes', exact: true }).getByRole('button').last().click();
      await page.getByRole('region', { name: 'Draft node inspector', exact: true }).getByRole('heading', { name: host.state.head.definition.body.nodes[255].node_id, exact: true }).waitFor();
      assert.equal(await page.locator('.react-flow__node').count(), 56);
      assert.equal(await page.getByRole('navigation', { name: 'Draft nodes', exact: true }).getByRole('button').last().evaluate(button => button.scrollHeight <= button.clientHeight), true);
    }
    host.state.mode = composing || name === 'pending-edit' || name === 'dense' ? 'ready' : name;
    if (name === 'catalog-denied') {
      await page.getByRole('button', { name: 'Refresh tool library', exact: true }).click();
      await page.waitForFunction(() => window.draftHarness.commands.session.snapshot.denied);
    } else {
      if (name === 'pending-edit') host.state.saveGate = new Promise(resolve => { releaseSave = resolve; });
      await page.getByRole('button', { name: 'Save draft', exact: true }).click();
      if (name === 'pending-edit') {
        await page.waitForFunction(() => window.draftHarness.commands.snapshot.phase === 'submitting');
        await page.getByLabel('Draft title', { exact: true }).fill('Newer local edit'); releaseSave();
      }
      const phase = name === 'lost-ack' ? 'unresolved' : name === 'save-denied' ? 'denied' : 'settled';
      await page.waitForFunction(phase => window.draftHarness.commands.snapshot.phase === phase, phase);
      if (name === 'lost-ack') {
        await page.getByRole('button', { name: 'Check original receipt', exact: true }).click();
        await page.waitForFunction(() => window.draftHarness.commands.snapshot.phase === 'settled');
      }
      if (composing) {
        await page.getByRole('button', { name: 'Validate saved revision', exact: true }).click();
        await page.waitForFunction(() => window.draftHarness.commands.session.snapshot.validationMatchesDraft);
      }
    }
    if (!composing) assert.equal(await page.getByLabel('Draft title', { exact: true }).inputValue(), name === 'pending-edit' ? 'Newer local edit' : 'Local work to retain');
    if (name === 'pending-edit' || name === 'conflict') assert.equal(await page.evaluate(() => window.draftHarness.commands.session.snapshot.dirty), true);
    if (name.endsWith('denied')) {
      assert.equal(await page.getByRole('button', { name: 'Save draft', exact: true }).isDisabled(), true);
      assert.equal(await page.getByLabel('Reviewed tool', { exact: true }).locator('option').count(), 1);
    }
    assert.equal(host.state.requests.filter(request => request.method === 'POST' && request.path.endsWith('/save')).length, name === 'catalog-denied' ? 0 : 1);
    assert.equal((await page.locator('body').textContent()).includes('private diagnostics'), false);
    for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
      await page.setViewportSize(viewport);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      const scan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
      assert.deepEqual(scan.violations.map(item => ({ id: item.id, targets: item.nodes.map(node => node.target) })), []);
      const filename = `${name}-${viewport.width}.png`; await page.screenshot({ path: resolve(output, filename), fullPage: true }); evidence.screenshots.push(filename);
    }
    assert.deepEqual(errors, []); evidence.scenarios.push({ name, status: 'passed', requests: host.state.requests }); await context.close();
  }
  evidence.status = 'passed';
} catch (error) { evidence.status = 'failed'; evidence.error = String(error); process.exitCode = 1; }
finally {
  releaseSave?.(); await writeFile(resolve(output, 'manifest.json'), JSON.stringify(evidence, null, 2));
  console.log(JSON.stringify({ status: evidence.status, output, error: evidence.error }));
  await browser.close(); await new Promise(resolve => host.server.close(resolve));
}
