import { createServer } from 'node:http';
import { mkdir, readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';
import { build } from 'esbuild';
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';

let input=''; for await (const chunk of process.stdin) input+=chunk;
const job=JSON.parse(input);
const token=process.env.STUDIO_OBSERVER_TOKEN;
assert.ok(token); delete process.env.STUDIO_OBSERVER_TOKEN; // Chromium must not inherit backend credentials.
assert.equal(new URL(job.endpoint).hostname,'127.0.0.1');
await mkdir(job.output,{recursive:true});
await build({entryPoints:['tests/integration/entry.tsx'],bundle:true,outdir:'dist/integration',format:'esm',jsx:'automatic'});
const prefix='/api/runtime/v1/graph-observations/'+encodeURIComponent(job.run);
const publicPaths=new Set([prefix+'/nodes',prefix+'/invalidations',...job.expected.nodes.map(node=>prefix+'/nodes/'+node.activation_id)]);
const forwarded=[];
const server=createServer(async(req,res)=>{
  try {
    const url=new URL(req.url,'http://localhost');
    if(req.method!=='GET'){res.writeHead(405);res.end();return;}
    if(publicPaths.has(url.pathname)){
      const response=await fetch(job.endpoint+url.pathname.slice('/api/runtime'.length)+url.search,
        {headers:{Authorization:'Bearer '+token,Accept:'application/json'},redirect:'error',signal:AbortSignal.timeout(15000)});
      const chunks=[];let bytes=0;
      for await(const chunk of response.body){bytes+=chunk.length;assert.ok(bytes<=2097152);chunks.push(chunk);}
      forwarded.push({path:url.pathname,status:response.status});
      res.writeHead(response.status,{'content-type':'application/json','cache-control':'no-store'});res.end(Buffer.concat(chunks));return;
    }
    if(url.pathname==='/'){
      const context=JSON.stringify({scope:job.scope,run:job.run}).replaceAll('<','\\u003c');
      res.setHeader('content-type','text/html');res.end(`<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Amphora · installed owner acceptance</title><link rel="stylesheet" href="/entry.css"></head><body><div id="root"></div><script id="observation-context" type="application/json">${context}</script><script type="module" src="/entry.js"></script></body></html>`);return;
    }
    if(!['/entry.js','/entry.css'].includes(url.pathname)){res.writeHead(404);res.end();return;}
    res.setHeader('content-type',url.pathname.endsWith('.css')?'text/css':'text/javascript');
    res.end(await readFile(resolve('dist/integration',url.pathname.slice(1))));
  }catch{if(!res.headersSent)res.writeHead(502);res.end('Observation peer unavailable');}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const browser=await chromium.launch({headless:true});
try{
  const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
  const page=await context.newPage();const errors=[],headers=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',request=>headers.push(request.allHeaders()));
  await page.goto(`http://127.0.0.1:${server.address().port}`);
  await page.waitForFunction(()=>['ready','empty'].includes(window.integrationHarness.model.snapshot.phase));
  const observation=await page.evaluate(()=>{
    const view=window.integrationHarness.model.snapshot;
    return {cut:view.window.snapshot.cut,nodes:view.window.nodes,snapshot_token:view.window.snapshot.snapshot_token,event_cursor:view.window.snapshot.event_cursor};
  });
  assert.deepEqual(observation.cut,job.expected.cut);
  assert.deepEqual(observation.nodes,job.expected.nodes);
  assert.equal(await page.locator('.node-list button').count(),job.expected.nodes.length);
  const details=[];
  for(const expected of job.expected.details){
    const button=page.locator(`.node-list button[data-node-id="${expected.node.activation_id}"]`);
    await button.focus();await page.keyboard.press('Enter');
    await page.waitForFunction(id=>window.integrationHarness.model.snapshot.detail?.node.activation_id===id,expected.node.activation_id);
    const actual=await page.evaluate(()=>window.integrationHarness.model.snapshot.detail);
    assert.deepEqual(actual,expected);details.push(actual);
    assert.equal(await page.getByRole('region',{name:'Selected node',exact:true}).getByRole('heading',{name:expected.node.path.node_id,exact:true}).count(),1);
  }
  await Promise.all([page.waitForResponse(response=>response.url().includes('/invalidations')),
    page.getByRole('button',{name:'Check for updates',exact:true}).click()]);
  if(job.old){
    const replay=await page.evaluate(async old=>{
      const {client}=window.integrationHarness;
      return {detail:await client.detail(old.cut.run_id,old.nodes[0].activation_id,old.snapshot_token,undefined,new AbortController().signal),
        events:await client.events(old.cut.run_id,old.event_cursor,new AbortController().signal)};
    },job.old);
    assert.deepEqual(replay.detail,job.expected.details[0]);assert.equal(replay.events.observed_revision,job.expected.cut.revision);assert.equal(replay.events.entries.length,0);
  }
  const scan=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
  assert.deepEqual(scan.violations.map(v=>v.id),[]);assert.deepEqual(errors,[]);
  for(const value of await Promise.all(headers))assert.ok(!value.authorization);
  assert.ok(!(await page.content()).includes(token));
  const screenshot=resolve(job.output,'monitor.png');await page.screenshot({path:screenshot,fullPage:true});
  console.log(JSON.stringify({...observation,details,browser:browser.version(),screenshot,forwarded,
    old_cursors_preserved:!!job.old,backend_credentials_absent_from_browser:true}));
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
