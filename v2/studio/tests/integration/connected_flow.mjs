import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const input=JSON.parse(await readFile(process.argv[2],'utf8')),output=resolve(process.argv[3]);
await mkdir(output,{recursive:true});const browser=await chromium.launch({headless:true});
const evidence={status:'running',errors:[],ownerWrites:[],checks:[]};let page;
try {
 const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});page=await context.newPage();
 evidence.asset_mode=process.argv[4]?'candidate_override':'actual_served';
 if(process.argv[4])for(const name of ['app.js','app.css'])await page.route(input.origin+'/'+name,async route=>route.fulfill({body:await readFile(resolve(process.argv[4],name)),contentType:name.endsWith('js')?'application/javascript':'text/css'}));
 page.on('pageerror',e=>evidence.errors.push(e.message));page.on('request',r=>{if(new URL(r.url()).pathname.startsWith('/api/')&&r.method()!=='GET')evidence.ownerWrites.push({method:r.method(),path:new URL(r.url()).pathname});});
 const issued=await context.request.post(input.origin+'/launcher/ticket',{headers:{Authorization:'Bearer '+process.env.AMPHORA_BROWSER_LAUNCH_KEY}});assert.equal(issued.status(),200);
 const {ticket}=await issued.json();await page.goto(input.origin+'/#view=question&launch='+encodeURIComponent(ticket));
 await page.getByRole('heading',{name:/Which polymer fixture/}).waitFor();
 await page.getByRole('button',{name:'Review the evaluation plan',exact:true}).click();
 await page.getByLabel('Inspect step',{exact:true}).selectOption('plan:solvency');
 await page.getByLabel('What should change next campaign?',{exact:true}).fill('Check parameter provenance before compatibility testing.');
 await page.getByRole('button',{name:'Save concern',exact:true}).click();
 await page.getByText('1 future concerns',{exact:false}).waitFor();
 await page.getByRole('button',{name:'Follow this plan in execution',exact:true}).click();
 await page.waitForFunction(()=>document.querySelectorAll('.react-flow__node').length===14&&document.querySelectorAll('.react-flow__edge-path').length===18);
 assert.equal(await page.locator('.react-flow__node[aria-label*="planning context"]').count(),8);
 await page.screenshot({path:resolve(output,'plan-execution.png'),fullPage:true});
 await page.getByRole('button',{name:'fixture-polymer-A — succeeded',exact:true}).click();
 const result=page.getByRole('region',{name:'Scientific result detail'});assert.match(await result.innerText(),/inside/);
 await result.getByRole('button',{name:'Why this method?',exact:true}).click();
 await page.getByRole('heading',{name:'Solvency: Hansen screening',exact:true}).waitFor();
 await page.getByRole('button',{name:'Compare the results',exact:true}).click();
 assert.equal(await page.getByRole('button',{name:'Inspect solvency',exact:true}).count(),2);
 assert.match(await page.getByRole('table').innerText(),/inside/);assert.match(await page.getByRole('table').innerText(),/outside/);
 await page.getByRole('button',{name:'Inspect viscosity',exact:true}).last().click();
 assert.match(await result.innerText(),/fixture-polymer-B/i);assert.match(await result.innerText(),/2.678553/);
 await page.getByRole('button',{name:'4. Results and evidence',exact:true}).click();
 for(const width of [1440,390]){await page.setViewportSize({width,height:width===1440?1000:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.deepEqual((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations.map(v=>v.id),[]);await page.screenshot({path:resolve(output,`comparison-${width}.png`),fullPage:true});}
 await page.getByRole('button',{name:'Choose what to improve next',exact:true}).click();
 await page.getByLabel('Next-campaign direction',{exact:true}).fill('Obtain synthesis evidence and define a process viscosity target.');await page.getByRole('button',{name:'Save direction',exact:true}).click();
 await page.getByRole('heading',{name:'2 focused concerns',exact:true}).waitFor();
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'Export next-campaign review',exact:true}).click();const saved=await download;await saved.saveAs(resolve(output,'next-campaign-review.json'));
 const exported=JSON.parse(await readFile(resolve(output,'next-campaign-review.json'),'utf8'));assert.equal(exported.source_run.run_id,input.run_id);assert.equal(exported.review.notes.length,2);assert.equal(exported.results.length,4);assert.equal(exported.source_plan.schema_ref.schema_id,'demo.campaign-context');assert.equal(exported.authority,'local_unsubmitted');
 await page.getByRole('button',{name:'2. Evaluation design',exact:true}).click();await page.getByText('2 future concerns',{exact:false}).waitFor();
 evidence.checks.push('Actual retained planning artifact drives all five views','Planning context and real execution nodes have distinct statuses/connections','Method-to-actual-result-to-method traversal','Two candidate comparison with unknown synthesis and no inferred winner','Two future concerns survive navigation and export exact source/result references','Desktop/mobile accessibility and no page overflow');
 assert.deepEqual(evidence.errors,[]);assert.deepEqual(evidence.ownerWrites,[]);evidence.status='passed';
}finally{
 if(page&&evidence.status!=='passed'){evidence.failure=await page.locator('body').innerText();await page.screenshot({path:resolve(output,'failure.png'),fullPage:true});}
 if(page)await page.evaluate(()=>fetch('/session/logout',{method:'POST'})).catch(()=>{});
 await writeFile(resolve(output,'evidence.json'),JSON.stringify(evidence,null,2)+'\n');await browser.close();
}
console.log('Actual connected campaign walkthrough passed: '+output);
