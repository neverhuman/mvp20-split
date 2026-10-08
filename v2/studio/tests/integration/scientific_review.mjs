import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const input=JSON.parse(await readFile(process.argv[2],'utf8')),output=resolve(process.argv[3]);
await mkdir(output,{recursive:true});const browser=await chromium.launch({headless:true});
const evidence={status:'running',errors:[],checks:[],views:[]};let page;
try {
 const context=await browser.newContext({viewport:{width:1440,height:1100},reducedMotion:'reduce'});page=await context.newPage();
 page.on('pageerror',e=>evidence.errors.push(e.message));
 const issued=await context.request.post(input.origin+'/launcher/ticket',{headers:{Authorization:'Bearer '+process.env.AMPHORA_BROWSER_LAUNCH_KEY}});assert.equal(issued.status(),200);
 const {ticket}=await issued.json();await page.goto(input.origin+'/#view=execution&launch='+encodeURIComponent(ticket));
 await page.waitForFunction(()=>document.querySelectorAll('.react-flow__node').length===5);
 await page.waitForFunction(()=>document.querySelectorAll('.react-flow__edge-path').length===4);
 assert.equal(await page.locator('.react-flow__edge-path').count(),4);
 assert.match(await page.locator('.react-flow__node').allTextContents().then(x=>x.join(' ')),/candidate a hansen solvency/);
 await page.screenshot({path:resolve(output,'execution.png'),fullPage:true});
 const result=page.getByRole('region',{name:'Scientific calculation result',exact:true});
 for(const [node,expected] of [['candidate_a_hansen_solvency','inside'],['candidate_b_hansen_solvency','outside'],['candidate_a_arrhenius_viscosity','Pa.s'],['candidate_b_arrhenius_viscosity','Pa.s']]) {
  await page.locator(`.react-flow__node[aria-label^="${node},"]`).click();
  await result.getByText('Artifact content and schema hashes verified.',{exact:false}).waitFor();
  assert.ok((await result.innerText()).includes(expected));
  await result.getByText('Retained input parameters',{exact:true}).click();
  evidence.checks.push({node,text:await result.innerText()});
 }
 for(const width of [1440,390]) {
  await page.setViewportSize({width,height:width===1440?1100:844});await page.getByRole('button',{name:'Fit graph',exact:true}).click();await page.waitForTimeout(200);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  assert.deepEqual((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations.map(v=>v.id),[]);
  await page.locator('.evidence-inspector').evaluate(e=>{e.parentElement.scrollTop=0;});
  await page.screenshot({path:resolve(output,`scientific-${width}.png`),fullPage:true});
  evidence.views.push({width,nodes:await page.locator('.react-flow__node').count(),edges:await page.locator('.react-flow__edge-path').count()});
 }
 assert.deepEqual(evidence.errors,[]);evidence.status='passed';
}finally{
 if(page&&evidence.status!=='passed'){evidence.failure=await page.locator('body').innerText();await page.screenshot({path:resolve(output,'failure.png'),fullPage:true});}
 if(page)await page.evaluate(()=>fetch('/session/logout',{method:'POST'})).catch(()=>{});
 await writeFile(resolve(output,'evidence.json'),JSON.stringify(evidence,null,2)+'\n');await browser.close();
}
console.log('Actual served scientific review passed: '+output);
