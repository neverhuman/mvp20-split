/** Scripted public peers with exact tool-produced numeric bytes; not a live campaign. */
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {build} from 'esbuild';
import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import {snapshot,detail} from '../../dist/tests/fixtures/observations.js';
const output=resolve(process.argv[2]);await mkdir(output,{recursive:true});
await build({entryPoints:['tests/browser/generation_comparison_entry.tsx'],bundle:true,format:'esm',jsx:'automatic',outfile:resolve(output,'app.js')});
const fixtures=await Promise.all(['first','second'].map(async name=>({record:JSON.parse(await readFile('tests/fixtures/generation_comparison/'+name+'.json','utf8')),bytes:await readFile('tests/fixtures/generation_comparison/'+name+'.content.json')})));
const scope=fixtures[0].record.reference.scope,pageData=snapshot();pageData.snapshot.cut.scope=scope;
const details=fixtures.map((f,i)=>{const d=detail(i+1);d.cut=pageData.snapshot.cut;d.outputs=[{port:'checkpoint',kind:'artifact',item_count:1,missing_count:0,artifact:f.record.reference}];return d;});
let denied=false;const errors=[],unexpected=[];
const server=createServer(async(req,res)=>{try{
 const path=new URL(req.url,'http://localhost').pathname;
 const send=(value,status=200)=>{res.writeHead(status,{'Content-Type':'application/json'});res.end(JSON.stringify(value));};
 if(path==='/probe-context')return send({scope,run:'run-1'});
 if(path==='/api/runtime/v1/graph-observations/run-1/nodes')return send(pageData);
 const d=details.find(d=>path.endsWith('/nodes/'+d.node.activation_id));if(d)return send(d);
 const f=fixtures.find(f=>path.includes('/artifacts/'+f.record.reference.artifact_id));
 if(f){if(denied)return send({error:'denied'},403);if(path.endsWith('/content')){res.writeHead(200,{'Content-Type':'application/json'});return res.end(f.bytes);}return send(f.record.reference);}
 if(['/app.js','/app.css'].includes(path)){res.setHeader('Content-Type',path.endsWith('js')?'text/javascript':'text/css');return res.end(await readFile(resolve(output,path.slice(1))));}
 if(path==='/favicon.ico'){res.writeHead(204);return res.end();}
 if(path==='/'){res.setHeader('Content-Type','text/html');return res.end('<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Generation fixture</title><link rel="stylesheet" href="/app.css"></head><body><div id="root"></div><script type="module" src="/app.js"></script></body></html>');}
 unexpected.push(path);send({},404);
 }catch(e){errors.push(e.message);res.writeHead(500);res.end();}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await chromium.launch({headless:true});
try{
 const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:'+server.address().port);
 await page.getByLabel('Checkpoint A',{exact:true}).selectOption({index:1});await page.getByLabel('Checkpoint B',{exact:true}).selectOption({index:2});
 await page.getByRole('heading',{name:'Objective comparison',exact:true}).waitFor();
 for(const width of [1440,390]){await page.setViewportSize({width,height:1000});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.deepEqual((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations.map(v=>v.id),[]);await page.screenshot({path:resolve(output,'comparison-'+width+'.png'),fullPage:true});}
 denied=true;await page.getByLabel('Checkpoint B',{exact:true}).selectOption({index:1});await page.getByText('Search evidence is unavailable to this session.',{exact:true}).waitFor();assert.equal(await page.getByRole('heading',{name:'A: Generation 0'}).count(),0);
 assert.deepEqual(errors,[]);assert.deepEqual(unexpected,[]);
 await writeFile(resolve(output,'evidence.json'),JSON.stringify({status:'passed',profile:'scripted public peers / actual tool fixture bytes',checks:['1440/390','no overflow','axe clean','denial clears both panes'],errors},null,2));console.log('Generation browser checks passed: '+output);
}finally{await browser.close();await new Promise(r=>server.close(r));}
