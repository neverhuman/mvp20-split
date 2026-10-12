/** Production presentation, model and HTTP transport; scripted public evidence only. */
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { build } from 'esbuild';
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import { fulfilled } from '../../dist/tests/transport/campaign_curation/fixtures.js';
const output = resolve(process.argv[2] ?? '../.test-results/curation-browser-' + Date.now());
await mkdir(output, { recursive: true });
await build({ entryPoints: ['tests/browser/campaign_curation_entry.tsx'], bundle: true, format: 'esm', jsx: 'automatic', outfile: resolve(output, 'app.js') });
let mode = 'verified';
const requests = [], errors = [], unexpected = [];
const base = fulfilled();
const crowded = structuredClone(base);
crowded.curation.proposal.outcome.gaps = Array.from({length:16},(_,index)=>({...structuredClone(base.capability.gap),gap_key:'step-'+index,
  purpose:`Step ${index+1}: characterize the heated multicomponent mixture and preserve provenance across subsequent additions`,
  graph_gap:'After combining several inputs, before heating and selecting the material for the next process branch'}));
crowded.curation.capability_requests = crowded.curation.proposal.outcome.gaps.map((_,index)=>({...base.capability.reference,request_id:'capability-'+'a'.repeat(64)+'-'+String(index).padStart(2,'0')}));
const server = createServer(async (request, response) => {
  try {
    const path = new URL(request.url, 'http://localhost').pathname;
    requests.push([request.method, path]);
    assert.equal(request.method, 'GET');
    const send = (value, status = 200) => { response.writeHead(status, {'Content-Type':'application/json'}); response.end(JSON.stringify(value)); };
    if (path === '/binding') return send(base.selection);
    if (path.startsWith('/api/planning/v1/campaign-curations/')) {
      if (mode === 'denied') return send({reason_code:'planning_access_denied'},403);
      if (mode === 'missing') return send({reason_code:'curation_not_recorded'},404);
      if (mode === 'unavailable') return send({error:'owner_request_rejected'},503);
      const value = structuredClone(mode==='crowded'?crowded.curation:base.curation);
      if (mode === 'invalid') value.specification.context.predecessor.run_id = 'other-run';
      if (['queued','failed','abstained','indeterminate'].includes(mode)) { value.receipt.phase=mode; value.proposal=null; value.provider=null; value.capability_requests=[]; }
      return send(value);
    }
    if (path.startsWith('/api/planning/v1/capability-requests/')) {
      if (mode === 'detail-denied') return send({reason_code:'planning_access_denied'},403);
      if (mode === 'crowded') { const index=Number(path.slice(-2)); return send({...base.capability,reference:crowded.curation.capability_requests[index],gap:crowded.curation.proposal.outcome.gaps[index],status:'requested',fulfillment:null}); }
      return send(fulfilled(['pending','rejected'].includes(mode)?mode:'verified').capability);
    }
    if (path === '/app.js' || path === '/app.css') { response.setHeader('Content-Type',path.endsWith('js')?'text/javascript':'text/css'); return response.end(await readFile(resolve(output,path.slice(1)))); }
    if (path === '/favicon.ico') { response.writeHead(204); return response.end(); }
    if (path === '/') { response.setHeader('Content-Type','text/html'); return response.end('<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Campaign curation fixture</title><link rel="stylesheet" href="/app.css"></head><body><div id="root"></div><script type="module" src="/app.js"></script></body></html>'); }
    unexpected.push(path); send({},404);
  } catch(error) { errors.push(error.message); response.writeHead(500); response.end('fixture failure'); }
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const browser = await chromium.launch({headless:true});
const evidence = {profile:'scripted-public-peers',states:[],screenshots:[],requests};
try {
  const context = await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
  const page = await context.newPage();
  page.on('pageerror',error=>errors.push(error.message));
  const url = `http://127.0.0.1:${server.address().port}`;
  await page.goto(url);
  await page.locator('.curation-detail h2').waitFor();
  await page.getByRole('button',{name:/Measure the heated mixture/}).click();
  await page.waitForFunction(()=>document.activeElement?.matches('.curation-detail h2'));
  for(const width of [1440,390]) {
    await page.setViewportSize({width,height:width===390?844:1000});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    const issues=(await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations;
    assert.deepEqual(issues.map(issue=>issue.id),[]);
    const name=`curation-${width}.png`; await page.screenshot({path:resolve(output,name),fullPage:true}); evidence.screenshots.push(name);
  }
  for(const state of ['pending','rejected','queued','failed','abstained','indeterminate','missing','denied','detail-denied','invalid','unavailable']) {
    mode=state; await page.goto(url);
    if(['pending','rejected'].includes(state)) await page.locator('.curation-detail h2').waitFor();
    else await page.getByText({queued:'Awaiting a retained proposal',failed:'No retained proposal',abstained:'No retained proposal',indeterminate:'No retained proposal',missing:'No revision record is available for this selection.',denied:'This revision or its capability details are not available to this session.','detail-denied':'This revision or its capability details are not available to this session.',invalid:'The recorded revision could not be verified.',unavailable:'The revision service is temporarily unavailable.'}[state],{exact:true}).waitFor();
    if(['denied','detail-denied'].includes(state)) assert.equal(await page.locator('.curation-intent').count(),0);
    evidence.states.push(state);
  }
  mode='crowded'; await page.goto(url); await page.locator('.curation-detail h2').waitFor();
  assert.equal(await page.locator('.curation-request-list button').count(),16);
  await page.locator('.curation-request-list button').last().focus(); await page.keyboard.press('Enter');
  await page.waitForFunction(()=>document.activeElement?.matches('.curation-detail h2') && document.activeElement.textContent.startsWith('Step 16:'));
  for(const width of [1440,390]) {
    await page.setViewportSize({width,height:width===390?844:1000});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    const name=`curation-crowded-${width}.png`; await page.screenshot({path:resolve(output,name),fullPage:true}); evidence.screenshots.push(name);
  }
  evidence.states.push('sixteen-long-requests-keyboard');
  await page.getByRole('button',{name:'Back to next iteration'}).click();
  assert.equal(new URL(page.url()).hash,'#view=design');
  assert.deepEqual(errors,[]); assert.deepEqual(unexpected,[]);
  await writeFile(resolve(output,'evidence.json'),JSON.stringify(evidence,null,2));
  console.log(JSON.stringify({passed:true,output,states:evidence.states,screenshots:evidence.screenshots}));
} finally { await browser.close(); await new Promise(resolve=>server.close(resolve)); }
