import { createServer } from 'node:http';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';
import { build } from 'esbuild';
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import { setTimeout as delay } from 'node:timers/promises';

let input = ''; for await (const chunk of process.stdin) input += chunk;
const job = JSON.parse(input), token = process.env.STUDIO_AUTHOR_TOKEN, registryToken = process.env.STUDIO_REGISTRY_TOKEN;
assert.ok(token && registryToken); delete process.env.STUDIO_AUTHOR_TOKEN; delete process.env.STUDIO_REGISTRY_TOKEN;
for (const endpoint of [job.endpoint, job.registry_endpoint]) assert.equal(new URL(endpoint).hostname, '127.0.0.1');
await mkdir(job.output, { recursive: true });
await build({ entryPoints: ['tests/integration/authoring_entry.tsx'], bundle: true, outdir: 'dist/authoring-integration', format: 'esm', jsx: 'automatic' });
const submitted = [], received = [];
const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url, 'http://localhost'), path = url.pathname;
    const registry = path === '/api/registry/v1/releases';
    const runtime = path.startsWith('/api/runtime/v1/') && (job.mode.startsWith('cancel')
      ? [ `/api/runtime/v1/graph-observations/${encodeURIComponent(job.run)}/nodes`, `/api/runtime/v1/graph-observations/${encodeURIComponent(job.run)}/invalidations`, '/api/runtime/v1/runs/cancel'].includes(path) || path.startsWith('/api/runtime/v1/commands/runtime.cancel/')
      : path === `/api/runtime/v1/definition-drafts/${encodeURIComponent(job.draft)}` ||
        ['/api/runtime/v1/definition-drafts/save', '/api/runtime/v1/definition-drafts/validate', '/api/runtime/v1/definition-universe', '/api/runtime/v1/graph-runs/drafts'].includes(path) ||
        ['/api/runtime/v1/definition-schemas/', '/api/runtime/v1/definition-validations/', '/api/runtime/v1/definition-commands/definition.save/', '/api/runtime/v1/definition-commands/definition.validate/', '/api/runtime/v1/commands/graph.admit_draft/'].some(prefix => path.startsWith(prefix)));
    if (registry || runtime) {
      const permittedPost = job.mode.startsWith('cancel') ? path.endsWith('/runs/cancel') : (['edit', 'writers', 'pending-crash'].includes(job.mode) && ['/definition-drafts/save', '/definition-drafts/validate'].some(suffix => path.endsWith(suffix))) || (job.mode.startsWith('activate') && ['/definition-drafts/validate', '/graph-runs/drafts'].some(suffix => path.endsWith(suffix)));
      if (req.method !== 'GET' && !(req.method === 'POST' && permittedPost)) { res.writeHead(405); res.end(); return; }
      const chunks = []; let size = 0;
      for await (const chunk of req) { size += chunk.length; assert.ok(size <= 262144); chunks.push(chunk); }
      const body = req.method === 'POST' ? Buffer.concat(chunks) : undefined;
      if (body) submitted.push(JSON.parse(body.toString('utf-8')));
      if (body && job.barrier && path.endsWith('/runs/cancel')) {
        // Controller-only files hold the real request before forwarding; never exposed to Chromium.
        await writeFile(job.barrier.marker, body);
        const deadline = Date.now() + 20000;
        while (true) {
          try { await readFile(job.barrier.release); break; } catch (error) { if (error.code !== 'ENOENT') throw error; }
          assert.ok(Date.now() < deadline, 'Cancellation barrier not released'); await delay(20);
        }
      }
      const response = await fetch((registry ? job.registry_endpoint : job.endpoint) + path.slice(registry ? '/api/registry'.length : '/api/runtime'.length) + url.search, {
        method: req.method, ...(body ? { body } : {}), headers: { Authorization: 'Bearer ' + (registry ? registryToken : token), Accept: 'application/json', 'Content-Type': 'application/json' },
        redirect: 'error', signal: AbortSignal.timeout(15000) });
      const output = []; size = 0; for await (const chunk of response.body) { size += chunk.length; assert.ok(size <= 2097152); output.push(chunk); }
      const bytes = Buffer.concat(output);
      if (body && response.status === 200) received.push(JSON.parse(bytes.toString('utf-8')));
      res.writeHead(response.status, { 'content-type': 'application/json', 'cache-control': 'no-store' }); res.end(bytes); return;
    }
    if (path === '/' && req.method === 'GET') {
      const context = JSON.stringify({ scope: job.scope, actor: job.actor, draft: job.draft, run: job.run, mode: job.mode }).replaceAll('<', '\\u003c');
      res.setHeader('content-type', 'text/html'); res.end(`<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Amphora owner authoring</title><link rel="stylesheet" href="/authoring_entry.css"></head><body><div id="root"></div><script id="authoring-context" type="application/json">${context}</script><script type="module" src="/authoring_entry.js"></script></body></html>`); return;
    }
    if (!['/authoring_entry.js', '/authoring_entry.css'].includes(path) || req.method !== 'GET') { res.writeHead(404); res.end(); return; }
    res.setHeader('content-type', path.endsWith('.css') ? 'text/css' : 'text/javascript'); res.end(await readFile(resolve('dist/authoring-integration', path.slice(1))));
  } catch { if (!res.headersSent) res.writeHead(502); res.end('Owner unavailable'); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const browser = await chromium.launch({ headless: true });
let page;
const errors = [];
try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
  page = await context.newPage(); const headers = [];
  page.on('pageerror', error => errors.push(error.message)); page.on('request', request => headers.push(request.allHeaders()));
  await page.goto(`http://127.0.0.1:${server.address().port}`);
  let result;
  if (job.mode.startsWith('cancel')) {
    await page.waitForFunction(() => window.authoringIntegration?.emergency?.snapshot.revision !== null && window.authoringIntegration?.emergency?.snapshot.status === 'running');
    await page.getByRole('link', { name: 'Emergency control', exact: true }).click();
    await page.getByRole('button', { name: 'Request emergency stop', exact: true }).click();
    await page.waitForFunction(expected => window.authoringIntegration.emergency.snapshot.phase === expected, job.expected_reason ? 'rejected' : 'accepted');
    const emergency = page.getByRole('region', { name: 'Emergency control', exact: true });
    if (job.expected_reason) await emergency.getByRole('status').filter({ hasText: job.expected_reason }).waitFor();
    else await emergency.getByRole('status').filter({ hasText: 'In-flight external effects may remain uncertain' }).waitFor();
    assert.equal(await page.evaluate(() => document.activeElement?.getAttribute('role')), 'status');
    await page.getByRole('button', { name: 'Refresh observation', exact: true }).click();
    const observed = job.expected_reason ? 'running' : 'cancelled';
    await page.waitForFunction(({ status, revision }) => {
      const snapshot = window.authoringIntegration.monitor.snapshot.window?.snapshot;
      return snapshot?.status === status && snapshot.cut.revision > revision;
    }, { status: observed, revision: submitted[0].payload.expected_run_revision });
    assert.equal(submitted.length, 1); assert.equal(received[0].outcome.status, job.expected_reason ? 'rejected' : 'accepted');
    if (job.expected_reason) assert.equal(received[0].outcome.reason_code, job.expected_reason);
    result = { receipt: received[0], submission: submitted[0], observed_status: observed };
  } else {
    await page.waitForFunction(() => window.authoringIntegration?.catalog?.snapshot.phase === 'ready');
    if (job.mode === 'edit') {
      await page.getByRole('navigation', { name: 'Draft nodes', exact: true }).getByRole('button', { name: 'seed · invoke', exact: true }).click();
      await page.getByRole('button', { name: 'Inspect parameters schema', exact: true }).click();
      await page.waitForFunction(() => window.authoringIntegration.catalog.snapshot.schemaPhase === 'ready');
      const schemaReference = await page.evaluate(() => window.authoringIntegration.catalog.snapshot.schema.reference);
      const body = await page.evaluate(() => window.authoringIntegration.commands.session.snapshot.local.definition.body);
      body.outputs.push({ name: 'browser_literal', value_type: { kind: 'scalar', scalar: 'number', unit: '1' } });
      body.nodes.find(node => node.kind === 'finish').outputs.push({ port: 'browser_literal', source: { kind: 'number', value: 1.25, unit: '1' } });
      await page.getByText('Advanced scope definition', { exact: true }).click();
      await page.getByLabel('Scope JSON', { exact: true }).fill(JSON.stringify(body));
      await page.getByRole('button', { name: 'Apply scope definition', exact: true }).click();
      await page.getByRole('button', { name: 'Save draft', exact: true }).click();
      await page.waitForFunction(() => window.authoringIntegration.commands.snapshot.phase === 'settled');
      assert.equal(received[0].outcome.status, 'accepted');
      await page.getByRole('button', { name: 'Validate saved revision', exact: true }).click();
      await page.waitForFunction(() => window.authoringIntegration.commands.session.snapshot.validationMatchesDraft);
      result = await page.evaluate(() => { const state = window.authoringIntegration.commands.session.snapshot; return { record: state.base, validation: state.validation }; });
      assert.equal(result.validation.structurally_valid, true, JSON.stringify(result.validation.findings));
      assert.equal(submitted[0].encoding, 'amphora-command-v2');
      result = { ...result, receipts: received, submissions: submitted, schema_reference: schemaReference };
    } else if (job.mode === 'pending-crash') {
      const base = await page.evaluate(() => window.authoringIntegration.commands.session.snapshot.base.head.revision);
      await page.getByLabel('Draft title', { exact: true }).fill('Original pending save');
      await page.getByRole('button', { name: 'Save draft', exact: true }).click();
      await page.waitForFunction(() => window.authoringIntegration.commands.snapshot.phase === 'unresolved');
      assert.equal(await page.getByRole('button', { name: 'Resume original command', exact: true }).count(), 0);
      await page.getByLabel('Draft title', { exact: true }).fill('Newer local work after crash');
      const deadline = Date.now() + 30000;
      while (true) {
        try { await readFile(job.barrier.release); break; } catch (error) { if (error.code !== 'ENOENT') throw error; }
        assert.ok(Date.now() < deadline, 'Owner did not restart'); await delay(20);
      }
      await page.getByRole('button', { name: 'Check original receipt', exact: true }).click();
      await page.getByRole('button', { name: 'Resume original command', exact: true }).waitFor();
      assert.equal(await page.evaluate(() => window.authoringIntegration.commands.session.snapshot.base.head.revision), base);
      await page.getByRole('button', { name: 'Resume original command', exact: true }).click();
      await page.waitForFunction(() => window.authoringIntegration.commands.snapshot.phase === 'settled');
      const state = await page.evaluate(() => window.authoringIntegration.commands.session.snapshot);
      assert.equal(state.base.head.revision, base + 1); assert.equal(state.base.head.title, 'Original pending save');
      assert.equal(state.local.title, 'Newer local work after crash');
      assert.equal(submitted.length, 2); assert.deepEqual(submitted[0], submitted[1]); assert.equal(received.length, 1);
      assert.equal(await page.evaluate(() => document.activeElement?.getAttribute('role')), 'status');
      result = { receipt: received[0], submission: submitted[0], newer_local_edits_preserved: true };
    } else if (job.mode === 'writers') {
      const secondContext = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
      const second = await secondContext.newPage();
      second.on('pageerror', error => errors.push(error.message));
      second.on('request', request => headers.push(request.allHeaders()));
      await second.goto(`http://127.0.0.1:${server.address().port}`);
      await second.waitForFunction(() => window.authoringIntegration?.catalog?.snapshot.phase === 'ready');
      const base = await page.evaluate(() => window.authoringIntegration.commands.session.snapshot.base.head.revision);
      assert.equal(await second.evaluate(() => window.authoringIntegration.commands.session.snapshot.base.head.revision), base);
      for (const [index, editor] of [page, second].entries()) {
        await editor.getByRole('navigation', { name: 'Draft nodes', exact: true }).getByRole('button', { name: 'seed \u00b7 invoke', exact: true }).click();
        await editor.getByLabel('Draft title', { exact: true }).fill(index ? 'Independent writer B' : 'Independent writer A');
      }
      await Promise.all([page, second].map(editor => editor.getByRole('button', { name: 'Save draft', exact: true }).click()));
      await Promise.all([page, second].map(editor => editor.waitForFunction(() => window.authoringIntegration.commands.snapshot.phase === 'settled')));
      const states = await Promise.all([page, second].map(editor => editor.evaluate(() => window.authoringIntegration.commands.session.snapshot)));
      assert.equal(states.filter(state => state.base.head.revision === base + 1).length, 1);
      assert.equal(states.filter(state => state.reason === 'draft_revision_conflict').length, 1);
      for (const [index, editor] of [page, second].entries()) {
        assert.equal(states[index].local.title, index ? 'Independent writer B' : 'Independent writer A');
        assert.equal(await editor.evaluate(() => document.activeElement?.getAttribute('role')), 'status');
        await editor.getByRole('region', { name: 'Draft node inspector', exact: true }).getByRole('heading', { name: 'seed', exact: true }).waitFor();
      }
      result = { base_revision: base, committed_revision: base + 1, receipts: received,
        independent_local_edits_preserved: true, selection_and_keyboard_focus_preserved: true };
      const secondContent = await second.content(); assert.ok(!secondContent.includes(token) && !secondContent.includes(registryToken));
      await secondContext.close();
    } else if (job.mode.startsWith('activate')) {
      await page.getByRole('button', { name: 'Validate saved revision', exact: true }).click();
      await page.waitForFunction(() => window.authoringIntegration.commands.session.snapshot.validationMatchesDraft);
      const region = page.getByRole('region', { name: 'Next campaign activation', exact: true });
      await region.getByText('Campaign inputs and limits', { exact: true }).click();
      await region.getByLabel('Campaign input bindings', { exact: true }).fill(JSON.stringify(job.inputs));
      await region.getByRole('button', { name: 'Request next campaign', exact: true }).click();
      await page.waitForFunction(expected => window.authoringIntegration.commands.activation.snapshot.phase === expected,
        job.expected_reason ? 'rejected' : 'accepted');
      assert.equal(submitted.length, 2); assert.equal(submitted[1].identity.command_family, 'graph.admit_draft');
      if (job.expected_reason) assert.equal(received[1].outcome.reason_code, job.expected_reason);
      result = { receipt: received[1], submission: submitted[1] };
    } else {
      const reads = await page.evaluate(async old => {
        const client = window.authoringIntegration.client, signal = new AbortController().signal;
        const record = await client.draft(old.record.head.draft_id, old.record.head.revision, signal);
        const validation = await client.validation(old.validation.validation_id, signal);
        // The installed client verifies exact original identities for receipt-only recovery.
        const receipts = await window.authoringIntegration.recover(old.submissions);
        return { record, validation, receipts };
      }, job.old);
      assert.deepEqual(reads.record, job.old.record); assert.deepEqual(reads.validation, job.old.validation); assert.deepEqual(reads.receipts, job.old.receipts);
      assert.equal(submitted.length, 0); result = reads;
    }
  }
  const screenshots = [];
  for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
    await page.setViewportSize(viewport); assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    const scan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze(); assert.deepEqual(scan.violations.map(item => item.id), []);
    const path = resolve(job.output, `${job.mode}-${viewport.width}.png`); await page.screenshot({ path, fullPage: true }); screenshots.push(path);
  }
  assert.deepEqual(errors, []);
  for (const header of await Promise.all(headers)) assert.equal(header.authorization, undefined);
  const content = await page.content(); assert.ok(!content.includes(token) && !content.includes(registryToken));
  const evidence = { ...result, screenshots, browser: browser.version(), owner_credentials_absent: true };
  await writeFile(resolve(job.output, 'browser.json'), JSON.stringify(evidence, null, 2)); console.log(JSON.stringify(evidence));
} catch (error) {
  if (page) {
    await page.screenshot({ path: resolve(job.output, 'failure.png'), fullPage: true }).catch(() => undefined);
    const state = await page.evaluate(() => ({ catalog: window.authoringIntegration?.catalog?.snapshot.phase,
      command: window.authoringIntegration?.commands?.snapshot.phase, activation: window.authoringIntegration?.commands?.activation?.snapshot, reason: window.authoringIntegration?.commands?.session.snapshot.reason,
      emergency: window.authoringIntegration?.emergency?.snapshot.phase, monitor: window.authoringIntegration?.monitor?.snapshot.phase,
      observedRevision: window.authoringIntegration?.monitor?.snapshot.window?.snapshot.cut.revision })).catch(() => null);
    await writeFile(resolve(job.output, 'failure.json'), JSON.stringify({ mode: job.mode, state, browserErrors: errors, error: String(error) }, null, 2));
  }
  throw error;
} finally { await browser.close(); await new Promise(resolve => server.close(resolve)); }
