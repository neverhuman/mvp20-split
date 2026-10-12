import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {build} from 'esbuild';
import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import {graphFixture} from '../../dist/tests/page_models/campaign_curation/graph_fixture.js';
import {CurationSubmission} from '../../dist/src/transport/campaign_curation/submission.js';
import {SuccessorSubmission} from '../../dist/src/transport/successor_launch/submission.js';
const output=resolve(process.argv[2]??'../.test-results/successor-browser-'+Date.now());await mkdir(output,{recursive:true});
await build({entryPoints:['tests/browser/successor_entry.tsx'],bundle:true,format:'esm',jsx:'automatic',outfile:resolve(output,'app.js')});
const f=graphFixture(),curation=await CurationSubmission.create({encoding:'amphora-command-v2',identity:f.curation.receipt.identity,payload:f.curation.specification});
f.curation.receipt.reference=curation.selection.reference;f.curation.receipt.request_sha256=curation.sha256;
f.curation.provider.attempt.engagement.engagement_id='curation-call-'+curation.sha256;f.selection=curation.selection;
const sources={scope:f.scope,predecessor:f.curation.specification.context.predecessor,predecessor_ready:true,sources:[]};
const catalog={scope:f.scope,profiles:[{scope:f.scope,title:'Reviewed synthetic heating tools',reference:{profile_id:'local',version:'1',sha256:'8'.repeat(64)},
  maximum_invocations:8,maximum_deadline_seconds:300,tools:[f.proposed.definition.body.nodes[0].tool]}]};
const storageKey='amphora.curation.v1:'+JSON.stringify([f.scope.tenant_id,f.scope.project_id,f.selection.actor,f.selection.predecessor]);
let launch=null,posts=0,mode='ready';const requests=[],errors=[],intents=[];
const server=createServer(async(request,response)=>{
  try{
    const path=new URL(request.url,'http://localhost').pathname;requests.push([request.method,path]);
    const send=(value,status=200)=>{response.writeHead(status,{'Content-Type':'application/json'});response.end(JSON.stringify(value));};
    if(path==='/binding')return send({selection:f.selection,storageKey,body:curation.body});
    if(path.startsWith('/api/planning/v1/campaign-curations/'))return send(f.curation);
    if(path.startsWith('/api/runtime/v1/definition-drafts/'))return send(path.endsWith('/proposed-draft')?f.saved:f.original);
    if(path==='/api/runtime/v1/definition-validations/validation')return send(f.validation);
    if(path.endsWith('/carry-sources'))return send(mode==='changed'?{...sources,predecessor:{...sources.predecessor,revision:99}}:sources);
    if(path==='/api/deployment/v1/campaign-launch-profiles')return send(mode==='unsupported'?{...catalog,profiles:catalog.profiles.map(profile=>({...profile,tools:[{...profile.tools[0],release:'2.0.0'}]}))}:catalog);
    if(path==='/api/deployment/v1/campaign-successor-launches'&&request.method==='POST'){
      const parts=[];for await(const part of request)parts.push(part);const body=Buffer.concat(parts).toString('utf8'),command=SuccessorSubmission.restore(body);posts++;intents.push(body);
      assert.deepEqual(command.request.payload.admission.payload.draft,f.curation.validated_draft);
      assert.deepEqual(command.request.payload.admission.payload.predecessor,sources.predecessor);
      const value=command.request;
      launch={profile_kind:'campaign-successor-launch.v1',identity:value.identity,request_sha256:'7'.repeat(64),profile:value.payload.profile,predecessor:sources.predecessor,
        revision:4,phase:'engaged',reason_code:null,created_at:'2026-10-12T08:00:00Z',updated_at:'2026-10-12T08:01:00Z',run_id:'successor-run',workers:{expected:1,ready:1},
        admission:{outcome:{status:'accepted',binding:{identity:value.payload.admission.identity,operation_id:'admission',request_sha256:'6'.repeat(64)},committed:{kind:'run',object_id:'successor-run',revision:0}}}};
      // Owner committed; gateway cannot return the acknowledgment. Browser socket resets may retry at its own HTTP layer.
      if(mode==='lost')return send({reason_code:'launch_unavailable'},502);
      if(mode==='socket'){response.destroy();return;}return send(launch,202);
    }
    if(path.startsWith('/api/deployment/v1/campaign-successor-launches/')){
      if(!launch)return send({reason_code:'launch_receipt_unavailable'},404);
      if(request.method==='POST'){const parts=[];for await(const part of request)parts.push(part);const query=JSON.parse(Buffer.concat(parts));assert.equal(query.request_sha256,launch.request_sha256);}
      return send(launch);
    }
    if(path==='/app.js'||path==='/app.css'){response.setHeader('Content-Type',path.endsWith('js')?'text/javascript':'text/css');return response.end(await readFile(resolve(output,path.slice(1))));}
    if(path==='/favicon.ico'){response.writeHead(204);return response.end();}
    if(path==='/'){response.setHeader('Content-Type','text/html');return response.end('<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Successor fixture</title><link rel="stylesheet" href="/app.css"></head><body><div id="root"></div><script type="module" src="/app.js"></script></body></html>');}
    throw Error('unexpected route '+path);
  }catch(error){errors.push(error.message);response.writeHead(500);response.end('fixture failure');}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const browser=await chromium.launch({headless:true});
const evidence={profile:'scripted-public-peers',screenshots:[],states:[],requests};
try{
  const context=await browser.newContext({viewport:{width:1440,height:1100},reducedMotion:'reduce'}),page=await context.newPage();
  page.on('pageerror',error=>errors.push(error.message));const url=`http://127.0.0.1:${server.address().port}`;
  await page.goto(url);const button=page.getByRole('button',{name:'Run this revised campaign',exact:true});await button.waitFor();
  await page.waitForFunction(()=>[...document.querySelectorAll('button')].some(button=>button.textContent==='Run this revised campaign'&&!button.disabled));
  for(const width of [1440,390]){
    await page.setViewportSize({width,height:width===390?844:1100});await button.scrollIntoViewIfNeeded();
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    const issues=(await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations;assert.deepEqual(issues.map(item=>item.id),[]);
    const name=`successor-${width}.png`;await page.screenshot({path:resolve(output,name),fullPage:true});evidence.screenshots.push(name);
  }
  mode='lost';await button.click();await page.waitForFunction(()=>localStorage.length>=3);await page.reload();
  await page.getByRole('button',{name:'Open new campaign',exact:true}).waitFor();assert.equal(posts,1);
  await page.getByRole('button',{name:'Open new campaign',exact:true}).click();await page.getByRole('heading',{name:'Opened successor successor-run'}).waitFor();evidence.states.push('lost-reply-reload-open-successor');
  await page.reload();await page.getByRole('button',{name:'Prepare another revision request'}).click();
  await page.getByRole('heading',{name:'Ready for a different research direction'}).waitFor();assert.equal(posts,1);evidence.states.push('explicit-next-request-no-post');
  for(const state of ['changed','unsupported']){
    mode=state;await page.evaluate(()=>localStorage.clear());await page.goto(url);
    await page.getByText(state==='changed'?'The predecessor changed after this proposal was requested. Prepare a new revision from its current state.':
      'No installed profile supports every tool in this proposal. The graph remains available for review.',{exact:true}).waitFor();
    assert.equal(await button.isDisabled(),true);evidence.states.push(state);
  }
  assert.equal(posts,1);evidence.gatewayFailureIntakePosts=posts;
  mode='socket';await page.evaluate(()=>localStorage.clear());await page.goto(url);
  await page.waitForFunction(()=>[...document.querySelectorAll('button')].some(button=>button.textContent==='Run this revised campaign'&&!button.disabled));
  const start=intents.length;await button.click();
  await page.getByRole('button',{name:'Open new campaign',exact:true}).waitFor();
  assert.ok(intents.length>start);assert.equal(new Set(intents.slice(start)).size,1);
  evidence.socketResetPhysicalPosts=intents.length-start;evidence.socketResetDistinctIntents=1;evidence.states.push('socket-reset-original-intent-preserved');
  assert.deepEqual(errors,[]);
  await writeFile(resolve(output,'evidence.json'),JSON.stringify(evidence,null,2));console.log(JSON.stringify({passed:true,output,states:evidence.states,posts}));
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
