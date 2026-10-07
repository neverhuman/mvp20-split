/** Deployable static entry; never includes fixtures or owner credentials. */
import { build } from 'esbuild';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
const output = resolve('dist/local');
await mkdir(output, {recursive:true});
await build({ entryPoints:['src/entry.tsx'], bundle:true, outfile:resolve(output,'app.js'), format:'esm', jsx:'automatic', minify:true, sourcemap:false });
await writeFile(resolve(output,'index.html'), '<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Amphora research workspace</title><link rel="stylesheet" href="/app.css"></head><body><div id="root"></div><script type="module" src="/app.js"></script></body></html>');
