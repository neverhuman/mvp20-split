import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const input=JSON.parse(await readFile(process.argv[2],'utf8')),assets=resolve(process.argv[3]),output=resolve(process.argv[4]);
await mkdir(output,{recursive:true});const browser=await chromium.launch({headless:true});
const evidence={status:'running',errors:[],checks:[],writes:[]};let page;
try{
 const context=await browser.newContext({viewport:{width:1440,height:1100},reducedMotion:'reduce'});page=await context.newPage();
 page.on('pageerror',e=>evidence.errors.push(e.message));
 page.on('request',r=>{if(['POST','PUT','DELETE','PATCH'].includes(r.method())&&new URL(r.url()).pathname!=='/session'&&!r.url().includes('/session/')&&!r.url().includes('/launcher/'))evidence.writes.push(r.url());});
 for(const name of process.argv.includes('--served')?[]:['app.js','app.css'])await page.route(input.origin+'/'+name,async route=>route.fulfill({body:await readFile(resolve(assets,name)),contentType:name.endsWith('js')?'application/javascript':'text/css'}));
 const issued=await context.request.post(input.origin+'/launcher/ticket',{headers:{Authorization:'Bearer '+process.env.AMPHORA_BROWSER_LAUNCH_KEY}});assert.equal(issued.status(),200);
 const {ticket}=await issued.json();await page.goto(input.origin+'/#view=evaluation&launch='+encodeURIComponent(ticket));
 await page.getByRole('heading',{name:'Which novel polymer candidates deserve the next experiment?'}).waitFor();
 await page.waitForFunction(()=>document.querySelectorAll('.evaluation-review .react-flow__edge-path').length===10);
 const inspector=page.getByRole('complementary',{name:'Evaluation step inspector'}),steps=page.getByRole('navigation',{name:'Evaluation steps'});
 for(const width of [1440,390]){
   await page.setViewportSize({width,height:width===1440?1100:844});await page.getByRole('button',{name:'Fit graph',exact:true}).click();await page.waitForTimeout(150);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   assert.deepEqual((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations.map(v=>v.id),[]);
   await page.screenshot({path:resolve(output,`review-${width}.png`),fullPage:true});
 }
 await page.setViewportSize({width:1440,height:1100});
 for(const [title,concern,text] of [
   ['Solvency: Hansen screening','inappropriate_method','Check applicability to the proposed polymer state before using Hansen screening.'],
   ['Choose candidates worth testing','missing_criterion','Define biological context and an explicit bioavailability evidence need.'],
   ['Compare evidence, then select','misleading_aggregation','Specify how unknown synthesis evidence affects selection; do not silently reward missing results.']
 ]){
   await steps.getByRole('button',{name:title,exact:true}).click();await inspector.getByLabel('Concern',{exact:true}).selectOption(concern);
   await inspector.getByLabel('What should change next campaign?').fill(text);await inspector.getByRole('button',{name:'Save concern',exact:true}).click();
 }
 await page.getByRole('button',{name:'Question',exact:true}).click();await page.getByRole('button',{name:'Evaluation design',exact:true}).click();
 await page.getByRole('heading',{name:'Next campaign: 3 concerns',exact:true}).waitFor();
 const [download]=await Promise.all([page.waitForEvent('download'),page.getByRole('button',{name:'Export review (3)',exact:true}).click()]);
 const raw=await readFile(await download.path(),'utf8'),saved=JSON.parse(raw);assert.equal(saved.notes.length,3);assert.equal(saved.target,'future_campaign_only');
 await writeFile(resolve(output,'exported-review.json'),raw);
 await page.getByLabel('Import design or saved review').setInputFiles({name:'bad.json',mimeType:'application/json',buffer:Buffer.from('{"format":"fake"}')});
 await page.getByText(/Import rejected:/).waitFor();assert.equal(await page.getByRole('heading',{name:'Next campaign: 3 concerns',exact:true}).count(),1);
 page.on('dialog',d=>d.accept());await page.reload();await page.getByRole('heading',{name:'Next campaign: 0 concerns',exact:true}).waitFor();
 await page.getByLabel('Import design or saved review').setInputFiles({name:'review.json',mimeType:'application/json',buffer:Buffer.from(raw)});
 await page.getByRole('button',{name:'Replace local review',exact:true}).click();await page.getByRole('heading',{name:'Next campaign: 3 concerns',exact:true}).waitFor();
 await steps.getByRole('button',{name:'Compare evidence, then select',exact:true}).click();await inspector.getByText(/Weights, hard constraints/).waitFor();
 await page.screenshot({path:resolve(output,'restored-concerns.png'),fullPage:true});
 assert.deepEqual(evidence.errors,[]);assert.deepEqual(evidence.writes,[]);
 evidence.checks=['Named criteria and scientific methods, not duplicated generic evaluators','Desktop/narrow graph and inspector accessibility','SME flags inappropriate method, missing criterion and misleading aggregation','Export and reload/import preserve exact design plus three future-only concerns','Invalid import preserves existing notes','Navigation retains concerns','No owner command or model call'];evidence.status='passed';
}finally{
 if(page&&evidence.status!=='passed'){evidence.failure=await page.locator('body').innerText();await page.screenshot({path:resolve(output,'failure.png'),fullPage:true});}
 if(page)await page.evaluate(()=>fetch('/session/logout',{method:'POST'})).catch(()=>{});
 await writeFile(resolve(output,'evidence.json'),JSON.stringify(evidence,null,2)+'\n');await browser.close();
}
console.log('SME evaluation review passed: '+output);
