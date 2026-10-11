/** Built entry with scripted public peers. Actual owners/workers are the separate L4 gate. */
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {createHash} from 'node:crypto';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import {revision,accepted,scope} from '../../dist/tests/fixtures/authoring.js';
import {snapshot,detail} from '../../dist/tests/fixtures/observations.js';
import {topology} from '../../dist/tests/fixtures/navigation.js';
import {profile,receipt} from '../../dist/tests/fixtures/launch.js';
import {LaunchSubmission} from '../../dist/src/transport/launch/submission.js';
import {polymerProposal} from '../../dist/src/page_models/evaluation_review/polymer_proposal.js';
import {contextSchema} from '../../dist/src/page_models/campaign_flow/schema_pin.js';
const output=resolve(process.argv[2]??'../.test-results/launch-browser-'+Date.now());await mkdir(output,{recursive:true});
const draft=revision(),tool={capability_id:'materials.hansen-solvency',release:'0.1.0',contract_version:'1',image_sha256:'a'.repeat(64)};
const context={format:'amphora.demo-campaign-context.v1',scope,design:polymerProposal(),bindings:[{method_id:'solvency',node_id:'node-1',candidate_id:'fixture-A',tool}],limitations:['Scripted browser fixture; no actual calculation.']};
const bytes=Buffer.from(JSON.stringify(context)),artifact={scope,artifact_id:'launch-plan',schema_ref:contextSchema,sha256:createHash('sha256').update(bytes).digest('hex'),size_bytes:bytes.length,media_type:'application/json'};
draft.definition.body.nodes=[{kind:'invoke',node_id:'node-1',tool,inputs:[],timeout_seconds:60},{kind:'finish',node_id:'node-2',outputs:[{port:'campaign_context',source:{kind:'artifact',artifact,representation:'campaign-review-context',unit:'1'}}]}];
draft.definition.body.edges=[{source:'node-1',target:'node-2',route:'next'}];
const validation={scope,draft_id:'draft',revision:1,content_sha256:draft.head.content_sha256,validation_id:'checked',universe_sha256:'c'.repeat(64),structurally_valid:true,plan_sha256:'a'.repeat(64),findings:[],pending_checks:['activation'],scientific_acceptance:'not_established'};
let saved,posts=0,complete=false,reads=0,changedCut=false,cutConflicts=0;
const pageWire=()=>{const p=snapshot({run:'actual-run'});p.snapshot.cut.scope=scope;p.nodes[1].kind='finish';if(complete){p.snapshot.status='completed';p.nodes.forEach(n=>n.status='succeeded');}return p;};
const server=createServer(async(req,res)=>{
 try{
  const path=new URL(req.url,'http://localhost').pathname;let body='';for await(const chunk of req)body+=chunk;
  const send=(value,status=200)=>{res.writeHead(status,{'Content-Type':'application/json'});res.end(JSON.stringify(value));};
  if(path==='/session')return send({actor_id:'researcher',scope,run_id:null,synthetic:true});
  if(path==='/api/deployment/v1/campaign-launch-profiles')return send({scope,profiles:[{reference:profile,scope,title:'Synthetic installed science',tools:[tool],maximum_invocations:8,maximum_deadline_seconds:300}]});
  if(path==='/api/runtime/v1/definition-drafts')return send({scope,drafts:[draft.head],next_after:null});
  if(path==='/api/runtime/v1/definition-drafts/draft')return send(draft);
  if(path==='/api/planning/v1/campaign-origins/draft')return send({reason_code:'campaign_origin_not_recorded'},404);
  if(path==='/api/runtime/v1/definition-drafts/validate'){const command=JSON.parse(body);return send(accepted({identity:command.identity},validation));}
  if(path==='/api/runtime/v1/definition-validations/checked')return send(validation);
  if(path==='/api/deployment/v1/campaign-launches'){posts++;const command=LaunchSubmission.restore(body);saved=receipt(command,true);saved.phase='engaged';saved.workers={expected:2,ready:2};return send(saved,202);}
  if(path.startsWith('/api/deployment/v1/campaign-launches/')){reads++;return send(saved??{},saved?200:404);}
  if(path==='/api/data/v1/artifacts/launch-plan')return send(artifact);
  if(path==='/api/data/v1/artifacts/launch-plan/content'){res.writeHead(200,{'Content-Type':'application/json','Content-Length':bytes.length});return res.end(bytes);}
  if(path==='/api/runtime/v1/graph-observations/actual-run/nodes')return send(pageWire());
  if(path.includes('/graph-observations/actual-run/nodes/')){if(changedCut){changedCut=false;cutConflicts++;return send({reason_code:'snapshot_changed'},409);}const index=Number.parseInt(path.split('/').at(-1),16),d=detail(index);d.cut=pageWire().snapshot.cut;d.node=pageWire().nodes[index-1];if(complete&&index===2)d.outputs=[{port:'campaign_context',kind:'artifact',item_count:1,missing_count:0,artifact}];return send(d);}
  if(path.endsWith('/topology')){const t=topology();t.cut=pageWire().snapshot.cut;t.nodes.forEach((n,i)=>n.activation=pageWire().nodes[i]);return send(t);}
  if(path.startsWith('/api/'))return send({},404);
  const name=path==='/'?'index.html':path.slice(1);if(!['index.html','app.js','app.css'].includes(name))return send({},404);
  res.writeHead(200,{'Content-Type':name.endsWith('.js')?'text/javascript':name.endsWith('.css')?'text/css':'text/html'});res.end(await readFile(resolve('dist/local',name)));
 }catch(error){res.writeHead(500);res.end('fixture failure');console.error(error);}
});
await new Promise(done=>server.listen(0,'127.0.0.1',done));const url='http://127.0.0.1:'+server.address().port;
const browser=await chromium.launch({headless:true});const errors=[];
const evidence={status:'running',checked_at:new Intl.DateTimeFormat('sv-SE',{timeZone:'America/Chicago',dateStyle:'short',timeStyle:'medium'}).format(new Date()),limits:['Scripted public peers; no live worker or science claim.'],screenshots:[]};
try{
 const browserContext=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
 const page=await browserContext.newPage();page.on('pageerror',error=>errors.push(error.message));
 await page.goto(url+'/#view=execution');await page.getByLabel('Saved campaign').selectOption('draft');
 assert.equal(await page.getByRole('button',{name:'Run campaign',exact:true}).isEnabled(),false);
 await page.getByRole('button',{name:'Check saved revision',exact:true}).click();
 for(const width of [1440,390]){await page.setViewportSize({width,height:width===390?844:1000});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  const name='ready-'+width+'.png';await page.screenshot({path:resolve(output,name),fullPage:true});evidence.screenshots.push(name);
 }
 await page.setViewportSize({width:1440,height:1000});
 await page.getByRole('button',{name:'Run campaign',exact:true}).click();
 await page.getByText('Pinned launch plan /',{exact:false}).waitFor();
 await page.getByRole('heading',{name:'Follow the planned work',exact:true}).waitFor();
 assert.equal(posts,1);await page.locator('.react-flow__edge').first().waitFor();
 for(const width of [1440,390]){await page.setViewportSize({width,height:width===390?844:1000});
  await page.getByRole('button',{name:'Fit graph',exact:true}).click();
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  const name='running-'+width+'.png';await page.screenshot({path:resolve(output,name),fullPage:true});evidence.screenshots.push(name);
  const axe=await new AxeBuilder({page}).analyze();assert.equal(axe.violations.filter(v=>['serious','critical'].includes(v.impact)).length,0);
 }
 await page.getByRole('button',{name:'2. Evaluation design',exact:true}).click();
 await page.getByText('Why this campaign?',{exact:false}).click();
 await page.getByText('No Planning origin is recorded for this exact draft.',{exact:false}).waitFor();
 evidence.missing_origin_displayed=true;assert.equal(posts,1);
 await page.getByRole('button',{name:'3. Approach and run',exact:true}).click();
 await page.reload();await page.getByRole('heading',{name:'Follow the planned work',exact:true}).waitFor();assert.equal(posts,1);assert.ok(reads>0);
 complete=true;changedCut=true;await page.getByText('Retained plan / completed execution',{exact:false}).waitFor({timeout:10000});
 assert.equal(cutConflicts,1);assert.equal(posts,1);assert.deepEqual(errors,[]);evidence.status='passed';evidence.launch_posts=posts;evidence.receipt_reads=reads;evidence.recovered_snapshot_conflicts=cutConflicts;
}catch(error){evidence.error=String(error);evidence.browser_errors=errors;const pages=browser.contexts().flatMap(c=>c.pages());if(pages[0]){await writeFile(resolve(output,'failure.txt'),await pages[0].locator('body').innerText());await pages[0].screenshot({path:resolve(output,'failure.png'),fullPage:true});}throw error;}
finally{await browser.close();await new Promise(done=>server.close(done));await writeFile(resolve(output,'evidence.json'),JSON.stringify(evidence,null,2));}
console.log('Launch browser fixture passed:',output);
