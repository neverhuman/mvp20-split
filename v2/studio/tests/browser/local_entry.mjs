import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { createInterface } from 'node:readline';
import { once } from 'node:events';
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import { context, snapshot, detail, events } from '../../dist/tests/fixtures/observations.js';

const output=resolve('../.test-results/studio-local-entry',new Date().toISOString().replace(/[:.]/g,'-'));
await mkdir(output,{recursive:true});
const fixture=resolve(output,'fixture.json');
await writeFile(fixture,JSON.stringify({scope:context.scope,run:context.run,snapshot:snapshot(),detail:detail(1),events:events([])}));
const key='synthetic-gateway-launcher-fixture-key-123456789';
const browser=await chromium.launch({headless:true});
const evidence={checked_at:new Intl.DateTimeFormat('sv-SE',{timeZone:'America/Chicago',dateStyle:'short',timeStyle:'medium'}).format(new Date()),status:'running',scenarios:[],screenshots:[],limits:['Actual gateway and built Studio; synthetic Runtime HTTP peer.','No six-owner deployment or scientific-validity claim.']};
try {
  for (const selected of [false,true]) {
    const process=spawn(globalThis.process.env.AMPHORA_GATEWAY_TEST_PYTHON ?? resolve('../dev/.venv/Scripts/python.exe'),[resolve('../services/local_gateway/tests/browser/fixture_host.py'),
      '--public',resolve('dist/local'),'--fixture',fixture,...(selected?['--selected']:[])],
      {env:{...globalThis.process.env,PYTHONUTF8:'1',GATEWAY_FIXTURE_KEY:key},windowsHide:true,stdio:['ignore','pipe','pipe']});
    const exited=once(process,'exit');
    try {
      const lines=createInterface({input:process.stdout});
      const ready=await Promise.race([once(lines,'line'),exited.then(()=>{throw new Error('gateway_fixture_exited');}),new Promise((_,reject)=>setTimeout(()=>reject(new Error('gateway_fixture_timeout')),15000).unref())]);
      const {url}=JSON.parse(ready[0]);
      const browserContext=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
      const page=await browserContext.newPage();const errors=[];page.on('pageerror',error=>errors.push(error.message));
      await page.goto(url);
      try { await page.getByRole('heading',{name:'Open a new workspace session'}).waitFor({timeout:10000}); }
      catch(error) { await writeFile(resolve(output,'entry-failure.json'),JSON.stringify({errors,body:await page.locator('body').innerText()},null,2));await page.screenshot({path:resolve(output,'entry-failure.png')});throw error; }
      const issued=await browserContext.request.post(url+'/launcher/ticket',{headers:{Authorization:'Bearer '+key}});
      assert.equal(issued.status(),200);const {ticket}=await issued.json();
      await page.goto(url+'/#launch='+ticket);
      try { await page.getByRole('heading',{name:selected?'Follow execution':'No campaign selected',exact:true}).waitFor({timeout:10000}); }
      catch(error) { await writeFile(resolve(output,'session-failure.json'),JSON.stringify({errors,body:await page.locator('body').innerText()},null,2));await page.screenshot({path:resolve(output,'session-failure.png')});throw error; }
      assert.equal(await page.evaluate(()=>location.hash),'');
      assert.equal(await page.evaluate(()=>localStorage.length),0);
      const cookies=await browserContext.cookies();assert.equal(cookies.length,1);assert.equal(cookies[0].httpOnly,true);assert.equal(cookies[0].sameSite,'Strict');
      if(selected) {await page.locator('.node-list button').first().waitFor();assert.equal(await page.locator('.node-list button').count(),2);}
      for (const viewport of [{width:1440,height:1000},{width:390,height:844}]) {
        await page.setViewportSize(viewport);
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
        const name=(selected?'monitor':'empty')+'-'+viewport.width+'.png';await page.screenshot({path:resolve(output,name),fullPage:true});evidence.screenshots.push(name);
        const accessibility=await new AxeBuilder({page}).analyze();assert.equal(accessibility.violations.filter(v=>['serious','critical'].includes(v.impact)).length,0);
      }
      await page.evaluate(()=>fetch('/session/logout',{method:'POST',credentials:'same-origin'}));
      await page.reload();await page.getByRole('heading',{name:'Open a new workspace session'}).waitFor();
      if (!selected) {
        let release;const held=new Promise(resolve=>{release=resolve;});
        await page.route('**/session',async route=>{await held;await route.fulfill({status:503,contentType:'application/json',body:'{"error":"unavailable"}'});});
        await page.reload();await page.getByRole('heading',{name:'Opening your workspace'}).waitFor();
        await page.screenshot({path:resolve(output,'loading-390.png')});evidence.screenshots.push('loading-390.png');
        release();await page.getByRole('heading',{name:'Workspace unavailable'}).waitFor();
        await page.screenshot({path:resolve(output,'failed-390.png')});evidence.screenshots.push('failed-390.png');
        await page.unroute('**/session');
        evidence.scenarios.push('browser-injected slow/unavailable session (presentation only)');
      }
      assert.deepEqual(errors,[]);evidence.scenarios.push(selected?'authenticated Monitor fixture':'authenticated empty workspace');
      await browserContext.close();
    } finally {process.kill();await exited;}
  }
  evidence.status='passed';
} finally {await browser.close();await writeFile(resolve(output,'evidence.json'),JSON.stringify(evidence,null,2));}
console.log('Actual gateway/Studio browser entry verified:',output);
