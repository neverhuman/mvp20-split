/** Actual browser -> Deployment -> Runtime -> managed scientific workers; no mocked route. */
import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const input=JSON.parse(await readFile(process.argv[2],'utf8')),output=resolve(process.argv[3]);
const reviewOnly=process.argv[5]==='--review-only';
assert.ok(!reviewOnly||process.argv[4],'Read-only recovery requires the original browser record');
await mkdir(output,{recursive:true});
if(input.tls_spki)assert.match(input.tls_spki,/^[A-Za-z0-9+/]{43}=$/);
const browser=await chromium.launch({headless:true,args:input.tls_spki?['--ignore-certificate-errors-spki-list='+input.tls_spki]:[]});let page;
const evidence={status:'running',timestamp_local:new Intl.DateTimeFormat('sv-SE',{timeZone:'America/Chicago',dateStyle:'short',timeStyle:'medium'}).format(new Date()),errors:[],launch_posts:[],receipts:[],checks:[]};
try{
 const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
 page=await context.newPage();page.on('pageerror',error=>evidence.errors.push(error.message));
 page.on('request',request=>{if(request.method()==='POST'&&request.url().endsWith('/v1/campaign-launches'))evidence.launch_posts.push(JSON.parse(request.postData()));});
 page.on('response',async response=>{try{if(response.url().includes('/api/deployment/v1/campaign-launches')&&response.ok()){const receipt=await response.json();evidence.receipts.push(receipt);await writeFile(resolve(output,'latest-launch.json'),JSON.stringify(receipt,null,2));}}catch{}});
 const issued=await context.request.post(input.origin+'/launcher/ticket',{headers:{Authorization:'Bearer '+process.env.AMPHORA_BROWSER_LAUNCH_KEY}});
 assert.equal(issued.status(),200);const {ticket}=await issued.json();
 if(process.argv[4]){
  const recovered=JSON.parse(await readFile(process.argv[4],'utf8'));
  await context.addInitScript(({origin,entries})=>{if(location.origin===origin)for(const [key,value] of entries)localStorage.setItem(key,value);},{origin:input.origin,entries:recovered});
 }
 await page.goto(input.origin+'/#view=execution&launch='+encodeURIComponent(ticket));
 if(!process.argv[4]){
  await page.getByLabel('Saved campaign').selectOption(input.draft_id);
  await page.getByRole('button',{name:'Check saved revision',exact:true}).click();
  await page.waitForFunction(()=>{const b=[...document.querySelectorAll('button')].find(b=>b.textContent==='Run campaign');return b&&!b.disabled;},{},{timeout:30000});
  await page.screenshot({path:resolve(output,'ready-to-run.png'),fullPage:true});
  await page.getByRole('button',{name:'Run campaign',exact:true}).click();
 }else if(!reviewOnly){
  await page.getByRole('button',{name:'Reconcile original campaign',exact:true}).click({timeout:60000});
 }
 await page.waitForFunction(()=>document.querySelector('.campaign-launch')?.textContent.includes('Campaign ')&&
   document.querySelector('.flow-context')?.textContent.toLowerCase().includes('pinned launch plan')||
   document.querySelector('.flow-context')?.textContent.toLowerCase().includes('retained plan / completed execution')||
   document.querySelector('.campaign-launch')?.textContent.includes('Launch rejected'),{},{timeout:60000});
 assert.ok(!evidence.receipts.some(row=>row.phase==='rejected'),'Actual launch was rejected; retained receipt explains the owner decision');
 assert.equal(evidence.launch_posts.length,reviewOnly?0:1);
 await writeFile(resolve(output,'browser-recovery.json'),JSON.stringify(await page.evaluate(()=>Object.entries(localStorage).filter(([key])=>key.startsWith('amphora.launch.v1:'))),null,2));
 await page.screenshot({path:resolve(output,'running.png'),fullPage:true});
 const admitted=evidence.receipts.find(row=>row.run_id);assert.ok(admitted);evidence.run_id=admitted.run_id;evidence.request_id=admitted.identity.command_id;
 await page.reload();
 await page.getByRole('heading',{name:'Follow the planned work',exact:true}).waitFor({timeout:60000});
 await page.getByText('Retained plan / completed execution',{exact:false}).waitFor({timeout:600000});
 await page.getByRole('button',{name:/Results and evidence/}).click();
 await page.getByRole('heading',{name:'Compare evidence, not just scores',exact:true}).waitFor();
 const table=await page.locator('.flow-table').innerText();assert.match(table,/inside/);assert.match(table,/outside/);assert.match(table,/Pa.s/);
 evidence.checks.push({name:'actual_scientific_results',table});
 for(const width of [1440,390]){await page.setViewportSize({width,height:width===390?844:1000});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.screenshot({path:resolve(output,'results-'+width+'.png'),fullPage:true});
  const axe=await new AxeBuilder({page}).analyze();assert.equal(axe.violations.filter(v=>['serious','critical'].includes(v.impact)).length,0);
 }
 assert.ok(evidence.receipts.every(row=>row.run_id===null||row.run_id===evidence.run_id));
 assert.equal(evidence.launch_posts.length,reviewOnly?0:1);if(!reviewOnly)assert.equal(evidence.launch_posts[0].identity.command_id,evidence.request_id);assert.deepEqual(evidence.errors,[]);evidence.status='passed';evidence.review_only=reviewOnly;
}finally{
 if(evidence.status!=='passed')evidence.status='failed';
 if(page){await writeFile(resolve(output,'browser-recovery.json'),JSON.stringify(await page.evaluate(()=>Object.entries(localStorage).filter(([key])=>key.startsWith('amphora.launch.v1:'))).catch(()=>[]),null,2));
  if(evidence.status!=='passed'){evidence.failure=await page.locator('body').innerText();await page.screenshot({path:resolve(output,'failure.png'),fullPage:true});}}
 await browser.close();await writeFile(resolve(output,'evidence.json'),JSON.stringify(evidence,null,2));
}
console.log('Actual browser campaign launch passed:',output);
