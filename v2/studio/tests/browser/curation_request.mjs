/** Production request form/model/transport against scripted public owners; zero model calls. */
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {createHash} from 'node:crypto';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {build} from 'esbuild';
import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
const output=resolve(process.argv[2]??'../.test-results/curation-request-browser-'+Date.now());await mkdir(output,{recursive:true});
await build({entryPoints:['tests/browser/curation_request_entry.tsx'],bundle:true,format:'esm',jsx:'automatic',outfile:resolve(output,'app.js')});
const vector=JSON.parse(await readFile('tests/fixtures/campaign_curation/commands.json','utf8'))[0],scope=vector.request.identity.scope;
const actor={scope,actor_id:'owner',run_id:'original-run'};
let original=null,ack=null,mode='ready';const requests=[],errors=[],unexpected=[];
const server=createServer(async(request,response)=>{
  try{
    const path=new URL(request.url,'http://localhost').pathname;requests.push([request.method,path]);
    let raw='';for await(const chunk of request)raw+=chunk;
    const send=(value,status=200)=>{response.writeHead(status,{'Content-Type':'application/json'});response.end(JSON.stringify(value));};
    if(path==='/binding')return send({actor,context:vector.request.payload.context});
    if(path==='/api/runtime/v1/graph-observations/original-run/nodes')return send({snapshot:{cut:{scope,run_id:actor.run_id,plan_sha256:'a'.repeat(64),revision:9,frontier_revision:0},
      status:mode==='running'?'running':'completed',budget:{limit:8,reserved:0,spent:0},query:{scope_key:null,frontier_only:false},node_count:0,snapshot_token:'snapshot',event_cursor:'events'},nodes:[],next_cursor:null});
    if(path==='/api/planning/v1/campaign-curations'){
      assert.equal(request.method,'POST');
      const command=JSON.parse(raw);assert.equal(command.payload.policy_id,'synthetic');
      if(original)assert.equal(raw,original);else{
        original=raw;ack={wire_version:'1',identity:command.identity,request_sha256:createHash('sha256').update(raw).digest('hex'),
          reference:{scope,curation_id:'curation-'+createHash('sha256').update(JSON.stringify(command.identity)).digest('hex')},
          revision:0,phase:'queued',reason_code:null,created_at:'2026-10-12T00:00:00Z',updated_at:'2026-10-12T00:00:00Z'};
      }
      if(mode==='lost')return send({error:'temporarily_unavailable'},503);
      return send(ack);
    }
    if(path==='/api/planning/v1/campaign-curations/receipts/query'){
      assert.equal(request.method,'POST');assert.deepEqual(JSON.parse(raw),{identity:ack.identity,request_sha256:ack.request_sha256});return send(ack);
    }
    if(ack&&path==='/api/planning/v1/campaign-curations/'+ack.reference.curation_id)return send({wire_version:'1',receipt:ack,specification:JSON.parse(original).payload,provider:null,proposal:null,capability_requests:[],validated_draft:null});
    if(path==='/app.js'||path==='/app.css'){response.setHeader('Content-Type',path.endsWith('js')?'text/javascript':'text/css');return response.end(await readFile(resolve(output,path.slice(1))));}
    if(path==='/favicon.ico'){response.writeHead(204);return response.end();}
    if(path==='/'){response.setHeader('Content-Type','text/html');return response.end('<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Curation request fixture</title><link rel="stylesheet" href="/app.css"></head><body><div id="root"></div><script type="module" src="/app.js"></script></body></html>');}
    unexpected.push(path);send({},404);
  }catch(error){errors.push(error.message);response.writeHead(500);response.end('fixture failure');}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const browser=await chromium.launch({headless:true});
const evidence={profile:'scripted-public-peers',states:[],screenshots:[],requests};
try{
  const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'}),page=await context.newPage();
  page.on('pageerror',error=>errors.push(error.message));const url=`http://127.0.0.1:${server.address().port}`;
  mode='running';await page.goto(url);await page.getByText('This campaign is still active. Prepare its revision after execution finishes.').waitFor();
  assert.equal(await page.getByRole('button',{name:'Request graph revision'}).isDisabled(),true);assert.equal(original,null);evidence.states.push('running-blocked');
  mode='ready';await page.getByRole('button',{name:'Refresh campaign context'}).click();
  await page.getByText(/Original campaign definition/).waitFor();
  await page.getByLabel('What should the next campaign investigate?').fill('Compare α polymer mixtures, then heat and add a third component. 🧪 Keep the original evidence.');
  for(const width of [1440,390]){
    await page.setViewportSize({width,height:width===390?844:1000});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    assert.deepEqual((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations.map(item=>item.id),[]);
    const name=`request-${width}.png`;await page.screenshot({path:resolve(output,name),fullPage:true});evidence.screenshots.push(name);
  }
  mode='lost';await page.getByRole('button',{name:'Request graph revision'}).click();
  await page.getByText('Confirmation is unavailable. Check the original request before trying again.').waitFor();evidence.states.push('lost-acknowledgement');
  const posts=()=>requests.filter(([method,path])=>method==='POST'&&path==='/api/planning/v1/campaign-curations').length;
  assert.equal(posts(),1);mode='ready';await page.reload();
  await page.getByRole('button',{name:'Review model proposal'}).waitFor();assert.equal(posts(),1);evidence.states.push('reload-exact-query-no-new-call');
  await page.getByRole('button',{name:'Review model proposal'}).click();await page.getByText('Awaiting a retained proposal',{exact:true}).waitFor();evidence.states.push('accepted-not-model-result');
  await page.getByRole('button',{name:'Back to next iteration'}).click();await page.getByRole('button',{name:'Review model proposal'}).waitFor();assert.equal(posts(),1);
  assert.deepEqual(errors,[]);assert.deepEqual(unexpected,[]);
  await writeFile(resolve(output,'evidence.json'),JSON.stringify(evidence,null,2));console.log(JSON.stringify({passed:true,output,states:evidence.states}));
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
