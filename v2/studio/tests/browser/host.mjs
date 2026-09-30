import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { build } from 'esbuild';
import { snapshot, detail, events } from '../../dist/tests/fixtures/observations.js';

export async function startObservationHost() {
  await build({ entryPoints: ['tests/browser/entry.tsx'], bundle: true, outdir: 'dist/browser', format: 'esm', jsx: 'automatic', sourcemap: true });
  const state = { revision: 1, mode: 'ready', hook: null, requests: [], responses: [] };
  const server = createServer(async (req, res) => {
    const url = new URL(req.url, 'http://localhost');
    const parts = url.pathname.split('/');
    const json = (status, data) => {
      state.responses.push({ path: url.pathname, status });
      res.writeHead(status, { 'content-type': 'application/json', 'cache-control': 'no-store' }); res.end(JSON.stringify(data));
    };
    try {
      if (['/api/runtime/v1/graph-observations/', '/api/runtime/v1/graph-runs/', '/api/runtime/v1/runs/', '/api/runtime/v1/commands/', '/api/artifacts/v1/artifacts/'].some(prefix => url.pathname.startsWith(prefix))) {
        state.requests.push({ path: url.pathname, query: url.search, revision: state.revision });
        if (state.hook && await state.hook(url, json, req)) return;
        if (state.mode === 'denied') { json(403, { detail: 'private server diagnostics must not render' }); return; }
        const run = parts[5], activation = parts[7];
        if (parts[6] === 'invalidations') { json(200, { ...events([],state.revision), run_id: run }); return; }
        if (activation) {
          const value = detail(Number.parseInt(activation,16), state.revision); value.cut.run_id = run;
          json(200, value); return;
        }
        json(200, snapshot({ run, revision: state.revision, ids: state.mode === 'empty' ? [] : [1,2],
          ...(state.mode === 'paged' ? { total: 4, next: 'next-window' } : {}) })); return;
      }
      if (url.pathname === '/') {
        res.setHeader('content-type', 'text/html');
        res.end('<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Amphora · observation fixture</title><link rel="stylesheet" href="/entry.css"></head><body><div id="root"></div><script type="module" src="/entry.js"></script></body></html>'); return;
      }
      if (!['/entry.js','/entry.css','/entry.js.map','/entry.css.map'].includes(url.pathname)) { res.writeHead(404); res.end(); return; }
      res.setHeader('content-type', url.pathname.endsWith('.css') ? 'text/css' : 'text/javascript');
      res.end(await readFile(resolve('dist/browser',url.pathname.slice(1))));
    } catch { if (!res.headersSent) res.writeHead(500); res.end(); }
  });
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  return { state, server, url: `http://127.0.0.1:${server.address().port}` };
}
