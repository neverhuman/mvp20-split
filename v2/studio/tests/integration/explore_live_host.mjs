/** Bounded loopback read adapter for acceptance only; never ships as a gateway. */
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { build } from 'esbuild';
import { allowedRoute } from '../../dist/src/transport/scientific/routes.js';

export async function startHost(owners, pins, output) {
  for (const owner of Object.values(owners)) {
    const url = new URL(owner.endpoint);
    if (url.protocol !== 'http:' || url.hostname !== '127.0.0.1' || url.pathname !== '/') throw new Error('owner_origin');
  }
  await build({ entryPoints: ['tests/integration/explore_live_entry.tsx'], bundle: true,
    outdir: output, format: 'esm', jsx: 'automatic' });
  const requests = [];
  const server = createServer(async (req, res) => {
    res.setHeader('cache-control', 'no-store');
    try {
      const url = new URL(req.url, 'http://localhost'), path = url.pathname;
      if (path.startsWith('/api/')) {
        if (url.search || req.headers.authorization || !allowedRoute(req.method, path)) { res.writeHead(403); res.end(); return; }
        const [, name, route] = /^\/api\/(data|knowledge|research)(\/v1\/.*)$/.exec(path) ?? [];
        if (!name) { res.writeHead(403); res.end(); return; }
        const chunks = []; let length = 0;
        for await (const chunk of req) { length += chunk.length; if (length > 262144) throw new Error('input_limit'); chunks.push(chunk); }
        const upstream = await fetch(owners[name].endpoint + route, { method: req.method, redirect: 'error',
          headers: { Authorization: 'Bearer ' + owners[name].token, 'Content-Type': 'application/json' },
          ...(req.method === 'POST' ? { body: Buffer.concat(chunks) } : {}), signal: AbortSignal.timeout(15000) });
        const parts = []; length = 0;
        for await (const chunk of upstream.body) { length += chunk.length; if (length > 4194304) throw new Error('output_limit'); parts.push(chunk); }
        requests.push({ path, method: req.method, status: upstream.status });
        res.writeHead(upstream.status, { 'content-type': upstream.headers.get('content-type') ?? 'application/json' });
        res.end(Buffer.concat(parts)); return;
      }
      if (req.method !== 'GET') { res.writeHead(405); res.end(); return; }
      if (path === '/') {
        res.setHeader('content-type', 'text/html');
        res.end('<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Amphora actual Explore acceptance</title><link rel="stylesheet" href="/explore_live_entry.css"></head><body><div id="root"></div><script type="application/json" id="explore-context">' + JSON.stringify(pins).replaceAll('<', '\\u003c') + '</script><script type="module" src="/explore_live_entry.js"></script></body></html>'); return;
      }
      if (!['/explore_live_entry.js', '/explore_live_entry.css'].includes(path)) { res.writeHead(404); res.end(); return; }
      res.setHeader('content-type', path.endsWith('.css') ? 'text/css' : 'text/javascript');
      res.end(await readFile(resolve(output, path.slice(1))));
    } catch { if (!res.headersSent) res.writeHead(502); res.end(); }
  });
  await new Promise(done => server.listen(0, '127.0.0.1', done));
  return { url: `http://127.0.0.1:${server.address().port}`, requests,
    close: () => { server.closeAllConnections(); return new Promise(done => server.close(done)); } };
}
