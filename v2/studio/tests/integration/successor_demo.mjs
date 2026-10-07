/** Retained actual successor lineage and artifact readback through the local gateway. */
import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';

const input=JSON.parse(await readFile(process.argv[2],'utf8'));
const output=resolve(process.argv[3]);
assert.ok(input.successor && process.env.AMPHORA_BROWSER_LAUNCH_KEY);
const browser=await chromium.launch({headless:true});
const evidence={status:'running',run_id:input.run_id,scenarios:[],screenshots:[],reads:[]};
try {
  for (const viewport of [{width:1440,height:1000},{width:390,height:844}]) {
    const context=await browser.newContext({viewport,reducedMotion:'reduce'});
    const page=await context.newPage(),errors=[];
    page.on('pageerror',error=>errors.push(error.message));
    try {
      const issued=await context.request.post(input.origin+'/launcher/ticket',
        {headers:{Authorization:'Bearer '+process.env.AMPHORA_BROWSER_LAUNCH_KEY}});
      assert.equal(issued.status(),200);
      const {ticket}=await issued.json();
      await page.goto(input.origin+'/#launch='+ticket);
      await page.getByRole('heading',{name:'Follow execution',exact:true}).waitFor();
      const node=page.getByRole('list',{name:'Loaded activation list'}).getByRole('button').first();
      await node.focus();await page.keyboard.press('Enter');
      await page.getByRole('button',{name:'Inspect output result',exact:true}).click();
      await page.getByRole('button',{name:/^Inspect artifact /}).first().click();
      await page.getByRole('heading',{name:'Artifact metadata',exact:true}).waitFor();
      await page.screenshot({path:resolve(output,'successor-output-'+viewport.width+'.png'),fullPage:true});
      evidence.screenshots.push('successor-output-'+viewport.width+'.png');
      await page.getByRole('button',{name:'Authored graph',exact:true}).click();
      await page.getByRole('list',{name:'Occurrence groups',exact:true}).getByRole('button').first().click();
      await page.getByText('Named research views',{exact:true}).click();
      await page.getByRole('button',{name:'Inspect predecessor lineage',exact:true}).click();
      const lineage=page.getByRole('region',{name:'Retained predecessor lineage',exact:true});
      await lineage.waitFor();
      assert.ok((await lineage.innerText()).includes(input.successor.predecessor.run_id));
      assert.ok((await lineage.innerText()).includes('1 explicit carried bindings'));
      assert.ok((await lineage.innerText()).includes('previous_result'));
      const axe=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
      assert.deepEqual(axe.violations.filter(row=>['serious','critical'].includes(row.impact)),[]);
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
      await page.screenshot({path:resolve(output,'successor-lineage-'+viewport.width+'.png'),fullPage:true});
      evidence.screenshots.push('successor-lineage-'+viewport.width+'.png');
      const trace=await page.evaluate(async input=>{
        async function read(path) {
          const response=await fetch(path,{credentials:'same-origin'});
          if(!response.ok)throw new Error('successor_read_'+response.status);
          return response.json();
        }
        const root='/api/runtime/v1/graph-runs/';
        const lineage=await read(root+input.run_id+'/lineage');
        const sources=await read(root+input.run_id+'/carry-sources');
        const parent=await read(root+input.successor.predecessor.run_id+'/carry-sources');
        const receipt=await read('/api/runtime/v1/commands/graph.admit_draft_successor/'+input.successor.admission_command_id);
        const graph=await read('/api/runtime/v1/graph-observations/'+input.run_id+'/nodes?limit=100');
        const values=await read('/api/runtime/v1/graph-observations/'+input.run_id+'/nodes/'+graph.nodes[0].activation_id+'/outputs/result?snapshot_token='+encodeURIComponent(graph.snapshot.snapshot_token));
        const artifact=values.items[0].value.artifact;
        const metadata=await read('/api/data/v1/artifacts/'+artifact.artifact_id);
        const response=await fetch('/api/data/v1/artifacts/'+artifact.artifact_id+'/content',{credentials:'same-origin'});
        if(!response.ok)throw new Error('carried_content_'+response.status);
        const bytes=await response.arrayBuffer();
        const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),n=>n.toString(16).padStart(2,'0')).join('');
        return {lineage,sources,parent,receipt,artifact,metadata,digest,size:bytes.byteLength};
      },input);
      assert.deepEqual(trace.lineage,input.successor.lineage);
      assert.deepEqual(trace.receipt,input.successor.receipt);
      assert.deepEqual(trace.sources,input.successor.child_sources);
      assert.deepEqual(trace.parent,input.successor.sources);
      assert.deepEqual(trace.metadata,trace.artifact);
      assert.equal(trace.digest,trace.artifact.sha256);assert.equal(trace.size,trace.artifact.size_bytes);
      assert.equal(await page.evaluate(()=>location.hash),'');assert.equal(await page.evaluate(()=>localStorage.length),0);
      if(input.successor.correction) {
        const correction=input.successor.correction;
        const records=await page.evaluate(async input=>{
          const response=await fetch('/api/runtime/v1/graph-observations/'+input.run_id+'/nodes?limit=100');
          const graph=await response.json();
          const values=await fetch('/api/runtime/v1/graph-observations/'+input.run_id+'/nodes/'+graph.nodes[0].activation_id+'/outputs/interpretation?snapshot_token='+encodeURIComponent(graph.snapshot.snapshot_token));
          if(!values.ok)throw new Error('corrected_output_'+values.status);
          return values.json();
        },input);
        assert.deepEqual(records.items[0].value.artifact,correction.artifact);
        for(const [revision,posture] of [[input.records.snapshot.reference,'hypothesis'],[correction.snapshot.reference,'unresolved']]) {
          await page.evaluate(graph=>{location.hash=new URLSearchParams({explore:JSON.stringify({graph,experiment:null,observations:[]})}).toString();},revision);
          await page.getByRole('button',{name:'Domain and evidence',exact:true}).click();
          await page.getByRole('heading',{name:'Follow the evidence',exact:true}).waitFor();
          await page.locator('.explore-concepts button').first().waitFor();
          await page.locator('.explore-concepts button').first().click();
          await page.getByRole('heading',{name:'Connected knowledge',exact:true}).waitFor();
          const claim=page.locator('.explore-claims li').filter({hasText:posture+' / affirmed'});
          await claim.getByRole('button').click();
          await page.getByLabel('Scientific evidence inspector').getByText(posture+' / affirmed',{exact:true}).waitFor();
          await page.getByRole('button',{name:'Read source passage 1',exact:true}).click();
          if(posture==='unresolved') {
            const passage=page.getByRole('region',{name:'Verified source passage',exact:true});
            await passage.waitFor();
            assert.ok((await passage.innerText()).includes(correction.proposal.operations[0].replacement.statement));
            await passage.scrollIntoViewIfNeeded();
            await page.screenshot({path:resolve(output,'corrected-source-'+viewport.width+'.png'),fullPage:true});
            evidence.screenshots.push('corrected-source-'+viewport.width+'.png');
          } else {
            await page.getByLabel('Scientific evidence inspector').getByText('The selected evidence is unavailable.',{exact:true}).waitFor();
          }
          const domainAxe=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
          assert.deepEqual(domainAxe.violations.filter(row=>['serious','critical'].includes(row.impact)),[]);
          assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
          await page.getByRole('button',{name:'Execution',exact:true}).click();
        }
        evidence.scenarios.push(viewport.width+': original pinned hypothesis remains; corrected unresolved interpretation has verified text passage and exact successor output');
      }
      assert.deepEqual(errors,[]);
      evidence.reads.push({width:viewport.width,predecessor:trace.lineage.predecessor,carried:trace.lineage.carried,artifact:trace.artifact});
      evidence.scenarios.push(viewport.width+': actual retained result, keyboard inspection, authored successor topology, immutable lineage/receipt, exact artifact bytes, accessibility');
    } catch(error) {
      await page.screenshot({path:resolve(output,'failure.png'),fullPage:true});
      await writeFile(resolve(output,'failure.txt'),await page.locator('body').innerText());
      throw error;
    } finally {await context.close();}
  }
  evidence.status='passed';
} finally {
  await browser.close();
  await writeFile(resolve(output,'browser-evidence.json'),JSON.stringify(evidence,null,2)+'\n');
}
