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
const artifactToken=process.env.STUDIO_ARTIFACT_TOKEN;
assert.ok(artifactToken); delete process.env.STUDIO_ARTIFACT_TOKEN;
assert.equal(new URL(job.endpoint).hostname,'127.0.0.1');
assert.equal(new URL(job.artifact_endpoint).hostname,'127.0.0.1');
await mkdir(job.output,{recursive:true});
await build({entryPoints:['tests/integration/entry.tsx'],bundle:true,outdir:'dist/integration',format:'esm',jsx:'automatic'});
const prefix='/api/runtime/v1/graph-observations/'+encodeURIComponent(job.run);
const publicPaths=new Set([prefix+'/nodes',prefix+'/invalidations',...job.expected.nodes.map(node=>prefix+'/nodes/'+node.activation_id)]);
publicPaths.add(prefix+'/views'); publicPaths.add(prefix+'/scopes');
for(const group of job.inspection.groups) publicPaths.add(prefix+'/scopes/'+group.graph_scope.scope_key+'/topology');
publicPaths.add('/api/runtime/v1/graph-runs/'+encodeURIComponent(job.run)+'/lineage');
publicPaths.add('/api/runtime/v1/runs/'+encodeURIComponent(job.run)+'/completions/'+encodeURIComponent(job.inspection.completion.completion_id));
for(const detail of job.expected.details) for(const output of detail.outputs)
  publicPaths.add(prefix+'/nodes/'+detail.node.activation_id+'/outputs/'+encodeURIComponent(output.port));
const artifactPath='/api/artifacts/v1/artifacts/'+encodeURIComponent(job.inspection.artifact.artifact_id);
const forwarded=[];
const server=createServer(async(req,res)=>{
  try {
    const url=new URL(req.url,'http://localhost');
    if(req.method!=='GET'){res.writeHead(405);res.end();return;}
    if(publicPaths.has(url.pathname)||url.pathname===artifactPath){
      const artifact=url.pathname===artifactPath;
      const response=await fetch((artifact?job.artifact_endpoint:job.endpoint)+url.pathname.slice(artifact?'/api/artifacts'.length:'/api/runtime'.length)+url.search,
        {headers:{Authorization:'Bearer '+(artifact?artifactToken:token),Accept:'application/json'},redirect:'error',signal:AbortSignal.timeout(15000)});
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
  const completion=job.inspection.completion;
  await page.locator(`.node-list button[data-node-id="${completion.activation_id}"]`).click();
  await page.getByRole('button',{name:'Inspect attempt '+completion.result.attempt_id,exact:true}).click();
  await page.getByRole('region',{name:'Retained completion',exact:true}).waitFor();
  assert.deepEqual(await page.evaluate(()=>window.integrationHarness.evidence.snapshot.completion.value),completion);
  const port=completion.result.outcome.outputs[0].port;
  await page.getByRole('button',{name:'Inspect output '+port,exact:true}).click();
  await page.getByRole('region',{name:'Output members',exact:true}).waitFor();
  const values=await page.evaluate(()=>window.integrationHarness.evidence.snapshot.values.value);
  assert.deepEqual(values.items,job.expected.values.find(item=>item.activation_id===completion.activation_id&&item.port===port).items);
  await page.getByRole('button',{name:'Inspect artifact '+job.inspection.artifact.artifact_id,exact:true}).click();
  await page.getByRole('region',{name:'Verified artifact metadata',exact:true}).waitFor();
  assert.deepEqual(await page.evaluate(()=>window.integrationHarness.evidence.snapshot.artifact.value),job.inspection.artifact);
  await page.screenshot({path:resolve(job.output,'evidence.png'),fullPage:true});
  await page.getByRole('button',{name:'Authored graph',exact:true}).click();
  await page.waitForFunction(()=>window.integrationHarness.namedViews.snapshot.phase==='ready');
  assert.deepEqual(await page.evaluate(()=>window.integrationHarness.namedViews.snapshot.catalog.page),job.inspection.catalog);
  const groups=[];
  for(const expected of job.inspection.groups){
    await page.evaluate(async parent=>{await window.integrationHarness.navigation.scopes(parent??undefined);},expected.graph_scope.parent_activation_id);
    const index=await page.evaluate(key=>window.integrationHarness.navigation.snapshot.scopes.scopes.findIndex(item=>item.scope_key===key),expected.graph_scope.scope_key);
    assert.ok(index>=0);
    await page.getByRole('list',{name:'Occurrence groups',exact:true}).getByRole('button').nth(index).click();
    await page.waitForFunction(key=>window.integrationHarness.navigation.snapshot.topology?.page.graph_scope.scope_key===key,expected.graph_scope.scope_key);
    const actual=await page.evaluate(()=>window.integrationHarness.navigation.snapshot.topology.page);
    assert.deepEqual(actual,expected); groups.push(actual);
  }
  await page.getByText('Named research views',{exact:true}).click();
  await page.getByRole('button',{name:'Inspect predecessor lineage',exact:true}).click();
  await page.waitForFunction(()=>['ready','failed'].includes(window.integrationHarness.namedViews.snapshot.lineagePhase));
  assert.deepEqual(await page.evaluate(()=>window.integrationHarness.namedViews.snapshot.lineage),job.inspection.lineage);
  const inspection={groups,completion,artifact:job.inspection.artifact,lineage:job.inspection.lineage};
  if(job.old) assert.deepEqual(inspection,job.old.inspection);
  const scan=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
  assert.deepEqual(scan.violations.map(v=>v.id),[]);assert.deepEqual(errors,[]);
  for(const value of await Promise.all(headers))assert.ok(!value.authorization);
  assert.ok(!(await page.content()).includes(token));
  assert.ok(!(await page.content()).includes(artifactToken));
  assert.ok(!forwarded.some(item=>item.path.endsWith('/content')));
  const screenshot=resolve(job.output,'monitor.png');await page.screenshot({path:screenshot,fullPage:true});
  console.log(JSON.stringify({...observation,details,inspection,browser:browser.version(),screenshot,forwarded,
    old_cursors_preserved:!!job.old,backend_credentials_absent_from_browser:true}));
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
