/** Built production entry and independently installed owners/Gateway; supplied structure only. */
import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
import {X509Certificate,createHash} from 'node:crypto';
const input=JSON.parse(await readFile(process.argv[2],'utf8')),output=resolve(process.argv[3]);await mkdir(output,{recursive:true});
const spki=input.tls_certificate?createHash('sha256').update(new X509Certificate(await readFile(input.tls_certificate)).publicKey.export({type:'spki',format:'der'})).digest('base64'):null;
const browser=await chromium.launch({headless:true,args:spki?['--ignore-certificate-errors-spki-list='+spki]:[]});
const evidence={status:'running',stage:'ticket',run_id:input.run_id,scope:input.scope,tls_spki:spki,errors:[],reads:[],forbiddenWrites:[]};let context;
try{
 context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});const page=await context.newPage();
 page.on('pageerror',()=>evidence.errors.push('browser_exception'));
 page.on('request',request=>{const path=new URL(request.url()).pathname;if(request.method()!=='GET'&&path.startsWith('/api/')&&!path.endsWith('/read')&&!path.endsWith('/catalog'))evidence.forbiddenWrites.push(path);});
 page.on('response',response=>{const path=new URL(response.url()).pathname;if(path.endsWith('/producer')||path.endsWith('/candidates/read')||path.endsWith('/content'))evidence.reads.push({path,status:response.status()});});
 const issued=await context.request.post(input.origin+'/launcher/ticket',{headers:{Authorization:'Bearer '+process.env.AMPHORA_BROWSER_LAUNCH_KEY}});assert.equal(issued.status(),200);const {ticket}=await issued.json();
 evidence.stage='navigation';
 await page.goto(input.origin+'/#view=knowledge&launch='+encodeURIComponent(ticket));
 evidence.stage='discovery';
 const selection=page.getByLabel('Structure-producing step');await selection.waitFor({timeout:60000});
 const options=await selection.locator('option').evaluateAll(items=>items.map(item=>({value:item.value,label:item.textContent})));evidence.choices=options.map(option=>option.label);
 assert.equal(options.length,2,'One actual producing invocation, not forwarding nodes');await selection.selectOption(options[1].value);
 evidence.stage='structure';
 await page.getByText('C4H10O3',{exact:true}).waitFor({timeout:30000});
 assert.ok(await page.getByRole('img').evaluate(image=>image.complete&&image.naturalWidth===800&&image.naturalHeight===600));
 await page.getByText('Execution and artifact provenance',{exact:true}).click();
 await page.getByText(input.completion_id,{exact:false}).waitFor();
 await page.getByText(input.candidate.representation.sha256,{exact:true}).waitFor();
 await page.getByRole('button',{name:'Inspect producing execution step',exact:true}).click();
 await page.getByRole('region',{name:'Producing execution step',exact:true}).waitFor();
 for(const [width,zoom] of [[1440,1],[390,1],[1440,2]]){
  evidence.stage=`visual-${width}-${zoom}`;
  await page.setViewportSize({width,height:1000});await page.evaluate(zoom=>document.body.style.zoom=String(zoom),zoom);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  assert.deepEqual((await new AxeBuilder({page}).include('.candidate-results').withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations.map(v=>v.id),[]);
  await page.screenshot({path:resolve(output,`actual-${width}-${zoom}.png`),fullPage:true});
 }
 assert.ok(evidence.reads.some(read=>read.path.endsWith('/producer')&&read.status===200));
 assert.ok(evidence.reads.some(read=>read.path.endsWith('/candidates/read')&&read.status===200));
 assert.deepEqual(evidence.forbiddenWrites,[]);assert.deepEqual(evidence.errors,[]);
 evidence.stage='complete';evidence.status='passed';console.log('Actual candidate inspector passed: '+output);
}catch(error){evidence.status='failed';evidence.failure=error?.name??'qualification_failed';evidence.browser_code=/net::[A-Z_]+/.exec(String(error))?.[0]??null;throw new Error('actual_candidate_qualification_failed');}
finally{if(context)await context.request.post(input.origin+'/session/logout').catch(()=>undefined);await writeFile(resolve(output,'evidence.json'),JSON.stringify(evidence,null,2));await browser.close();}
