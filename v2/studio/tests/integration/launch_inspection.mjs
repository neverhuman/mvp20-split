/** Read-only inspection of a retained browser launch; never submits a campaign. */
import {chromium} from 'playwright';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const input=JSON.parse(await readFile(process.argv[2],'utf8')),output=resolve(process.argv[3]);
const entries=JSON.parse(await readFile(process.argv[4],'utf8'));
await mkdir(output,{recursive:true});
const browser=await chromium.launch({headless:true,args:input.tls_spki?['--ignore-certificate-errors-spki-list='+input.tls_spki]:[]});
try{
 const context=await browser.newContext({viewport:{width:1440,height:1000}});
 await context.addInitScript(({origin,entries})=>{if(location.origin===origin)for(const [key,value] of entries)localStorage.setItem(key,value);},{origin:input.origin,entries});
 const issued=await context.request.post(input.origin+'/launcher/ticket',{headers:{Authorization:'Bearer '+process.env.AMPHORA_BROWSER_LAUNCH_KEY}});
 assert.equal(issued.status(),200);const {ticket}=await issued.json();
 const page=await context.newPage(),reads=[];
 page.on('response',async response=>{if(response.url().includes('/api/'))reads.push({url:response.url(),status:response.status()});});
 await page.goto(input.origin+'/#view=execution&launch='+encodeURIComponent(ticket));
 await page.waitForTimeout(15000);
 await page.screenshot({path:resolve(output,'inspection.png'),fullPage:true});
 await writeFile(resolve(output,'inspection.json'),JSON.stringify({body:await page.locator('body').innerText(),reads},null,2));
}finally{await browser.close();}
