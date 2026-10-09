/** Served campaign -> pinned Knowledge -> verified source -> campaign. No mocks. */
import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const input=JSON.parse(await readFile(process.argv[2],'utf8')),output=resolve(process.argv[3]);
await mkdir(output,{recursive:true});
if(input.tls_spki)assert.match(input.tls_spki,/^[A-Za-z0-9+/]{43}=$/);
const browser=await chromium.launch({headless:true,args:input.tls_spki?['--ignore-certificate-errors-spki-list='+input.tls_spki]:[]});
const evidence={status:'running',errors:[],checks:[],run_id:input.run_id,asset_mode:'actual_served'};
let page;
try{
 const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
 page=await context.newPage();page.on('pageerror',e=>evidence.errors.push(e.message));
 const issued=await context.request.post(input.origin+'/launcher/ticket',{headers:{Authorization:'Bearer '+process.env.AMPHORA_BROWSER_LAUNCH_KEY}});
 assert.equal(issued.status(),200);const {ticket}=await issued.json();
 await page.goto(input.origin+'/#view=domain&launch='+encodeURIComponent(ticket));
 await page.getByRole('heading',{name:'Follow the evidence',exact:true}).waitFor();
 await page.getByText('This exact Knowledge revision is retained',{exact:false}).waitFor();
 await page.getByRole('button',{name:'Hansen solvency screen',exact:true}).first().click();
 await page.getByRole('heading',{name:'Connected knowledge',exact:true}).waitFor();
 await page.waitForFunction(()=>document.querySelectorAll('.explore-domain .react-flow__edge-path').length>0);
 await page.locator('.explore-claims button').filter({hasText:'requires'}).first().click();
 await page.getByRole('heading',{name:'Claim and grounding',exact:true}).waitFor();
 await page.getByRole('button',{name:'Read source passage 1',exact:true}).click();
 await page.getByRole('region',{name:'Verified source passage',exact:true}).waitFor();
 assert.match(await page.locator('.source-text').innerText(),/not scientific validation/);
 await page.getByRole('button',{name:'Inspect conversion 1',exact:true}).click();
 await page.getByRole('region',{name:'Conversion history',exact:true}).waitFor();
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:width===1440?1000:844});
  await page.getByRole('button',{name:'Fit graph',exact:true}).click();
  await page.getByRole('button',{name:'Read source passage 1',exact:true}).click();
  await page.getByRole('region',{name:'Verified source passage',exact:true}).waitFor();
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  const violations=(await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations;
  evidence['accessibility_'+width]=violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}));
  assert.deepEqual(violations.map(v=>v.id),[]);
  await page.getByRole('button',{name:'Read source passage 1',exact:true}).click();
  await page.getByRole('region',{name:'Verified source passage',exact:true}).waitFor();
  await page.screenshot({path:resolve(output,'knowledge-'+width+'.png'),fullPage:true});
 }
 await page.getByRole('button',{name:'Return to campaign execution',exact:true}).click();
 await page.getByRole('button',{name:'4. Results and evidence',exact:true}).click();
 assert.match(await page.getByRole('table').innerText(),/inside/);assert.match(await page.getByRole('table').innerText(),/outside/);
 await page.getByRole('button',{name:'5. Knowledge graph',exact:true}).click();
 await page.getByRole('button',{name:'Hansen solvency screen',exact:true}).first().waitFor();
 assert.match(page.url(),/view=domain/);
 assert.deepEqual(evidence.errors,[]);
 evidence.checks.push('Retained context selects exact Knowledge revision without URL explore pin','Actual connected domain neighborhood','Hypothesis claim to digest-verified source passage and conversion trace','Return to actual campaign results and back','1440/390 accessibility and no page overflow');
 evidence.status='passed';
}finally{
 if(page&&evidence.status!=='passed'){evidence.failure=await page.locator('body').innerText();await page.screenshot({path:resolve(output,'failure.png'),fullPage:true});}
 if(page)await page.evaluate(()=>fetch('/session/logout',{method:'POST'})).catch(()=>{});
 await writeFile(resolve(output,'evidence.json'),JSON.stringify(evidence,null,2)+'\n');await browser.close();
}
console.log('Knowledge traversal verified: '+output);
