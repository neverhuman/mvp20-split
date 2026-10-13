/** Actual retained scientific proposal -> managed successor; no model request or fixture graph. */
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
const input=JSON.parse(await readFile(process.argv[2],'utf8')),output=resolve(process.argv[3]);
await mkdir(output,{recursive:true});
const browser=await chromium.launch({headless:true,args:input.tls_spki?['--ignore-certificate-errors-spki-list='+input.tls_spki]:[]});
const evidence={status:'running',requests:[],screenshots:[],errors:[],receipts:[]};let page;
try{
 const context=await browser.newContext({viewport:{width:1440,height:1100},reducedMotion:'reduce'});
 await context.addInitScript(entries=>{for(const [key,value] of entries)if(localStorage.getItem(key)===null)localStorage.setItem(key,value);},input.recovery);
 page=await context.newPage();page.on('pageerror',e=>evidence.errors.push(e.message));
 page.on('request',r=>{if(r.method()==='POST'&&[/\/v1\/campaign-successor-launches$/,/\/v1\/campaign-curations$/,/\/v1\/campaign-launches$/].some(p=>p.test(r.url())))evidence.requests.push({url:r.url(),body:r.postData()});});
 page.on('response',async r=>{try{if(r.ok()&&r.url().includes('/api/deployment/v1/campaign-successor-launches')){const receipt=await r.json();evidence.receipts.push(receipt);await writeFile(resolve(output,'latest-launch.json'),JSON.stringify(receipt,null,2));}}catch{}});
 const issued=await context.request.post(input.origin+'/launcher/ticket',{headers:{Authorization:'Bearer '+process.env.AMPHORA_BROWSER_LAUNCH_KEY}});
 assert.equal(issued.status(),200);const {ticket}=await issued.json();
 evidence.assets={};
 for(const [name,expected] of Object.entries(input.expected_assets??{})){
  assert.ok(['index.html','app.js','app.css'].includes(name));
  const response=await context.request.get(input.origin+(name==='index.html'?'/':'/'+name));
  assert.equal(response.status(),200);const sha=createHash('sha256').update(await response.body()).digest('hex');
  assert.equal(sha,expected,'Actual served asset differs: '+name);evidence.assets[name]=sha;
 }
 await page.goto(input.origin+'/#view=curation&curation='+input.curation_id+'&launch='+ticket);
 await page.getByRole('heading',{name:'How would the next campaign change?',exact:true}).waitFor({timeout:60000});
 const read=await context.request.get(input.origin+'/api/planning/v1/campaign-curations/'+input.curation_id);
 assert.equal(read.status(),200);const record=await read.json();assert.equal(record.receipt.phase,'ready');
 assert.equal(record.proposal.outcome.kind,'propose_campaign');
 evidence.curation=record;assert.equal(record.specification.context.artifacts.length,4);
 const nodes=record.proposal.outcome.candidate.definition.body.nodes;
 assert.equal(nodes.filter(n=>n.kind==='invoke').length,4);
 await page.getByRole('button',{name:'Proposed campaign',exact:true}).click();
 async function capture(name,graph=false){
  for(const width of [1440,390]){
   await page.setViewportSize({width,height:width===390?844:1100});
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);
   if(graph)await page.waitForFunction(()=>{
    const canvas=document.querySelector('.react-flow');if(!canvas)return false;const bounds=canvas.getBoundingClientRect();
    const nodes=[...canvas.querySelectorAll('.react-flow__node')];if(!nodes.length||!nodes[0].offsetWidth)return false;
    const boxes=nodes.map(node=>node.getBoundingClientRect()),zoom=boxes[0].width/nodes[0].offsetWidth;
    if(zoom<=0)return false;
    const left=Math.min(...boxes.map(b=>b.left)),right=Math.max(...boxes.map(b=>b.right));
    const top=Math.min(...boxes.map(b=>b.top)),bottom=Math.max(...boxes.map(b=>b.bottom));
    const ideal=Math.max(.05,Math.min(1,bounds.width/((right-left)/zoom*1.24),bounds.height/((bottom-top)/zoom*1.24)));
    return canvas.querySelectorAll('.react-flow__edge-path').length>0&&zoom>=ideal*.9&&
     left>=bounds.left-1&&right<=bounds.right+1&&top>=bounds.top-1&&bottom<=bounds.bottom+1;
   });
   const issues=(await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations;
   assert.deepEqual(issues.filter(x=>['serious','critical'].includes(x.impact)).map(x=>x.id),[]);
   const file=name+'-'+width+'.png';await page.screenshot({path:resolve(output,file),fullPage:true});evidence.screenshots.push(file);
  }
 }
 await capture('proposed-scientific-graph',true);
 if(!input.review_only){
  const launch=page.getByRole('button',{name:'Run this revised campaign',exact:true});
  await page.waitForFunction(()=>[...document.querySelectorAll('button')].some(b=>b.textContent==='Run this revised campaign'&&!b.disabled),{},{timeout:60000});
  await launch.click();
 }
 await page.getByRole('button',{name:'Open new campaign',exact:true}).waitFor({timeout:90000});
 await page.getByRole('button',{name:'Open new campaign',exact:true}).click();
 const until=Date.now()+120000;let receipt;
 do{receipt=evidence.receipts.find(r=>r.run_id);if(receipt)break;await page.waitForTimeout(100);}while(Date.now()<until);
 assert.ok(receipt?.run_id);evidence.run_id=receipt.run_id;
 await writeFile(resolve(output,'browser-recovery.json'),JSON.stringify(await page.evaluate(()=>Object.entries(localStorage).filter(([key])=>key.startsWith('amphora.'))),null,2));
 await page.waitForFunction(()=>document.body.textContent.includes('Retained plan / completed execution')||document.body.textContent.includes('Execution complete'),{},{timeout:180000});
 await capture('completed-scientific-successor',true);
 const results=page.getByRole('button',{name:/Results and evidence/});
 assert.equal(await results.count(),1,'Scientific successor must preserve its research flow');await results.click();
 await page.getByRole('heading',{name:'Compare evidence, not just scores',exact:true}).waitFor();
 const table=await page.locator('.flow-table').innerText();assert.match(table,/inside/);assert.match(table,/outside/);assert.match(table,/Pa.s/);
 evidence.results=table;await capture('scientific-successor-results');
 if(input.expect_no_structure){
  await page.getByText('No supported chemical structure output was found.',{exact:false}).waitFor();
  assert.equal(await page.locator('.candidate-inspector img').count(),0);
 }
 await page.getByRole('button',{name:/Knowledge graph/}).click();
 await page.getByRole('heading',{name:'Follow the evidence',exact:true}).waitFor();
 await page.getByRole('button',{name:'Hansen solvency screen',exact:true}).first().click();
 await page.getByRole('heading',{name:'Connected knowledge',exact:true}).waitFor();await capture('selected-knowledge',true);
 await page.getByRole('button',{name:/Next iteration/}).click();
 await page.getByLabel('What should the next campaign investigate?').fill('Review the evidence for a future screening iteration.');
 await page.waitForFunction(()=>[...document.querySelectorAll('button')].some(b=>b.textContent==='Request graph revision'&&!b.disabled));
 assert.match(await page.locator('.curation-composer').innerText(),/4 input artifacts/);await capture('successor-next-context');
 await page.goto(input.origin+'/#view=curation&curation='+input.curation_id);await page.reload();
 await page.getByRole('button',{name:'Open new campaign',exact:true}).waitFor({timeout:60000});
 const launchPosts=evidence.requests.filter(r=>r.url.endsWith('/v1/campaign-successor-launches'));
 assert.equal(launchPosts.length,input.review_only?0:1);
 assert.equal(evidence.requests.filter(r=>!r.url.endsWith('/v1/campaign-successor-launches')).length,0);
 assert.deepEqual(evidence.errors,[]);evidence.status='passed';
}catch(error){evidence.error=String(error);if(page){await writeFile(resolve(output,'failure.txt'),await page.locator('body').innerText());await page.screenshot({path:resolve(output,'failure.png'),fullPage:true});}throw error;}
finally{await browser.close();await writeFile(resolve(output,'evidence.json'),JSON.stringify(evidence,null,2));}
console.log('Actual scientific successor journey passed');
