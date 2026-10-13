/** Actual gateway/owners; only exact retained browser recovery hints are seeded. */
import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';

const input=JSON.parse(await readFile(process.argv[2],'utf8')),output=resolve(process.argv[3]);
assert.ok(process.env.AMPHORA_BROWSER_LAUNCH_KEY);
const browser=await chromium.launch({headless:true});
const evidence={status:'running',scope:'actual-owner retained-command browser recovery',states:[],screenshots:[],requests:[]};
let page;
try{
  const context=await browser.newContext({viewport:{width:1440,height:1100},reducedMotion:'reduce'});
  await context.addInitScript(seeds=>{for(const seed of seeds)if(localStorage.getItem(seed.key)===null)localStorage.setItem(seed.key,seed.value);},input.seeds);
  page=await context.newPage();const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',request=>{const url=new URL(request.url());if(url.pathname.startsWith('/api/'))evidence.requests.push({method:request.method(),path:url.pathname});});
  const issued=await context.request.post(input.origin+'/launcher/ticket',{headers:{Authorization:'Bearer '+process.env.AMPHORA_BROWSER_LAUNCH_KEY}});
  assert.equal(issued.status(),200);const {ticket}=await issued.json();
  await page.goto(input.origin+'/#launch='+ticket+'&view=curation&curation='+input.curation_id);
  await page.getByRole('heading',{name:'How would the next campaign change?',exact:true}).waitFor();
  await page.getByRole('button',{name:'Open new campaign',exact:true}).waitFor();
  async function screenshot(name,width){
    await page.setViewportSize({width,height:width===390?844:1100});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);
    if(name!=='next-curation-ready')await page.waitForFunction(()=>{
      const canvas=document.querySelector('.react-flow');if(!canvas)return false;
      const bounds=canvas.getBoundingClientRect();
      return [...canvas.querySelectorAll('.react-flow__node')].some(node=>{
        const box=node.getBoundingClientRect();
        return box.width>0&&box.height>0&&box.right>bounds.left&&box.left<bounds.right&&box.bottom>bounds.top&&box.top<bounds.bottom;
      });
    });
    const issues=(await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations;
    assert.deepEqual(issues.map(row=>row.id),[]);
    const file=name+'-'+width+'.png';await page.screenshot({path:resolve(output,file),fullPage:true});evidence.screenshots.push(file);
  }
  await page.getByRole('button',{name:'Original campaign',exact:true}).click();
  await page.getByRole('button',{name:'Proposed campaign',exact:true}).click();
  for(const width of [1440,390])await screenshot('retained-proposal',width);
  evidence.states.push('actual original/proposed graph and recovered successor receipt');
  await page.getByRole('button',{name:'Open new campaign',exact:true}).click();
  // This deliberately minimal seed graph has no scientific campaign-flow recipe.
  // Production renders its general authored execution graph rather than inventing one.
  await page.getByRole('heading',{name:'Follow execution',exact:true}).waitFor();
  await page.getByText('Execution complete',{exact:true}).waitFor();
  await page.getByText('Campaign '+input.successor,{exact:true}).waitFor();
  for(const width of [1440,390])await screenshot('completed-successor',width);
  await page.getByLabel('Inspect campaign').selectOption('original');
  await page.getByText('Campaign '+input.predecessor,{exact:true}).waitFor();
  await page.getByLabel('Inspect campaign').selectOption('0');
  await page.getByRole('button',{name:'Next iteration',exact:true}).click();
  const direction=page.getByLabel('What should the next campaign investigate?');await direction.fill('Investigate the retained result in a later synthetic campaign.');
  await page.waitForFunction(()=>[...document.querySelectorAll('button')].some(button=>button.textContent==='Request graph revision'&&!button.disabled));
  for(const width of [1440,390])await screenshot('next-curation-ready',width);
  evidence.states.push('completed successor/original navigation and next-curation context readiness');
  // Reload recovers the original workspace and same retained proposal, with no POST intent.
  await page.goto(input.origin+'/#view=curation&curation='+input.curation_id);await page.reload();
  await page.getByRole('button',{name:'Open new campaign',exact:true}).waitFor();
  assert.deepEqual(errors,[]);
  assert.deepEqual(evidence.requests.filter(row=>row.method==='POST'&&[
    '/api/planning/v1/campaign-curations','/api/deployment/v1/campaign-successor-launches','/api/deployment/v1/campaign-launches'].includes(row.path)),[]);
  evidence.states.push('reload/read-only reconciliation without duplicate intent');evidence.status='passed';
}catch(error){evidence.error=String(error);if(page){await writeFile(resolve(output,'failure.txt'),await page.locator('body').innerText());await page.screenshot({path:resolve(output,'failure.png'),fullPage:true});}throw error;}
finally{await browser.close();await writeFile(resolve(output,'browser-evidence.json'),JSON.stringify(evidence,null,2));}
console.log(JSON.stringify({status:evidence.status,states:evidence.states}));
