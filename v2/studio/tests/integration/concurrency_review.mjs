import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const input=JSON.parse(await readFile(process.argv[2],'utf8')),assets=resolve(process.argv[3]),output=resolve(process.argv[4]);
await mkdir(output,{recursive:true});const browser=await chromium.launch({headless:true});
const evidence={status:'running',errors:[],checks:[],views:[]};let page;
try {
 const context=await browser.newContext({viewport:{width:1440,height:1100},reducedMotion:'reduce'});page=await context.newPage();
 page.on('pageerror',e=>evidence.errors.push(e.message));
 for(const name of process.argv.includes('--served')?[]:['app.js','app.css'])await page.route(input.origin+'/'+name,async route=>route.fulfill({body:await readFile(resolve(assets,name)),contentType:name.endsWith('js')?'application/javascript':'text/css'}));
 const issued=await context.request.post(input.origin+'/launcher/ticket',{headers:{Authorization:'Bearer '+process.env.AMPHORA_BROWSER_LAUNCH_KEY}});assert.equal(issued.status(),200);
 const {ticket}=await issued.json();await page.goto(input.origin+'/#view=execution&launch='+encodeURIComponent(ticket));
 await page.getByRole('button',{name:'Collapse evaluate_batch (2 parallel branches)',exact:true}).waitFor();
 await page.waitForFunction(()=>document.querySelectorAll('.react-flow__node').length===14);
 await page.waitForFunction(()=>document.querySelectorAll('.react-flow__minimap-node').length===14);
 await page.waitForTimeout(200);
 await page.screenshot({path:resolve(output,'initial-focused.png'),fullPage:true});
 const geometry=async()=>page.evaluate(()=>({nodes:[...document.querySelectorAll('.react-flow__node')].map(n=>{const r=n.getBoundingClientRect();return {id:n.dataset.id,text:n.textContent,x:r.x,y:r.y,width:r.width,height:r.height};}),edges:[...document.querySelectorAll('.react-flow__edge-path')].map(e=>({path:e.getAttribute('d'),dashed:getComputedStyle(e).strokeDasharray}))}));
 for(const width of [1440,390]) {
  await page.setViewportSize({width,height:width===1440?1100:844});await page.getByRole('button',{name:'Fit graph',exact:true}).click();await page.waitForTimeout(200);
  const g=await geometry(),branches=g.nodes.filter(n=>/evaluateBranch [12]/.test(n.text));
  assert.equal(branches.length,2);assert.notEqual(branches[0].x,branches[1].x);assert.ok(Math.abs(branches[0].y-branches[1].y)<2);
  assert.ok(g.nodes.some(n=>n.text.includes('Rejoin branches')));assert.ok(g.edges.some(e=>e.dashed!=='none'));
  for(const a of g.nodes)for(const b of g.nodes)if(a.id!==b.id)assert.ok(a.x+a.width<=b.x+.1||b.x+b.width<=a.x+.1||a.y+a.height<=b.y+.1||b.y+b.height<=a.y+.1);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  assert.deepEqual((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations.map(v=>v.id),[]);
  await page.screenshot({path:resolve(output,`parallel-${width}.png`),fullPage:true});evidence.views.push({width,...g});
 }
 await page.setViewportSize({width:1440,height:1100});
 await page.getByRole('button',{name:'Expand generations (2 iterations)',exact:true}).click();
 await page.getByRole('button',{name:'Collapse generations (2 iterations)',exact:true}).waitFor();
 await page.waitForFunction(()=>document.querySelectorAll('.react-flow__node').length===33);
 for(const i of [1,2]) {
  await page.getByRole('button',{name:`Expand evaluate_batch / generations ${i} (2 parallel branches)`,exact:true}).click();
  await page.getByRole('button',{name:`Collapse evaluate_batch / generations ${i} (2 parallel branches)`,exact:true}).waitFor();
 }
 await page.waitForFunction(()=>document.querySelectorAll('.react-flow__node').length===43);
 await page.getByRole('button',{name:'Fit graph',exact:true}).click();await page.waitForTimeout(200);
 assert.equal(await page.locator('.react-flow__node[aria-label^="evaluate, succeeded"]').count(),6);
 await page.screenshot({path:resolve(output,'all-generations.png'),fullPage:true});
 const refreshed=page.waitForResponse(r=>new URL(r.url()).pathname.endsWith('/nodes')&&r.request().method()==='GET');
 await page.getByRole('button',{name:'Refresh observation',exact:true}).click();await refreshed;
 await page.waitForFunction(()=>document.querySelectorAll('.react-flow__node').length===43);
 await page.getByRole('button',{name:'Collapse generations (2 iterations)',exact:true}).waitFor();
 evidence.checks.push('All expanded generations and nested parallel groups restored after actual refresh');
 await page.getByRole('button',{name:'Collapse generations (2 iterations)',exact:true}).click();
 await page.waitForFunction(()=>document.querySelectorAll('.react-flow__node').length===14);
 await page.locator('.react-flow__node[aria-label^="evaluate, succeeded"]').first().click();
 await page.getByRole('region',{name:'Selected node',exact:true}).getByRole('heading',{name:'evaluate',exact:true}).waitFor();
 await page.getByRole('button',{name:'Focus expanded work',exact:true}).click();await page.waitForTimeout(200);
 await page.screenshot({path:resolve(output,'focused-branches.png'),fullPage:true});
 evidence.checks.push('Two real sibling evaluations visible together on opening','Distinct fan-out and rejoin boundaries','Desktop/narrow geometry, accessibility and no overlap','Two generations expanded without losing root context','Six evaluations across three parallel batches on one canvas','Nested branch selection reads real owner detail');
 // Separate presentation fault fixture. Owner records are never changed.
 await page.route('**/api/runtime/**',async route=>{
  const response=await route.fetch();if(response.status()!==200)return route.fulfill({response});
  const body=await response.json();
  const node=n=>{const occurrence=n.path?.occurrences?.at(-1);
   if(occurrence?.kind==='scatter'&&occurrence.index===1)n.status=n.kind==='invoke'?'failed':'blocked';
   else if(!occurrence&&n.kind==='scatter')n.status='blocked';
  };
  for(const n of body.nodes??[])node(n.activation??n);if(body.node)node(body.node);
  const scope=s=>{const o=s.occurrences?.at(-1);if(o?.kind==='scatter'&&o.index===1)s.status='failed';else if(!o)s.status='blocked';};
  for(const s of body.scopes??[])scope(s);if(body.graph_scope)scope(body.graph_scope);if(body.snapshot)body.snapshot.status='blocked';
  await route.fulfill({response,json:body});
 });
 await page.getByRole('button',{name:'Refresh observation',exact:true}).click();
 await page.locator('.react-flow__node[aria-label^="evaluate, failed"]').waitFor();
 await page.waitForFunction(()=>document.querySelectorAll('.react-flow__minimap-node').length===14);
 await page.getByRole('button',{name:'Focus expanded work',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('.react-flow__node[aria-label^="evaluate, failed"]')?.getBoundingClientRect().width>180);
 assert.equal(await page.locator('.react-flow__node[aria-label^="evaluate, succeeded"]').count(),1);
 assert.equal(await page.locator('.react-flow__node[aria-label^="Rejoin branches, blocked"]').count(),1);
 await page.evaluate(()=>{const label=document.createElement('p');label.textContent='PRESENTATION TEST FIXTURE: one failed sibling and blocked join; not the retained campaign outcome.';document.body.prepend(label);});
 await page.screenshot({path:resolve(output,'fixture-failed-sibling.png'),fullPage:true});
 evidence.checks.push('Separate intercepted presentation fixture: succeeded and failed siblings with blocked rejoin visible together; no owner writes');
 assert.deepEqual(evidence.errors,[]);evidence.status='passed';
}finally{
 if(page&&evidence.status!=='passed'){evidence.failure=await page.locator('body').innerText();await page.screenshot({path:resolve(output,'failure.png'),fullPage:true});}
 if(page)await page.evaluate(()=>fetch('/session/logout',{method:'POST'})).catch(()=>{});
 await writeFile(resolve(output,'evidence.json'),JSON.stringify(evidence,null,2)+'\n');await browser.close();
}
console.log('Concurrency review passed: '+output);
