/** Scripted owner boundaries with real P1 toolkit formula/PNG; actual owners are P4. */
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {createHash} from 'node:crypto';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {build} from 'esbuild';
import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import {fixture} from '../../../dist/tests/page_models/candidate_inspector/fixture.js';
const output=resolve(process.argv[2]);await mkdir(output,{recursive:true});
await build({entryPoints:['tests/browser/candidate_inspector/entry.tsx'],bundle:true,format:'esm',jsx:'automatic',outfile:resolve(output,'app.js')});
const f=fixture(),input=Buffer.from(JSON.stringify(f.request));f.input.sha256=createHash('sha256').update(input).digest('hex');f.input.size_bytes=input.length;
f.result.source_sha256=f.input.sha256;const result=Buffer.from(JSON.stringify(f.result));f.output.sha256=createHash('sha256').update(result).digest('hex');f.output.size_bytes=result.length;
const snapshot={schema_version:'1',snapshot:{...f.anchor,node_count:1},nodes:[f.detail.node],next_cursor:null};
let denied=false;const errors=[],unexpected=[];
const server=createServer(async(req,res)=>{try{
 const path=new URL(req.url,'http://localhost').pathname;
 res.setHeader('Cache-Control','no-store');res.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'");
 const send=(body,status=200)=>{res.writeHead(status,{'Content-Type':'application/json'});res.end(JSON.stringify(body));};
 if(path==='/probe-context')return send({scope:f.anchor.cut.scope,run:f.anchor.cut.run_id});
 if(path==='/api/runtime/v1/graph-observations/run-1/nodes')return send(snapshot);
 if(path===`/api/runtime/v1/graph-observations/run-1/nodes/${f.detail.node.activation_id}`)return send(f.detail);
 if(path==='/api/runtime/v1/runs/run-1/completions/completion-1/producer')return send(f.proof);
 if(path==='/api/research/v1/candidates/read')return send(f.candidate);
 for(const [ref,bytes] of [[f.input,input],[f.output,result]])if(path.startsWith('/api/data/v1/artifacts/'+ref.artifact_id)){
  if(denied)return send({},403);
  if(path.endsWith('/content')){res.writeHead(200,{'Content-Type':'application/json'});return res.end(bytes);}return send(ref);
 }
 if(['/app.js','/app.css'].includes(path)){res.setHeader('Content-Type',path.endsWith('js')?'text/javascript':'text/css');return res.end(await readFile(resolve(output,path.slice(1))));}
 if(path==='/favicon.ico'){res.writeHead(204);return res.end();}
 if(path==='/'){res.setHeader('Content-Type','text/html');return res.end('<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Candidate inspection</title><link rel="stylesheet" href="/app.css"></head><body><div id="root"></div><script type="module" src="/app.js"></script></body></html>');}
 unexpected.push(path);send({},404);
 }catch{errors.push('host_failure');res.writeHead(500);res.end();}});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const browser=await chromium.launch({headless:true});
try{
 const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'}),page=await context.newPage();page.on('pageerror',()=>errors.push('page_error'));
 await page.goto('http://127.0.0.1:'+server.address().port);
 await page.getByLabel('Structure-producing step').selectOption({index:1});
 await page.getByText('C4H10O3',{exact:true}).waitFor();
 assert.ok(await page.getByRole('img').evaluate(img=>img.complete&&img.naturalWidth===800&&img.naturalHeight===600));
 await page.getByRole('button',{name:'Inspect producing execution step',exact:true}).click();
 await page.getByRole('region',{name:'Producing execution step',exact:true}).waitFor();
 for(const [width,zoom] of [[1440,1],[390,1],[1440,2]]){
  await page.setViewportSize({width,height:1000});await page.evaluate(zoom=>document.body.style.zoom=String(zoom),zoom);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  assert.ok(await page.evaluate(()=>[...document.querySelectorAll('.candidate-results>header,.candidate-detail>header')].every(header=>header.getBoundingClientRect().bottom<=header.nextElementSibling.getBoundingClientRect().top)));
  assert.deepEqual((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations.map(v=>v.id),[]);
  await page.screenshot({path:resolve(output,`candidate-${width}-${zoom}.png`),fullPage:true});
 }
 denied=true;await page.getByRole('button',{name:'Refresh candidate outputs'}).click();
 await page.getByLabel('Structure-producing step').selectOption({index:1});
 await page.getByText('Candidate evidence could not be verified.',{exact:false}).waitFor();assert.equal(await page.getByRole('img').count(),0);assert.equal(await page.getByText('C4H10O3',{exact:true}).count(),0);
 assert.deepEqual(errors,[]);assert.deepEqual(unexpected,[]);
 await writeFile(resolve(output,'evidence.json'),JSON.stringify({status:'passed',profile:'scripted owner boundaries / P1 toolkit formula and PNG',checks:['same-origin CSP','actual image decode','1440/390/200%','no overflow','axe clean','exact execution inspection','denial clears structure'],errors},null,2));
 console.log('Candidate browser checks passed: '+output);
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
