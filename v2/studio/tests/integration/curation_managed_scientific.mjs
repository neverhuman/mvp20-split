/** Actual managed model request against the scientific demo; one original intent. */
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve} from 'node:path';
import {chromium} from 'playwright';
const input=JSON.parse(await readFile(process.argv[2],'utf8')),output=resolve(process.argv[3]);
await mkdir(output,{recursive:true});
const browser=await chromium.launch({headless:true});let page;
const evidence={status:'running',requests:[],errors:[],scope:'managed scientific curation; synthetic only'};
try{
 const context=await browser.newContext({viewport:{width:1440,height:1100},reducedMotion:'reduce'});
 await context.addInitScript(entries=>{for(const [key,value] of entries)localStorage.setItem(key,value);},input.recovery);
 page=await context.newPage();page.on('pageerror',e=>evidence.errors.push(e.message));
 page.on('request',request=>{if(request.method()==='POST'&&request.url().endsWith('/v1/campaign-curations'))evidence.requests.push(JSON.parse(request.postData()));});
 const issued=await context.request.post(input.origin+'/launcher/ticket',{headers:{Authorization:'Bearer '+process.env.AMPHORA_BROWSER_LAUNCH_KEY}});
 assert.equal(issued.status(),200);const {ticket}=await issued.json();
 await page.goto(input.origin+'/#view=execution&launch='+ticket);
 await page.getByText('Retained plan / completed execution',{exact:false}).waitFor({timeout:60000});
 await page.getByRole('button',{name:/Next iteration/}).click();
 await page.getByLabel('What should the next campaign investigate?').fill(input.direction);
 await page.waitForFunction(()=>[...document.querySelectorAll('button')].some(b=>b.textContent==='Request graph revision'&&!b.disabled),{},{timeout:60000});
 const summary=await page.locator('.curation-composer').innerText();
 assert.match(summary,/1 Knowledge revisions/);assert.match(summary,/1 research questions/);
 await page.screenshot({path:resolve(output,'requested-context.png'),fullPage:true});
 const receiptPromise=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/v1/campaign-curations'));
 await page.getByRole('button',{name:'Request graph revision',exact:true}).click();
 const response=await receiptPromise;assert.ok([200,202].includes(response.status()));
 const receipt=await response.json();evidence.receipt=receipt;
 await writeFile(resolve(output,'original-receipt.json'),JSON.stringify(receipt,null,2));
 await writeFile(resolve(output,'browser-recovery.json'),JSON.stringify(await page.evaluate(()=>Object.entries(localStorage).filter(([key])=>key.startsWith('amphora.'))),null,2));
 await page.getByRole('button',{name:'Review model proposal',exact:true}).click();
 let record;
 const deadline=Date.now()+360000;
 do{
  const read=await context.request.get(input.origin+'/api/planning/v1/campaign-curations/'+receipt.reference.curation_id);
  assert.equal(read.status(),200);record=await read.json();
  await writeFile(resolve(output,'current-record.json'),JSON.stringify(record,null,2));
  if(['ready','failed','abstained','indeterminate'].includes(record.receipt.phase))break;
  await page.waitForTimeout(1000);
 }while(Date.now()<deadline);
 evidence.phase=record.receipt.phase;
 await page.getByRole('button',{name:'Refresh record',exact:true}).click();
 await page.waitForTimeout(500);
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:width===390?844:1100});
  await page.screenshot({path:resolve(output,'proposal-'+width+'.png'),fullPage:true});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);
 }
 assert.equal(evidence.requests.length,1);assert.equal(evidence.requests[0].payload.context.knowledge.length,1);
 assert.equal(evidence.requests[0].payload.context.questions.length,1);assert.deepEqual(evidence.errors,[]);
 assert.equal(record.receipt.phase,'ready','Actual model outcome retained; do not retry automatically');
 await page.reload();await page.getByRole('heading',{name:'How would the next campaign change?',exact:true}).waitFor();
 assert.equal(evidence.requests.length,1);evidence.status='passed';
}catch(error){evidence.error=String(error);if(page){await writeFile(resolve(output,'failure.txt'),await page.locator('body').innerText());await page.screenshot({path:resolve(output,'failure.png'),fullPage:true});}throw error;}
finally{await browser.close();await writeFile(resolve(output,'evidence.json'),JSON.stringify(evidence,null,2));}
console.log('Managed scientific curation browser passed');
