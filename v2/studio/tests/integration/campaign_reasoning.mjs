/** Existing live-provider history only. No request, launch or provider issuance. */
import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const input=JSON.parse(await readFile(process.argv[2],'utf8')),output=resolve(process.argv[3]);await mkdir(output,{recursive:true});
const browser=await chromium.launch({headless:true}),evidence={status:'running',run_id:input.run_id,errors:[],mutations:[],models:[],captures:[]};let context;
try{
 context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});const page=await context.newPage();
 page.on('pageerror',e=>evidence.errors.push(e.message));page.on('request',r=>{if(r.method()!=='GET'&&r.url().includes('/api/'))evidence.mutations.push([r.method(),r.url()]);});
 page.on('response',async r=>{try{if(r.ok()&&r.url().includes('/api/runtime/v1/supervision/')){const d=await r.json();for(const row of d.items??[]){if(row.model)evidence.models.push(row.model);if(row.capture)evidence.captures.push({status:row.status,selected_by_winner:row.selected_by_winner,capture:row.capture});}}}catch{}});
 const issued=await context.request.post(input.origin+'/launcher/ticket',{headers:{Authorization:'Bearer '+process.env.AMPHORA_BROWSER_LAUNCH_KEY}});assert.equal(issued.status(),200);const {ticket}=await issued.json();
 await page.goto(input.origin+'/#view=knowledge&launch='+encodeURIComponent(ticket));
 const open=page.getByRole('button',{name:'Inspect model decisions',exact:true});await open.focus();await page.keyboard.press('Enter');
 await page.getByRole('heading',{name:'What did the model recommend?',exact:true}).waitFor();
 const panel=page.getByRole('region',{name:'Recorded campaign decisions',exact:true});
 await panel.getByRole('button',{name:'review-numeric-seed',exact:true}).click();await panel.getByRole('button',{name:'Inspect request 1',exact:true}).click();
 await panel.getByText('Included: knowledge',{exact:true}).waitFor();
 await panel.getByRole('button',{name:'Responses',exact:true}).click();await panel.getByText('Selected by the committed outcome',{exact:true}).waitFor();
 await panel.getByRole('button',{name:'Inspect recorded proposal',exact:true}).click();
 await panel.getByText('Recorded intent · Subsequent campaign adoption not verified',{exact:true}).waitFor();
 evidence.recorded_rationale=await panel.getByRole('region',{name:'Recorded follow-up proposal',exact:true}).innerText();
 assert.ok(evidence.models.some(m=>m.provider_id==='openai'&&m.model_id==='gpt-5.4-mini-2026-03-17'));
 assert.ok(evidence.captures.some(c=>c.selected_by_winner));
 for(const width of [1440,390]){await page.setViewportSize({width,height:1000});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.deepEqual((await new AxeBuilder({page}).include('.campaign-reasoning').withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations.map(v=>v.id),[]);await page.screenshot({path:resolve(output,'reasoning-'+width+'.png'),fullPage:true});}
 await panel.getByRole('button',{name:'Return to results',exact:true}).click();await page.getByRole('heading',{name:'Compare retained generations',exact:true}).waitFor();assert.equal(await page.getByRole('region',{name:'Recorded follow-up proposal'}).count(),0);
 assert.deepEqual(evidence.mutations,[]);assert.deepEqual(evidence.errors,[]);evidence.status='passed';console.log('Recorded OpenAI reasoning browser passed: '+output);
}catch(e){evidence.status='failed';evidence.failure=String(e);throw e;}
finally{if(context)await context.request.post(input.origin+'/session/logout').catch(()=>undefined);await writeFile(resolve(output,'evidence.json'),JSON.stringify(evidence,null,2));await browser.close();}
