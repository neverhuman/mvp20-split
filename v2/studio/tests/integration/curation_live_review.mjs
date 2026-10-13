/** Real retained live output variants, including unresolved requested capability. */
import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
const input=JSON.parse(await readFile(process.argv[2],'utf8')),output=resolve(process.argv[3]);
const browser=await chromium.launch({headless:true});
const evidence={status:'running',screenshots:[],requests:[],scope:'actual live capability request and failed graph'};
let page;
try{
  const context=await browser.newContext({viewport:{width:1440,height:1100},reducedMotion:'reduce'});
  await context.addInitScript(seeds=>{for(const seed of seeds)if(localStorage.getItem(seed.key)===null)localStorage.setItem(seed.key,seed.value);},input.seeds);
  page=await context.newPage();const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',request=>{const url=new URL(request.url());if(url.pathname.startsWith('/api/'))evidence.requests.push({method:request.method(),path:url.pathname});});
  const issued=await context.request.post(input.origin+'/launcher/ticket',{headers:{Authorization:'Bearer '+process.env.AMPHORA_BROWSER_LAUNCH_KEY}});
  assert.equal(issued.status(),200);const {ticket}=await issued.json();
  await page.goto(input.origin+'/#launch='+ticket+'&view=curation&curation='+input.missing);
  await page.getByText('Additional tools needed',{exact:true}).waitFor();
  const region=page.getByRole('region',{name:'Requested capabilities',exact:true});
  assert.equal(await region.getByRole('button').count(),input.capabilities.length);
  for(let i=0;i<input.capabilities.length;i++){
    await region.getByRole('button').nth(i).click();
    await page.getByRole('heading',{name:input.capabilities[i].purpose,exact:true}).waitFor();
    await page.getByText('Not yet supplied',{exact:true}).waitFor();
    await page.getByText('Requested inputs and outputs',{exact:true}).click();
    await page.getByRole('heading',{name:'What would demonstrate it works?',exact:true}).waitFor();
  }
  async function capture(name){
    for(const width of [1440,390]){
      await page.setViewportSize({width,height:width===390?844:1100});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);
      assert.deepEqual((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations.map(row=>row.id),[]);
      const file=name+'-'+width+'.png';await page.screenshot({path:resolve(output,file),fullPage:true});evidence.screenshots.push(file);
    }
  }
  assert.equal(await page.getByRole('button',{name:'Open new campaign',exact:true}).count(),0);
  await capture('missing-capability');
  await page.reload();await page.getByText('Not yet supplied',{exact:true}).waitFor();
  await page.goto(input.origin+'/#view=curation&curation='+input.failed);
  await page.getByText(input.failure_label??'Revision preparation failed',{exact:true}).waitFor();
  await page.getByRole('heading',{name:input.outcome_heading??'No retained proposal',exact:true}).waitFor();
  if(input.duplicate_nodes){
    await page.getByText('Duplicate step identities prevent a reliable canvas. Inspect the structural changes and correct the proposal.',{exact:true}).waitFor();
    assert.equal(await page.getByRole('button',{name:'Open new campaign',exact:true}).count(),0);
  }
  await capture('failed-graph');
  await page.getByRole('button',{name:'Refresh record',exact:true}).click();
  await page.reload();await page.getByRole('heading',{name:input.outcome_heading??'No retained proposal',exact:true}).waitFor();
  assert.deepEqual(errors,[]);
  assert.deepEqual(evidence.requests.filter(row=>row.method==='POST'&&[
    '/api/planning/v1/campaign-curations','/api/deployment/v1/campaign-successor-launches','/api/deployment/v1/campaign-launches'].includes(row.path)),[]);
  evidence.status='passed';
}catch(error){evidence.error=String(error);if(page){await writeFile(resolve(output,'failure.txt'),await page.locator('body').innerText());await page.screenshot({path:resolve(output,'failure.png'),fullPage:true});}throw error;}
finally{await browser.close();await writeFile(resolve(output,'browser-evidence.json'),JSON.stringify(evidence,null,2));}
console.log(JSON.stringify({status:evidence.status,screenshots:evidence.screenshots}));
