import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import { build } from 'esbuild';

function ordered(value) {
  if (Array.isArray(value)) return value.map(ordered);
  return value && typeof value === 'object' ? Object.fromEntries(Object.keys(value).sort().map(key => [key, ordered(value[key])])) : value;
}
function digest(format, view, request) {
  const copy = { ...request }; delete copy.position;
  return createHash('sha256').update(JSON.stringify(ordered({ format, view, request: copy }))).digest('hex');
}
const summary = entity => ({ reference: entity.reference, entity_type: entity.entity_type, label: entity.label, is_latest: true, alias_target: null });

export async function startExploreHost() {
  await build({ entryPoints: ['tests/browser/explore_entry.tsx'], bundle: true, outdir: 'dist/explore-browser', format: 'esm', jsx: 'automatic', sourcemap: true });
  const fixture = JSON.parse(await readFile('tests/fixtures/scientific/explore.json', 'utf8'));
  const feedback = JSON.parse(await readFile('tests/fixtures/scientific/feedback-browser.json', 'utf8'));
  const many = structuredClone(feedback);
  many.question.objective = 'A deliberately long research question about measurement context, processing history, confidence and independently repeatable evidence across prepared candidate materials';
  many.question.criteria = Array.from({ length: 32 }, (_, i) => ({ criterion_id: 'c' + i, description: 'Independent synthetic criterion ' + i }));
  many.need.criterion_ids = many.question.criteria.map(c => c.criterion_id);
  many.assessment.outcome.assessment.needs = many.question.criteria.map(c => ({ ...structuredClone(feedback.assessment.outcome.assessment.needs[0]), criterion_id: c.criterion_id, gap: { ...feedback.assessment.outcome.assessment.needs[0].gap, criterion_id: c.criterion_id } }));
  const state = { mode: 'ready', held: null, requests: [] };
  const artifacts = new Map();
  function collect(value) {
    if (value && typeof value === 'object') {
      if (value.artifact_id) artifacts.set(value.artifact_id, value);
      for (const child of Object.values(value)) collect(child);
    }
  }
  collect(fixture); collect(feedback);
  const server = createServer(async (req, res) => {
    const path = new URL(req.url, 'http://localhost').pathname;
    const reply = (status, value) => { res.writeHead(status, { 'content-type': 'application/json', 'cache-control': 'no-store' }); res.end(JSON.stringify(value)); };
    try {
      if (path.startsWith('/api/')) {
        state.requests.push({ path, method: req.method, ownerAuthorization: !!req.headers.authorization });
        let raw = ''; for await (const chunk of req) { raw += chunk; if (raw.length > 262144) throw new Error('fixture_request_limit'); }
        const query = raw ? JSON.parse(raw) : null;
        if (state.held && path.endsWith('/entities')) { state.held.enter(); await state.held.promise; }
        if (state.mode === 'denied' && path.endsWith('/content')) { reply(403, {}); return; }
        if (state.mode === 'offline' && path.endsWith('/entities')) { reply(503, {}); return; }
        if (path.endsWith('/entities')) {
          let rows = state.mode === 'empty' ? [] : structuredClone(fixture.entities).map(summary);
          if (state.mode === 'long') rows[0].label = 'Candidate material with a deliberately long contextual name describing preparation and uncertain reported applicability';
          if (state.mode === 'paged') rows = Array.from({ length: 30 }, (_, i) => ({ ...rows[0], reference: { ...rows[0].reference, entity_id: 'A' + i }, label: 'Candidate ' + i }));
          rows = rows.filter(row => !query.text || row.label.includes(query.text) || row.reference.entity_id.includes(query.text));
          const offset = query.position?.entity_offset ?? 0, selected = rows.slice(offset, offset + query.limit), end = offset + selected.length;
          const sha = digest('knowledge.explore-query.v1', 'entity_search', query);
          reply(200, { wire_version: '1', request: query, query_sha256: sha, entities: selected, total: rows.length,
            next_position: end === rows.length ? null : { entity_offset: end, assertion_offset: 0, query_sha256: sha } }); return;
        }
        if (path.endsWith('/neighborhood')) {
          const entities = fixture.entities.map(summary), assertion = fixture.assertion;
          const row = Object.fromEntries(['reference', 'subject', 'predicate', 'object', 'polarity', 'posture'].map(key => [key, assertion[key]]));
          reply(200, { wire_version: '1', request: query, query_sha256: digest('knowledge.explore-query.v1', 'neighborhood', query), entities,
            assertions: [{ ...row, is_latest: true, retracted: false }], entity_total: 2, assertion_total: 1, unresolved_entities: [], next_position: null }); return;
        }
        if (path.endsWith('/object')) {
          const detail = query.selection.kind === 'assertion' ? { kind: 'assertion', record: fixture.assertion, is_latest: true, retracted: false } :
            { kind: 'entity', record: fixture.entities.find(entity => entity.reference.entity_id === query.selection.reference.entity_id), is_latest: true, alias_target: null };
          reply(200, { wire_version: '1', request: query, detail }); return;
        }
        if (path.includes('/acquisition/sources/')) { reply(200, fixture.source); return; }
        if (path.includes('/acquisition/traces/')) { reply(200, fixture.trace); return; }
        if (path.endsWith('/content')) { res.writeHead(200, { 'content-type': 'text/plain; charset=utf-8' }); res.end(state.mode === 'corrupt' ? 'X' + fixture.source_text.slice(1) : fixture.source_text); return; }
        if (path.endsWith('/derivation')) { reply(404, {}); return; }
        if (path.includes('/artifacts/')) { const record = artifacts.get(decodeURIComponent(path.split('/').at(-1))); reply(record ? 200 : 404, record ?? {}); return; }
        if (path.endsWith('/questions/read')) { reply(200, state.mode === 'feedback-long' ? many.question : feedback.question); return; }
        if (path.endsWith('/evidence-needs/read')) { reply(state.mode === 'feedback-denied' ? 403 : 200, state.mode === 'feedback-long' ? many.need : feedback.need); return; }
        if (path.endsWith('/assessments/read')) { reply(200, state.mode === 'feedback-pending' ? { ...feedback.assessment, outcome: { status: 'pending' } } : state.mode === 'feedback-long' ? many.assessment : feedback.assessment); return; }
        if (path.endsWith('/assessment-publications/read')) { reply(200, feedback.publication); return; }
        if (path.endsWith('/assessment-receipts/select')) { reply(200, query.revision.ordinal === 1 ? feedback.root : feedback.next); return; }
        if (path.includes('/proposals/')) { reply(200, feedback.proposal); return; }
        if (path.endsWith('/graph-changes/read')) { reply(200, feedback.change); return; }
        const research = fixture.research;
        if (path.endsWith('/specimens')) {
          reply(200, { ...research.specimen_page, request: query, query_sha256: digest('research.view-query.v1', 'specimens', query), next_position: null }); return;
        }
        if (path.endsWith('/properties')) {
          const rows = query.observations.map(ref => {
            const record = ref.observation_id === research.series.reference.observation_id ? research.series : research.observation;
            const value = record.value.kind === 'series' ? { kind: 'series', point_count: record.value.points.length, x_unit: record.value.x_unit, y_unit: record.value.y_unit } : record.value;
            return { ...research.property_page.rows[0], reference: ref, source: record.source, binding: record.binding, value, quality: record.quality };
          });
          const offset = query.position?.offset ?? 0, selected = rows.slice(offset, offset + query.limit), end = offset + selected.length, sha = digest('research.view-query.v1', 'properties', query);
          reply(200, { ...research.property_page, request: query, rows: selected, total: rows.length, query_sha256: sha,
            next_position: end === rows.length ? null : { offset: end, query_sha256: sha } }); return;
        }
        if (path.endsWith('/observation-series')) {
          reply(200, { ...research.series_page, request: query, points: research.series.value.points, total: research.series.value.points.length,
            query_sha256: digest('research.view-query.v1', 'observation_series', query), next_position: null }); return;
        }
        reply(404, {}); return;
      }
      if (path === '/') {
        res.setHeader('content-type', 'text/html'); res.end('<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Amphora Explore fixture</title><link rel="stylesheet" href="/explore_entry.css"></head><body><div id="root"></div><script type="module" src="/explore_entry.js"></script></body></html>'); return;
      }
      if (!['/explore_entry.js', '/explore_entry.css', '/explore_entry.js.map', '/explore_entry.css.map'].includes(path)) { res.writeHead(404); res.end(); return; }
      res.setHeader('content-type', path.endsWith('.css') ? 'text/css' : 'text/javascript'); res.end(await readFile(resolve('dist/explore-browser', path.slice(1))));
    } catch { if (!res.headersSent) res.writeHead(500); res.end(); }
  });
  await new Promise(done => server.listen(0, '127.0.0.1', done));
  return { state, server, url: `http://127.0.0.1:${server.address().port}` };
}
