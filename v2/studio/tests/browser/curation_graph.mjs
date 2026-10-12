/** Exact production graph readback and canvas with scripted public owner records. */
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {build} from 'esbuild';
import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import {graphFixture} from '../../dist/tests/page_models/campaign_curation/graph_fixture.js';
const output=resolve(process.argv[2]??'../.test-results/curation-graph-browser-'+Date.now());await mkdir(output,{recursive:true});
await build({entryPoints:['tests/browser/curation_graph_entry.tsx'],bundle:true,format:'esm',jsx:'automatic',outfile:resolve(output,'app.js')});
const f=graphFixture();
const graph=f.curation.proposal.outcome.candidate.definition;
const heat=graph.body.nodes[0];
for(const name of ['solvency','stability'])graph.body.nodes.splice(-1,0,{...structuredClone(heat),node_id:'evaluate-'+name,
  tool:{...heat.tool,capability_id:'synthetic.'+name},inputs:[{port:'material',source:{kind:'output',node_id:'heat-mixture',port:'material'}}]});
graph.body.edges=[{source:'heat-mixture',target:'evaluate-solvency',route:'next'},{source:'heat-mixture',target:'evaluate-stability',route:'next'},
  {source:'evaluate-solvency',target:'done',route:'next'},{source:'evaluate-stability',target:'done',route:'next'}];
f.saved.definition=structuredClone(graph);
let mode='ready';const errors=[],requests=[];
const server=createServer(async(request,response)=>{
  try{
    const url=new URL(request.url,'http://localhost'),path=url.pathname;requests.push([request.method,path]);assert.equal(request.method,'GET');
    const send=(value,status=200)=>{response.writeHead(status,{'Content-Type':'application/json'});response.end(JSON.stringify(value));};
    if(path==='/binding')return send(f.selection);
    if(path.startsWith('/api/planning/v1/campaign-curations/'))return send(f.curation);
    if(path.startsWith('/api/runtime/v1/definition-drafts/')){
      assert.equal(url.searchParams.get('revision'),'1');
      if(mode==='denied')return send({},403);
      const value=structuredClone(path.endsWith('/proposed-draft')?f.saved:f.original);
      if(mode==='changed'&&path.endsWith('/proposed-draft'))value.definition.body.nodes[0].node_id='substituted';
      return send(value);
    }
    if(path==='/api/runtime/v1/definition-validations/validation')return send(f.validation);
    if(path==='/app.js'||path==='/app.css'){response.setHeader('Content-Type',path.endsWith('js')?'text/javascript':'text/css');return response.end(await readFile(resolve(output,path.slice(1))));}
    if(path==='/favicon.ico'){response.writeHead(204);return response.end();}
    if(path==='/'){response.setHeader('Content-Type','text/html');return response.end('<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Curation graph fixture</title><link rel="stylesheet" href="/app.css"></head><body><div id="root"></div><script type="module" src="/app.js"></script></body></html>');}
    throw Error('unexpected route '+path);
  }catch(error){errors.push(error.message);response.writeHead(500);response.end('fixture failure');}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const browser=await chromium.launch({headless:true});
const evidence={profile:'scripted-public-peers',screenshots:[],states:[],requests};
try{
  const context=await browser.newContext({viewport:{width:1440,height:1100},reducedMotion:'reduce'}),page=await context.newPage();
  page.on('pageerror',error=>errors.push(error.message));const url=`http://127.0.0.1:${server.address().port}`;
  await page.goto(url);await page.locator('.react-flow__node').first().waitFor();
  await page.locator('.react-flow__edge-path').first().waitFor({state:'attached'});
  assert.equal(await page.locator('.react-flow__node').count(),4);assert.ok(await page.locator('.react-flow__edge-path').count()>=4);
  await page.getByLabel('Inspect scientific step').selectOption('evaluate-solvency');
  await page.getByRole('region',{name:'Selected research step'}).waitFor();
  for(const width of [1440,390]){
    await page.setViewportSize({width,height:width===390?844:1100});
    await page.getByRole('region',{name:'Proposed campaign graph'}).scrollIntoViewIfNeeded();
    await page.waitForFunction(()=>{
      const bounds=document.querySelector('.react-flow').getBoundingClientRect();
      return [...document.querySelectorAll('.react-flow__node')].every(node=>{
        const box=node.getBoundingClientRect();
        return box.left>=bounds.left&&box.right<=bounds.right&&box.top>=bounds.top&&box.bottom<=bounds.bottom;
      });
    });
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    const issues=(await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations;
    assert.deepEqual(issues.map(item=>item.id),[]);
    const name=`graph-${width}.png`;await page.screenshot({path:resolve(output,name),fullPage:true});evidence.screenshots.push(name);
  }
  await page.getByRole('button',{name:'Original campaign',exact:true}).click();await page.getByRole('region',{name:'Original campaign graph'}).waitFor();
  await page.waitForFunction(()=>document.querySelectorAll('.react-flow__node').length===1);evidence.states.push('original-proposed-switch');
  for(const state of ['changed','denied']){
    mode=state;await page.goto(url);
    await page.getByText(state==='denied'?'Graph details are unavailable to this session.':'The original or proposed graph could not be verified.',{exact:true}).waitFor();
    assert.equal(await page.locator('.react-flow').count(),0);evidence.states.push(state);
  }
  assert.deepEqual(errors,[]);await writeFile(resolve(output,'evidence.json'),JSON.stringify(evidence,null,2));console.log(JSON.stringify({passed:true,output,states:evidence.states}));
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
