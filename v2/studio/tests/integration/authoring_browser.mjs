import { createServer } from 'node:http';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';
import { build } from 'esbuild';
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';

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
    const runtime = path.startsWith('/api/runtime/v1/') && (job.mode === 'cancel'
      ? [ `/api/runtime/v1/graph-observations/${encodeURIComponent(job.run)}/nodes`, `/api/runtime/v1/graph-observations/${encodeURIComponent(job.run)}/invalidations`, '/api/runtime/v1/runs/cancel'].includes(path) || path.startsWith('/api/runtime/v1/commands/runtime.cancel/')
      : path === `/api/runtime/v1/definition-drafts/${encodeURIComponent(job.draft)}` ||
        ['/api/runtime/v1/definition-drafts/save', '/api/runtime/v1/definition-drafts/validate', '/api/runtime/v1/definition-universe'].includes(path) ||
        ['/api/runtime/v1/definition-schemas/', '/api/runtime/v1/definition-validations/', '/api/runtime/v1/definition-commands/definition.save/', '/api/runtime/v1/definition-commands/definition.validate/'].some(prefix => path.startsWith(prefix)));
    if (registry || runtime) {
      const permittedPost = job.mode === 'cancel' ? path.endsWith('/runs/cancel') : job.mode === 'edit' && ['/definition-drafts/save', '/definition-drafts/validate'].some(suffix => path.endsWith(suffix));
      if (req.method !== 'GET' && !(req.method === 'POST' && permittedPost)) { res.writeHead(405); res.end(); return; }
      const chunks = []; let size = 0;
      for await (const chunk of req) { size += chunk.length; assert.ok(size <= 262144); chunks.push(chunk); }
      const body = req.method === 'POST' ? Buffer.concat(chunks) : undefined;
      if (body) submitted.push(JSON.parse(body.toString('utf-8')));
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
  if (job.mode === 'cancel') {
    await page.waitForFunction(() => window.authoringIntegration?.emergency?.snapshot.revision !== null && window.authoringIntegration?.emergency?.snapshot.status === 'running');
    await page.getByRole('link', { name: 'Emergency control', exact: true }).click();
    await page.getByRole('button', { name: 'Request emergency stop', exact: true }).click();
    await page.waitForFunction(() => window.authoringIntegration.emergency.snapshot.phase === 'accepted');
    await page.getByRole('button', { name: 'Refresh observation', exact: true }).click();
    await page.waitForFunction(() => window.authoringIntegration.monitor.snapshot.window?.snapshot.status === 'cancelled');
    assert.equal(submitted.length, 1); assert.equal(received[0].outcome.status, 'accepted');
    result = { receipt: received[0], observed_status: 'cancelled' };
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
      command: window.authoringIntegration?.commands?.snapshot.phase, reason: window.authoringIntegration?.commands?.session.snapshot.reason,
      emergency: window.authoringIntegration?.emergency?.snapshot.phase, monitor: window.authoringIntegration?.monitor?.snapshot.phase,
      observedRevision: window.authoringIntegration?.monitor?.snapshot.window?.snapshot.cut.revision })).catch(() => null);
    await writeFile(resolve(job.output, 'failure.json'), JSON.stringify({ mode: job.mode, state, browserErrors: errors, error: String(error) }, null, 2));
  }
  throw error;
} finally { await browser.close(); await new Promise(resolve => server.close(resolve)); }
