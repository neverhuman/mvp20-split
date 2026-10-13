/** UI-01/V1: actual retained owners, native Chromium zoom, keyboard and labelled read failures. */
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,mkdtemp} from 'node:fs/promises';
import {resolve} from 'node:path';
import {tmpdir} from 'node:os';
import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';

const input=JSON.parse(await readFile(process.argv[2],'utf8')),output=resolve(process.argv[3]);
await mkdir(output,{recursive:true});
const profile=await mkdtemp(resolve(tmpdir(),'amphora-ui-acceptance-'));
const extension=resolve(profile,'zoom-control');await mkdir(extension);
await writeFile(resolve(extension,'manifest.json'),JSON.stringify({manifest_version:3,name:'Amphora acceptance zoom control',version:'1.0',permissions:['tabs'],background:{service_worker:'worker.js'}}));
await writeFile(resolve(extension,'worker.js'),'chrome.runtime.onInstalled.addListener(()=>{});');
const context=await chromium.launchPersistentContext(resolve(profile,'browser'),{
 channel:'chromium',headless:true,viewport:null,reducedMotion:'reduce',
 args:['--window-size=1440,1100','--disable-extensions-except='+extension,'--load-extension='+extension],
});
const evidence={status:'running',profile,checks:[],screenshots:[],commands:[],page_errors:[],failure_injections:[]};
let page;
try{
 const worker=context.serviceWorkers()[0]??await context.waitForEvent('serviceworker',{timeout:30000});
 await context.addInitScript(entries=>{for(const [key,value] of entries)if(localStorage.getItem(key)===null)localStorage.setItem(key,value);},input.recovery);
 page=await context.newPage();page.on('pageerror',e=>evidence.page_errors.push(e.message));
 page.on('request',r=>{if(r.method()==='POST'&&/\/v1\/(campaign-curations|campaign-launches|campaign-successor-launches)$/.test(r.url()))evidence.commands.push(r.url());});
 const issued=await context.request.post(input.origin+'/launcher/ticket',{headers:{Authorization:'Bearer '+process.env.AMPHORA_BROWSER_LAUNCH_KEY}});
 assert.equal(issued.status(),200);const {ticket}=await issued.json();
 const original=input.origin+'/#view=curation&curation='+input.curation_id;
 await page.goto(original+'&launch='+ticket);
 const open=page.getByRole('button',{name:'Open new campaign',exact:true});await open.waitFor({timeout:60000});
 async function enter(locator){await locator.focus();await page.keyboard.press('Enter');}
 const direction=page.locator('.curation-intent details');assert.equal(await direction.getAttribute('open'),null);
 await enter(direction.locator('summary'));assert.ok((await direction.locator('p').innerText()).length>400);
 await enter(direction.locator('summary'));assert.equal(await direction.getAttribute('open'),null);
 evidence.checks.push('long original direction retained behind keyboard disclosure');
 await enter(open);
 await page.getByRole('heading',{name:'Follow the planned work',exact:true}).waitFor({timeout:60000});
 assert.ok((await page.getByLabel('Inspect campaign').locator('option:checked').innerText()).includes(input.run_id));
 async function zoom(factor){
  const result=await worker.evaluate(async ({origin,factor})=>{
   const tabs=await chrome.tabs.query({});const tab=tabs.find(t=>t.url?.startsWith(origin));
   if(!tab)throw Error('Acceptance tab missing');
   await chrome.tabs.setZoomSettings(tab.id,{mode:'automatic',scope:'per-origin'});
   await chrome.tabs.setZoom(tab.id,factor);return await chrome.tabs.getZoom(tab.id);
  },{origin:input.origin,factor});
  assert.equal(result,factor);await page.waitForTimeout(350);
  return page.evaluate(()=>({innerWidth,innerHeight,dpr:devicePixelRatio}));
 }
 const baseline=await zoom(1);const enlarged=await zoom(2);
 assert.ok(enlarged.dpr>=baseline.dpr*1.9,'Native browser zoom must change device pixel ratio');
 evidence.native_zoom={baseline,enlarged,factor:2,method:'chrome.tabs.setZoom; verified getZoom and devicePixelRatio'};
 async function snapshot(name){
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true,'Document overflows');
  const failures=(await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations;
  assert.deepEqual(failures.filter(v=>['critical','serious'].includes(v.impact)).map(v=>v.id),[]);
  // Native browser zoom makes CSS pixels differ from CDP's device-independent
  // layout coordinates. Use the latter explicitly; Playwright's full-page CSS
  // clip otherwise captures only the left half at 200% on this Chromium build.
  const client=await context.newCDPSession(page);
  try{
   const metrics=await client.send('Page.getLayoutMetrics');
   const {data}=await client.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:true,
    clip:{...metrics.contentSize,scale:1}});
   const bytes=Buffer.from(data,'base64');
   assert.ok(bytes.readUInt32BE(16)>=Math.floor(metrics.contentSize.width),'Native zoom capture is clipped');
   await writeFile(resolve(output,name+'.png'),bytes);
  }finally{await client.detach();}
  evidence.screenshots.push(name+'.png');
 }
 for(const [label,heading] of [
  ['1. Question','What this campaign can tell us'],
  ['2. Evaluation design','Review the reasoning'],
  ['3. Approach and run','Follow the planned work'],
  ['4. Results and evidence','Compare evidence, not just scores'],
  ['5. Knowledge graph','Follow the evidence'],
  ['6. Next iteration','Improve the next campaign'],
 ]){
  await enter(page.getByRole('button',{name:label,exact:true}));
  await page.getByRole('heading',{name:heading,exact:true}).waitFor();
  assert.ok((await page.getByLabel('Inspect campaign').locator('option:checked').innerText()).includes(input.run_id));
  if(label.startsWith('5.')){
   assert.equal(await page.getByText('This view needs a fresh read.',{exact:true}).count(),0,'Unselected evidence must remain idle');
   await enter(page.getByRole('button',{name:'Hansen solvency screen',exact:true}).first());
   await page.getByRole('heading',{name:'Connected knowledge',exact:true}).waitFor();
   await page.waitForFunction(()=>document.querySelectorAll('.react-flow__edge-path').length===2);
  }
  await snapshot('native-zoom200-'+label[0]);evidence.checks.push('keyboard navigation '+label);
 }
 const draft='Keep the original results; investigate the missing synthesis evidence in the next campaign.';
 const composer=page.getByLabel('What should the next campaign investigate?');
 await composer.fill(draft);await enter(page.getByRole('button',{name:'Refresh campaign context',exact:true}));
 await page.waitForFunction(()=>[...document.querySelectorAll('button')].some(b=>b.textContent==='Request graph revision'&&!b.disabled));
 assert.equal(await composer.inputValue(),draft);
 assert.match(await page.locator('.curation-composer').innerText(),/4 input artifacts/);
 await page.keyboard.press('Tab');await page.keyboard.press('Tab');
 assert.ok(await page.evaluate(()=>document.activeElement instanceof HTMLButtonElement));
 evidence.checks.push('unsent direction survives verified context refresh; four inputs retained; tab reaches controls');
 await zoom(1);
 await enter(page.getByRole('button',{name:'3. Approach and run',exact:true}));
 await page.getByRole('heading',{name:'Follow the planned work',exact:true}).waitFor();
 const step=page.getByLabel('Inspect step',{exact:true});await step.focus();await page.keyboard.press('End');await page.keyboard.press('Enter');
 assert.match(await page.locator('.flow-inspector').innerText(),/viscosity|Arrhenius/i);
 await snapshot('keyboard-scientific-inspector');evidence.checks.push('keyboard step selector opens scientific result');
 // Only the named GET is intercepted. No owner record or application state is changed.
 const route='**/api/planning/v1/campaign-curations/'+input.curation_id;
 for(const [status,body,message] of [
  [403,{reason_code:'planning_access_denied'},'This revision or its capability details are not available to this session.'],
  [503,{error:'owner_request_rejected'},'The revision service is temporarily unavailable.'],
 ]){
  await page.route(route,r=>r.request().method()==='GET'?r.fulfill({status,contentType:'application/json',body:JSON.stringify(body)}):r.continue());
  await page.goto(original);await page.reload();await page.getByText(message,{exact:true}).waitFor();
  assert.equal(await page.locator('.curation-intent').count(),0);
  await snapshot('injected-read-failure-'+status);evidence.failure_injections.push({status,scope:'Browser-only retained curation GET; actual owner untouched'});
  await page.unroute(route);await enter(page.getByRole('button',{name:'Refresh record',exact:true}));
  await open.waitFor({timeout:60000});evidence.checks.push('original receipt recovered after injected '+status);
 }
 await page.reload();await open.waitFor({timeout:60000});
 assert.deepEqual(evidence.commands,[]);assert.deepEqual(evidence.page_errors,[]);
 evidence.status='passed';
}catch(error){evidence.status='failed';evidence.error=String(error).split('\n')[0];if(page){await page.screenshot({path:resolve(output,'failure.png'),fullPage:true});await writeFile(resolve(output,'failure.txt'),await page.locator('body').innerText());}throw error;}
finally{await context.close();await writeFile(resolve(output,'evidence.json'),JSON.stringify(evidence,null,2));}
console.log('Integrated workspace acceptance passed');
