/** Actual installed Runtime/Data/Gateway; retained campaign only, zero mutations. */
import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const input=JSON.parse(await readFile(process.argv[2],'utf8')),output=resolve(process.argv[3]);await mkdir(output,{recursive:true});
const browser=await chromium.launch({headless:true});
const evidence={status:'running',timestamp_local:new Intl.DateTimeFormat('sv-SE',{timeZone:'America/Chicago',dateStyle:'short',timeStyle:'medium'}).format(new Date()),run_id:input.run_id,scope:input.scope,errors:[],mutations:[],artifacts:[]};let context;
try{
 context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});const page=await context.newPage();
 page.on('pageerror',e=>evidence.errors.push(e.message));page.on('request',r=>{if(r.method()!=='GET'&&r.url().includes('/api/'))evidence.mutations.push([r.method(),r.url()]);});
 page.on('response',async r=>{try{if(r.ok()&&r.url().includes('/api/data/v1/artifacts/')&&!r.url().endsWith('/content'))evidence.artifacts.push(await r.json());}catch{}});
 const issued=await context.request.post(input.origin+'/launcher/ticket',{headers:{Authorization:'Bearer '+process.env.AMPHORA_BROWSER_LAUNCH_KEY}});assert.equal(issued.status(),200);const {ticket}=await issued.json();
 await page.goto(input.origin+'/#view=knowledge&launch='+encodeURIComponent(ticket));
 const a=page.getByLabel('Checkpoint A',{exact:true}),b=page.getByLabel('Checkpoint B',{exact:true});await a.waitFor({timeout:60000});
 const options=await a.locator('option').evaluateAll(rows=>rows.map(r=>({value:r.value,text:r.textContent})));
 const first=options.find(o=>/^\d+\. collect \/ result$/.test(o.text));
 const later=options.find(o=>/^\d+\. finish \/ result$/.test(o.text));
 evidence.options=options.map(o=>o.text);assert.ok(first&&later,'Expected actual retained selected-generation outputs');
 await a.selectOption(first.value);await b.selectOption(later.value);await page.getByRole('heading',{name:'Objective comparison',exact:true}).waitFor({timeout:30000});
 assert.equal(await page.getByText('Same pinned search specification, different completed generations.',{exact:false}).count(),1);
 evidence.comparison=await page.locator('.generation-comparison').innerText();
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:1000});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  const issues=(await new AxeBuilder({page}).include('.generation-comparison').withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations;assert.deepEqual(issues.map(v=>v.id),[]);
  await page.screenshot({path:resolve(output,'actual-'+width+'.png'),fullPage:true});
 }
 assert.deepEqual(evidence.mutations,[]);assert.deepEqual(evidence.errors,[]);evidence.status='passed';console.log('Actual generation comparison passed: '+output);
}catch(e){evidence.status='failed';evidence.failure=String(e);throw e;}
finally{if(context)await context.request.post(input.origin+'/session/logout').catch(()=>undefined);await writeFile(resolve(output,'evidence.json'),JSON.stringify(evidence,null,2));await browser.close();}
