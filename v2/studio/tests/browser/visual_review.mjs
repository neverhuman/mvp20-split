/** Supplement existing narrow/keyboard suites with explicit 200% CSS layout stress. */
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import { startObservationHost } from './host.mjs';
import { startDraftHost } from './draft_host.mjs';

const output=resolve('../.test-results/studio-visual-review',new Date().toISOString().replace(/[:.]/g,'-'));
await mkdir(output,{recursive:true});
const browser=await chromium.launch({headless:true});
const evidence={status:'running',browser:browser.version(),cases:[],limits:['Scripted public peers supplement actual-owner journeys.','CSS zoom200% is a layout stress check, not native browser/text zoom or full screen-reader conformance.']};
try{
  for(const mode of ['monitor','design']){
    const host=await(mode==='monitor'?startObservationHost():startDraftHost());
    const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
    const page=await context.newPage(),errors=[];page.on('pageerror',error=>errors.push(error.message));
    try{
      await page.goto(host.url+(mode==='monitor'?'/?emergency=1':''));
      await page.waitForFunction(mode=>mode==='monitor'?window.observationHarness.model.snapshot.phase==='ready':window.draftHarness.catalog.snapshot.phase==='ready',mode);
      await page.evaluate(()=>{document.body.style.zoom='2';});
      const names=mode==='monitor'?['Refresh observation','Pin loaded inspection','Request emergency stop']:['Save draft','Compare with saved revision'];
      for(const name of names){
        const control=page.getByRole('button',{name,exact:true});assert.equal(await control.isEnabled(),true);
        await control.focus();await control.scrollIntoViewIfNeeded();
        const box=await control.boundingBox();assert.ok(box&&box.x>=0&&box.x+box.width<=1441&&box.y>=0&&box.y+box.height<=1001);
        assert.equal(await control.evaluate(element=>element===document.activeElement),true);
      }
      if(mode==='design'){
        await page.keyboard.press('Enter');
        await page.getByRole('region',{name:'Draft comparison',exact:true}).waitFor();
      }
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);
      assert.deepEqual((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations.map(value=>value.id),[]);
      assert.deepEqual(errors,[]);
      await page.screenshot({path:resolve(output,mode+'-zoom200.png'),fullPage:true});
      evidence.cases.push({mode,css_zoom:2,essential_controls:names,status:'passed'});
    }finally{await context.close();host.server.closeAllConnections();await new Promise(resolve=>host.server.close(resolve));}
  }
  evidence.status='passed';
}catch(error){evidence.status='failed';evidence.error=String(error);throw error;}
finally{await writeFile(resolve(output,'manifest.json'),JSON.stringify(evidence,null,2));await browser.close();console.log(JSON.stringify({status:evidence.status,output}));}
