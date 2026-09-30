import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { resolve, extname } from 'node:path';
import { build } from 'esbuild';

export async function startSpike() {
  await build({ entryPoints: ['spikes/interaction/main.tsx'], bundle: true, outdir: 'dist/spike', format: 'esm', sourcemap: true, jsx: 'automatic' });
  const counts = { requests: 0, maxNodes: 0, returnedNodes: 0 };
  const server = createServer(async (req, res) => {
    try {
      const url = new URL(req.url, 'http://localhost');
      if (url.pathname === '/fixture/scene') {
        // Synthetic topology defined by this fixture only, never inferred from Runtime activation order.
        const query = (url.searchParams.get('q') ?? '').toLowerCase().slice(0, 120);
        const labels = ['Seed candidates', 'Select population', 'Mutate representation', 'Score candidate', 'Retain evidence'];
        const match = [];
        for (let i = 0; i < 10000; i++) {
          const label = `${labels[i % 5]} · ${String(i + 1).padStart(5, '0')}${i === 37 ? ' — long applicability and evidence-context label for the synthetic representation variant' : ''}`;
          if (label.toLowerCase().includes(query)) match.push({ i, label });
        }
        const offset = Math.max(0, Math.min(match.length, Number(url.searchParams.get('offset')) || 0));
        const nodes = match.slice(offset, offset + 200).map(({ i, label }) => ({ id: `n${i}`, label,
          status: i % 29 === 0 ? 'failed' : i % 7 === 0 ? 'running' : 'completed',
          x: (i % 5) * 245, y: Math.floor(i / 5) * 100 }));
        const ids = new Set(nodes.map(n => n.id));
        const edges = nodes.filter(n => Number(n.id.slice(1)) % 5 !== 4 && ids.has(`n${Number(n.id.slice(1)) + 1}`))
          .map(n => ({ id: `e${n.id}`, source: n.id, target: `n${Number(n.id.slice(1)) + 1}` }));
        counts.requests++; counts.maxNodes = Math.max(counts.maxNodes, nodes.length); counts.returnedNodes += nodes.length;
        res.writeHead(200, { 'content-type': 'application/json', 'cache-control': 'no-store' });
        res.end(JSON.stringify({ nodes, edges, total: match.length, offset })); return;
      }
      if (url.pathname === '/fixture/counts') { res.setHeader('content-type', 'application/json'); res.end(JSON.stringify(counts)); return; }
      if (url.pathname === '/') {
        res.setHeader('content-type', 'text/html');
        res.end('<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Amphora · interaction prototype</title><link rel="stylesheet" href="/main.css"></head><body><div id="root"></div><script type="module" src="/main.js"></script></body></html>'); return;
      }
      if (!['/main.js', '/main.css', '/main.js.map', '/main.css.map'].includes(url.pathname)) { res.writeHead(404); res.end(); return; }
      res.setHeader('content-type', extname(url.pathname) === '.css' ? 'text/css' : 'text/javascript');
      res.end(await readFile(resolve('dist/spike', url.pathname.slice(1))));
    } catch { res.writeHead(500); res.end('Synthetic fixture unavailable'); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  return { server, url: `http://127.0.0.1:${server.address().port}`, counts };
}
