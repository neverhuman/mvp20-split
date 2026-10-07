/** Actual local gateway and owner history; no synthetic HTTP peers or provider access. */
import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';

const input = JSON.parse(await readFile(process.argv[2], 'utf8'));
const output = resolve(process.argv[3]);
const key = process.env.AMPHORA_BROWSER_LAUNCH_KEY;
assert.ok(key);
const browser = await chromium.launch({headless:true});
const evidence = {status:'running', run_id:input.run_id, scenarios:[], screenshots:[], reads:[]};
try {
  for (const viewport of [{width:1440,height:1000},{width:390,height:844}]) {
    const context = await browser.newContext({viewport,reducedMotion:'reduce'});
    try {
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(input.origin);
      await page.getByRole('heading',{name:'Open a new workspace session'}).waitFor();
      const issued = await context.request.post(input.origin+'/launcher/ticket',{headers:{Authorization:'Bearer '+key}});
      assert.equal(issued.status(),200);
      const {ticket} = await issued.json();
      const selection = new URLSearchParams({explore:JSON.stringify({graph:input.records.snapshot.reference,experiment:null,observations:[]})});
      await page.goto(input.origin+'/#'+selection+'&launch='+ticket);
      await page.getByRole('heading',{name:'Follow execution',exact:true}).waitFor();
      await page.locator('.node-list button').first().waitFor();
      assert.equal(await page.evaluate(()=>new URLSearchParams(location.hash.slice(1)).has('launch')),false);
      assert.equal(await page.evaluate(()=>localStorage.length),0);
      assert.ok((await context.cookies()).every(cookie=>cookie.httpOnly && cookie.sameSite==='Strict'));
      await page.screenshot({path:resolve(output,'execution-'+viewport.width+'.png'),fullPage:true});
      evidence.screenshots.push('execution-'+viewport.width+'.png');
      const reasoning = page.getByRole('button',{name:'Inspect checkpoint reasoning'});
      await reasoning.focus(); await page.keyboard.press('Enter');
      await page.getByRole('button',{name:'review-numeric-seed',exact:true}).click();
      await page.getByRole('button',{name:'Inspect request 1',exact:true}).click();
      await page.getByRole('button',{name:'Context',exact:true}).click();
      await page.getByText('Included: knowledge',{exact:true}).waitFor();
      await page.getByRole('button',{name:'Responses',exact:true}).click();
      await page.getByText('Selected by the committed outcome',{exact:true}).waitFor();
      await page.locator('.supervision-records').getByText('Attempt 1: Scientific abstention',{exact:true}).waitFor();
      assert.ok((await page.getByLabel('Authoritative checkpoint outcome').innerText()).includes('Model accepted: abstained'));
      const axe = await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
      assert.deepEqual(axe.violations.filter(row=>['serious','critical'].includes(row.impact)),[]);
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Horizontal page overflow');
      await page.screenshot({path:resolve(output,'reasoning-'+viewport.width+'.png'),fullPage:true});
      evidence.screenshots.push('reasoning-'+viewport.width+'.png');
      await page.getByRole('button',{name:'Domain and evidence',exact:true}).click();
      await page.getByRole('heading',{name:'Follow the evidence',exact:true}).waitFor();
      await page.locator('.explore-concepts button').first().waitFor();
      assert.equal(await page.locator('.explore-concepts button').count(),2);
      await page.locator('.explore-concepts button').first().click();
      await page.getByRole('heading',{name:'Connected knowledge',exact:true}).waitFor();
      await page.locator('.explore-claims button').first().click();
      await page.getByLabel('Scientific evidence inspector').getByText('hypothesis / affirmed',{exact:true}).waitFor();
      await page.getByRole('button',{name:'Read source passage 1',exact:true}).click();
      // Original immutable source is octet-stream; the text viewer must refuse it.
      await page.getByLabel('Scientific evidence inspector').getByText('The selected evidence is unavailable.',{exact:true}).waitFor();
      await page.getByRole('button',{name:'Inspect applicability',exact:true}).click();
      await page.getByRole('heading',{name:'Verified artifact',exact:true}).waitFor();
      const domainAxe = await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
      assert.deepEqual(domainAxe.violations.filter(row=>['serious','critical'].includes(row.impact)),[]);
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Domain page overflow');
      await page.screenshot({path:resolve(output,'domain-'+viewport.width+'.png'),fullPage:true});
      evidence.screenshots.push('domain-'+viewport.width+'.png');
      await page.getByRole('button',{name:'Execution',exact:true}).click();
      await page.getByRole('heading',{name:'Follow execution',exact:true}).waitFor();
      await page.getByRole('heading',{name:'Checkpoint reasoning',exact:true}).waitFor();
      // API trace uses the same authenticated browser context and actual fixed owner routes.
      const trace = await page.evaluate(async input => {
        async function read(path, body) {
          const response = await fetch(path,{method:body===undefined?'GET':'POST',credentials:'same-origin',
            headers:{'Content-Type':'application/json'},...(body===undefined?{}:{body:JSON.stringify(body)})});
          if (!response.ok) throw new Error('owner_trace_'+response.status);
          return response.json();
        }
        const graph = await read('/api/runtime/v1/graph-observations/'+input.run_id+'/nodes?limit=100');
        const question = await read('/api/research/v1/questions/read',input.records.question.reference);
        const need = await read('/api/research/v1/evidence-needs/read',input.records.need.reference);
        const snapshot = await read('/api/knowledge/v1/graph-snapshots/read',input.records.snapshot.reference);
        const context = await read('/api/data/v1/artifacts/'+input.context.artifact_id+'/content');
        const objective = await fetch('/api/data/v1/artifacts/'+input.objective.artifact_id+'/content',{credentials:'same-origin'});
        if (!objective.ok) throw new Error('objective_unavailable');
        return {graph,question,need,snapshot,context,objective:await objective.text()};
      },input);
      assert.equal(trace.graph.snapshot.status,'completed');
      assert.equal(trace.graph.nodes.length,input.expected_nodes);
      assert.deepEqual(trace.question,input.records.question);
      assert.deepEqual(trace.need,input.records.need);
      assert.deepEqual(trace.snapshot,input.records.snapshot);
      assert.equal(trace.context.profile,'synthetic-demo-context.v1');
      assert.ok(trace.objective.includes('synthetic numeric seed'));
      // A navigation link cannot select another project or initiate owner reads for it.
      let foreignReads = 0;
      page.on('request', request => { if (request.url().includes('/api/knowledge/')) foreignReads++; });
      const foreign = structuredClone(input.records.snapshot.reference);
      foreign.graph.scope.project_id = 'foreign-project';
      await page.evaluate(value => { location.hash = new URLSearchParams({explore:JSON.stringify({graph:value,experiment:null,observations:[]})}).toString(); },foreign);
      await page.getByRole('button',{name:'Domain and evidence',exact:true}).click();
      await page.getByRole('heading',{name:'Research context unavailable',exact:true}).waitFor();
      assert.equal(foreignReads,0);
      await page.getByRole('button',{name:'Execution',exact:true}).click();
      await page.getByRole('heading',{name:'Follow execution',exact:true}).waitFor();
      assert.deepEqual(errors,[]);
      evidence.reads.push({width:viewport.width,graph_nodes:trace.graph.nodes.length,question:trace.question.reference,
        knowledge_snapshot:trace.snapshot.reference,context_assertions:trace.context.assertions.length});
      evidence.scenarios.push(viewport.width+': actual execution, keyboard reasoning, selected abstention, required knowledge, domain navigation and hypothesis, public owner trace, accessibility');
    } catch (error) {
      const failedPage = context.pages()[0];
      if (failedPage) {
        await failedPage.screenshot({path:resolve(output,'failure.png'),fullPage:true});
        await writeFile(resolve(output,'failure.txt'),await failedPage.locator('body').innerText());
      }
      throw error;
    } finally { await context.close(); }
  }
  evidence.status='passed';
} finally {
  await browser.close();
  await writeFile(resolve(output,'browser-evidence.json'),JSON.stringify(evidence,null,2)+'\n');
}
