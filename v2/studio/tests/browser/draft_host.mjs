import { createServer } from 'node:http';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { build } from 'esbuild';
import { revision, scope } from '../../dist/tests/fixtures/authoring.js';
import { registryFixture } from '../../dist/tests/fixtures/registry.js';

/** Synthetic public-wire peer only; no claim to implement Runtime validation or authority. */
export async function startDraftHost() {
  await build({ entryPoints: ['tests/browser/draft_entry.tsx'], bundle: true, outdir: 'dist/draft-browser', format: 'esm', jsx: 'automatic', sourcemap: true });
  const { release, universe } = registryFixture();
  const bytes = Buffer.from(JSON.stringify({ type: 'object', additionalProperties: false, required: ['gain'], properties: {
    gain: { type: 'number', minimum: 0, maximum: 2 }, values: { type: 'array', items: { type: 'number' }, maxItems: 10 } } }));
  const reference = { schema_id: 'numeric-input', version: '1', sha256: createHash('sha256').update(bytes).digest('hex') };
  release.lock.input_schemas[0].schema_ref = reference; release.descriptor.tool.inputs[0].schema_ref = reference;
  universe.reviewed_tools = [structuredClone(release.lock)]; universe.schemas = [reference];
  const state = { mode: 'ready', head: revision(), records: new Map([[1, revision()]]), receipts: new Map(), validations: new Map(), requests: [], saveGate: null };
  const server = createServer(async (req, res) => {
    const url = new URL(req.url, 'http://localhost');
    const json = (status, value) => { res.writeHead(status, { 'content-type': 'application/json', 'cache-control': 'no-store' }); res.end(JSON.stringify(value)); };
    try {
      if (url.pathname.startsWith('/api/')) {
        state.requests.push({ method: req.method, path: url.pathname });
        if (state.mode === 'catalog-denied' && url.pathname.endsWith('/definition-universe')) { json(403, { detail: 'private diagnostics' }); return; }
        if (url.pathname.endsWith('/definition-universe')) { json(200, universe); return; }
        if (url.pathname.endsWith('/releases')) { json(200, { items: [release], next_after: null }); return; }
        if (url.pathname.includes('/definition-schemas/')) {
          json(200, { reference, scope, universe_sha256: universe.universe_sha256, schema_bytes_base64: bytes.toString('base64') }); return;
        }
        if (req.method === 'POST') {
          let body = ''; for await (const chunk of req) body += chunk;
          const command = JSON.parse(body), id = command.identity.command_id;
          const binding = { identity: command.identity, operation_id: id, request_sha256: createHash('sha256').update(body).digest('hex') };
          if (url.pathname.endsWith('/graph-runs/drafts')) {
            if (state.mode === 'activation-denied') { json(403, { detail: 'private diagnostics' }); return; }
            if (state.mode === 'activation-collision') { json(409, { reason_code: 'command_identity_conflict' }); return; }
            const outcome = state.mode === 'activation-active'
              ? { binding, status: 'rejected', reason_code: 'active_run_exists' }
              : { binding, status: 'accepted', committed: { kind: 'run', object_id: 'new-run', revision: 0 } };
            state.receipts.set(id, { outcome });
            json(state.mode === 'activation-lost' ? 503 : 200, state.mode === 'activation-lost' ? {} : { outcome }); return;
          }
          if (state.mode === 'pending-owner') {
            state.receipts.set(id, { outcome: { status: 'pending', binding } }); json(503, {}); return;
          }
          if (state.mode === 'identity-conflict') { json(409, { reason_code: 'command_identity_conflict' }); return; }
          if (state.mode === 'save-denied') { json(403, { detail: 'private save diagnostics' }); return; }
          if (state.mode === 'conflict') { json(200, { outcome: { status: 'rejected', binding, reason_code: 'draft_revision_conflict' } }); return; }
          let committed;
          if (url.pathname.endsWith('/save')) {
            const number = state.head.head.revision + 1;
            state.head = { scope, definition: command.payload.definition, parent_revision: number - 1, head: {
              draft_id: 'draft', revision: number, title: command.payload.title, content_sha256: createHash('sha256').update(JSON.stringify(command.payload)).digest('hex') } };
            state.records.set(number, structuredClone(state.head));
            committed = { kind: 'draft_revision', object_id: 'draft', revision: number, content_sha256: state.head.head.content_sha256 };
          } else {
            const validation = { scope, draft_id: 'draft', revision: command.payload.revision, content_sha256: command.payload.content_sha256,
              validation_id: 'validation', universe_sha256: universe.universe_sha256, structurally_valid: true, findings: [], pending_checks: ['current_tool_eligibility'],
              plan_sha256: 'f'.repeat(64), scientific_acceptance: 'not_established' };
            state.validations.set('validation', validation);
            committed = { kind: 'draft_validation', object_id: 'validation', revision: validation.revision, content_sha256: validation.content_sha256 };
          }
          const receipt = { outcome: { status: 'accepted', binding, committed } }; state.receipts.set(id, receipt);
          if (state.saveGate && url.pathname.endsWith('/save')) await state.saveGate;
          json(state.mode === 'lost-ack' ? 503 : 200, state.mode === 'lost-ack' ? { detail: 'receipt unavailable' } : receipt); return;
        }
        if (url.pathname.includes('/commands/graph.admit_draft/')) { json(200, state.receipts.get(url.pathname.split('/').at(-1))); return; }
        if (url.pathname.includes('/definition-commands/')) { json(200, state.receipts.get(url.pathname.split('/').at(-1))); return; }
        if (url.pathname.includes('/definition-validations/')) { json(200, state.validations.get(url.pathname.split('/').at(-1))); return; }
        if (url.pathname.endsWith('/definition-drafts/draft')) { json(200, state.records.get(Number(url.searchParams.get('revision') ?? state.head.head.revision))); return; }
        json(404, {}); return;
      }
      if (url.pathname === '/') {
        res.setHeader('content-type', 'text/html'); res.end('<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Amphora draft fixture</title><link rel="stylesheet" href="/draft_entry.css"></head><body><div id="root"></div><script type="module" src="/draft_entry.js"></script></body></html>'); return;
      }
      if (!['/draft_entry.js', '/draft_entry.css'].includes(url.pathname)) { res.writeHead(404); res.end(); return; }
      res.setHeader('content-type', url.pathname.endsWith('.css') ? 'text/css' : 'text/javascript'); res.end(await readFile(resolve('dist/draft-browser', url.pathname.slice(1))));
    } catch { if (!res.headersSent) res.writeHead(500); res.end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  return { state, server, url: `http://127.0.0.1:${server.address().port}`, descriptor: release.lock.descriptor_sha256 };
}
