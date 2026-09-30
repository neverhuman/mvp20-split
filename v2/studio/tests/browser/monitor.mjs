import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { startObservationHost } from './host.mjs';
import { detail } from '../../dist/tests/fixtures/observations.js';

const output = resolve('../.test-results/studio-monitor', new Date().toISOString().replace(/[:.]/g,'-'));
await mkdir(output,{recursive:true});
const host = await startObservationHost();
const browser = await chromium.launch({ headless: true });
const evidence = { verified_at: new Intl.DateTimeFormat('sv-SE',{timeZone:'America/Chicago',dateStyle:'short',timeStyle:'medium'}).format(new Date()),
  timezone:'America/Chicago',status:'running',browser:browser.version(),scenarios:[],screenshots:[],limits:['Scripted HTTP peer, not live Runtime.','Local Chromium, no target-host or full screen-reader conformance claim.'] };
const id = index => index.toString(16).padStart(64,'0');
const deferred = () => { let release; const promise = new Promise(resolve => { release=resolve; }); return {promise,release}; };
const activeReleases = [];
try {
  for (const name of ['slow-detail','new-revision','denied','detail-denied','empty','cursor-expired','events-expired']) {
    host.state.mode = name === 'empty' ? 'empty' : name === 'cursor-expired' ? 'paged' : 'ready';
    host.state.revision=1; host.state.hook=null; host.state.requests=[]; host.state.responses=[];
    const context = await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
    const page = await context.newPage(); const errors=[]; page.on('pageerror',error=>errors.push(error.message));
    await page.goto(host.url);
    await page.waitForFunction(() => ['ready','empty'].includes(window.observationHarness.model.snapshot.phase));
    const choose = async index => { const button = page.locator(`.node-list button[data-node-id="${id(index)}"]`); await button.focus(); await page.keyboard.press('Enter'); };
    const currentDetail = async (index,revision=1) => page.waitForFunction(({id,revision})=> {
      const detail=window.observationHarness.model.snapshot.detail; return detail?.node.activation_id===id && detail.cut.revision===revision;
    },{id:id(index),revision});
    const start=performance.now();
    if (name === 'slow-detail' || name === 'new-revision') {
      const entered=deferred(), gate=deferred(), returned=deferred(); activeReleases.push(gate.release);
      let held=false;
      host.state.hook = async (url,json) => {
        if (!held && url.pathname.endsWith('/nodes/'+id(1))) {
          held=true; entered.release(); await gate.promise; json(200,detail(1,1)); returned.release(); return true;
        }
        return false;
      };
      await choose(1); await entered.promise;
      await page.getByText('Loading selected detail…',{exact:true}).waitFor();
      if (name === 'slow-detail') {
        await page.screenshot({path:resolve(output,'slow-detail-pending.png'),fullPage:true});
        evidence.screenshots.push('slow-detail-pending.png');
      }
      assert.equal(await page.locator('.node-list button').nth(1).isEnabled(),true);
      if (name === 'slow-detail') { await choose(2); await currentDetail(2); }
      else { host.state.revision=2; await page.getByRole('button',{name:'Refresh observation',exact:true}).click(); await currentDetail(1,2); }
      gate.release(); await returned.promise;
      await page.evaluate(() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
      const actual=await page.evaluate(()=>({selection:window.observationHarness.model.snapshot.selection,revision:window.observationHarness.model.snapshot.detail?.cut.revision}));
      assert.deepEqual(actual,{selection:id(name==='slow-detail'?2:1),revision:name==='slow-detail'?1:2});
      assert.equal(await page.getByRole('region',{name:'Selected node',exact:true}).getByRole('heading',{name:name==='slow-detail'?'node-2':'node-1',exact:true}).count(),1);
    } else if (name === 'denied') {
      await choose(1); await currentDetail(1); host.state.mode='denied';
      await page.getByRole('button',{name:'Check for updates',exact:true}).click();
      await page.waitForFunction(()=>window.observationHarness.model.snapshot.phase==='denied');
      assert.equal(await page.locator('.node-list button').count(),0);
      assert.equal(await page.locator('.react-flow__node').count(),0);
      assert.equal(await page.getByText('node-1',{exact:true}).count(),0);
      assert.equal((await page.locator('body').textContent()).includes('private server diagnostics'),false);
    } else if (name === 'detail-denied') {
      await choose(1); await currentDetail(1);
      await page.getByRole('button',{name:'Pin loaded inspection',exact:true}).click();
      await page.getByRole('region',{name:'Pinned inspection',exact:true}).waitFor();
      await page.getByLabel('Inspect',{exact:true}).selectOption('');
      host.state.hook=async(url,json)=> { if(url.pathname.endsWith('/nodes/'+id(1))){json(403,{detail:'private detail'});return true;}return false; };
      await choose(1); await page.getByText('Access to this detail is denied.',{exact:true}).waitFor();
      assert.equal(await page.locator('.node-list button').count(),2);
      assert.equal(await page.locator('#inspection-history option').count(),1);
    } else if (name === 'empty') {
      await page.getByText('No activations in this scope.',{exact:true}).waitFor();
      assert.equal(await page.locator('.react-flow__node').count(),0);
      assert.equal(await page.getByRole('button',{name:'Load next page',exact:true}).isDisabled(),true);
    } else if (name === 'cursor-expired') {
      host.state.hook=async(url,json)=> {if(url.searchParams.has('cursor')){json(410,{detail:'expired'});return true;}return false;};
      await page.getByRole('button',{name:'Load next page',exact:true}).click();
      await page.getByText('Observation expired or changed. Refresh to continue.',{exact:true}).waitFor();
      assert.equal(await page.locator('.node-list button').first().isDisabled(),true);
      host.state.revision=2; host.state.mode='ready';host.state.hook=null;
      await page.getByRole('button',{name:'Refresh observation',exact:true}).click();
      await page.waitForFunction(()=>window.observationHarness.model.snapshot.window?.snapshot.cut.revision===2);
    } else if (name === 'events-expired') {
      let expired=false;
      host.state.hook=async(url,json)=> {if(!expired && url.pathname.endsWith('/invalidations')){expired=true;host.state.revision=2;json(410,{detail:'expired'});return true;}return false;};
      await page.getByRole('button',{name:'Check for updates',exact:true}).click();
      await page.waitForFunction(()=>window.observationHarness.model.snapshot.window?.snapshot.cut.revision===2);
      assert.equal(host.state.requests.filter(request=>request.path.endsWith('/nodes')).length,2);
    }
    for(const viewport of [{width:1440,height:1000},{width:390,height:844}]) {
      await page.setViewportSize(viewport);
      await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
      const scan=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
      assert.deepEqual(scan.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),[]);
      const filename=`${name}-${viewport.width}.png`;await page.screenshot({path:resolve(output,filename),fullPage:true});evidence.screenshots.push(filename);
    }
    assert.deepEqual(errors,[]);
    evidence.scenarios.push({name,status:'passed',elapsed_ms:Math.round(performance.now()-start),requests:host.state.requests});
    await context.close();
  }
  evidence.status='passed';
} catch(error){evidence.status='failed';evidence.error=String(error);process.exitCode=1;}
finally {
  for(const release of activeReleases)release();
  await writeFile(resolve(output,'manifest.json'),JSON.stringify(evidence,null,2));
  console.log(JSON.stringify({status:evidence.status,manifest:resolve(output,'manifest.json'),scenarios:evidence.scenarios.map(s=>s.name),error:evidence.error}));
  await browser.close();await new Promise(resolve=>host.server.close(resolve));
}
