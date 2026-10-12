import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import {workspaceFixture} from './curation_workspace/fixture.mjs';
const output=resolve(process.argv[2]??'../.test-results/curation-workspace-'+Date.now());await mkdir(output,{recursive:true});
const fixture=await workspaceFixture('dist/local'),server=createServer(fixture.handle);
await new Promise(done=>server.listen(0,'127.0.0.1',done));const browser=await chromium.launch({headless:true}),errors=[];
const evidence={status:'running',profile:'production-entry-scripted-public-peers',screenshots:[],states:[],counts:fixture.counts,requests:fixture.requests};
let page;
try{
  const context=await browser.newContext({viewport:{width:1440,height:1100},reducedMotion:'reduce'});
  await context.addInitScript(seed=>{if(!localStorage.getItem(seed.key))localStorage.setItem(seed.key,seed.value);},fixture.seed);
  page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));await page.goto(`http://127.0.0.1:${server.address().port}/#view=execution`);
  await page.getByRole('heading',{name:'Follow the planned work',exact:true}).waitFor();
  await page.getByRole('button',{name:'6. Next iteration',exact:true}).click();
  const direction=page.getByLabel('What should the next campaign investigate?');await direction.fill('Refine the research sequence using the selected evidence.');
  await page.getByRole('button',{name:'Request graph revision',exact:true}).click();
  await page.getByRole('button',{name:'Review model proposal',exact:true}).click();await page.getByText('Awaiting a retained proposal',{exact:true}).waitFor();
  await page.getByRole('button',{name:'Refresh record',exact:true}).click();
  const run=page.getByRole('button',{name:'Run this revised campaign',exact:true});await run.waitFor();
  await page.waitForFunction(()=>[...document.querySelectorAll('button')].some(button=>button.textContent==='Run this revised campaign'&&!button.disabled));
  evidence.states.push('original-composer-proposal-review');
  await run.click();await page.getByRole('button',{name:'Open new campaign',exact:true}).click();
  await page.getByRole('heading',{name:'Follow the planned work',exact:true}).waitFor();
  await page.getByText('Pinned launch plan /',{exact:false}).waitFor();
  for(const width of [1440,390]){
    await page.setViewportSize({width,height:width===390?844:1100});await page.getByRole('button',{name:'Fit graph',exact:true}).click();
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    const issues=(await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations;assert.deepEqual(issues.map(item=>item.id),[]);
    const name=`successor-running-${width}.png`;await page.screenshot({path:resolve(output,name),fullPage:true});evidence.screenshots.push(name);
  }
  await page.getByLabel('Inspect campaign').selectOption('original');await page.getByText('Retained plan / completed execution',{exact:false}).waitFor();
  await page.getByLabel('Inspect campaign').selectOption('0');await page.getByText('Pinned launch plan /',{exact:false}).waitFor();evidence.states.push('successor-runtime-and-predecessor-navigation');
  fixture.completeChild();await page.getByText('Retained plan / completed execution',{exact:false}).waitFor({timeout:10000});
  await page.getByRole('button',{name:'6. Next iteration',exact:true}).click();await direction.fill('Request a missing heat-and-addition capability.');
  await page.getByRole('button',{name:'Request graph revision',exact:true}).click();await page.getByRole('button',{name:'Review model proposal',exact:true}).click();
  await page.getByRole('button',{name:'Refresh record',exact:true}).click();await page.getByRole('heading',{name:'What does the next campaign need?',exact:true}).waitFor();
  await page.getByRole('region',{name:'Capability inspection'}).getByText('After mixing, before the final addition',{exact:true}).waitFor();
  await page.getByRole('button',{name:'Prepare another revision request',exact:true}).click();await direction.waitFor();
  assert.equal(await direction.inputValue(),'');assert.equal(fixture.counts.curation,2);assert.equal(fixture.counts.successor,1);assert.equal(fixture.counts.fresh,0);
  evidence.states.push('successor-next-curation-missing-capability-new-cycle');
  assert.deepEqual(errors,[]);assert.deepEqual(fixture.errors,[]);evidence.status='passed';
}catch(error){evidence.error=String(error);evidence.errors=[...errors,...fixture.errors];if(page){await writeFile(resolve(output,'failure.txt'),await page.locator('body').innerText());await page.screenshot({path:resolve(output,'failure.png'),fullPage:true});}throw error;}
finally{await browser.close();await new Promise(done=>server.close(done));await writeFile(resolve(output,'evidence.json'),JSON.stringify(evidence,null,2));}
console.log(JSON.stringify({passed:true,output,states:evidence.states,counts:fixture.counts}));
