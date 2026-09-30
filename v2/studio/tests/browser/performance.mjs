/** Production Monitor/GraphCanvas timing over a bounded synthetic public HTTP source. */
import assert from 'node:assert/strict';
import os from 'node:os';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium } from 'playwright';
import { startObservationHost } from './host.mjs';
import { snapshot, detail, id } from '../../dist/tests/fixtures/observations.js';

const recordOnly=process.argv.includes('--record-baseline');
const output=resolve('../.test-results/studio-performance',new Date().toISOString().replace(/[:.]/g,'-'));
await mkdir(output,{recursive:true});
const host=await startObservationHost(), packets=[];
host.state.hook=async(url,json)=>{
  if(!url.pathname.includes('/nodes')) return false;
  await delay(25); // Explicit fixture delay, not a claim about Runtime/database latency.
  let packet;
  if(url.pathname.endsWith('/nodes')){
    const offset=Number(url.searchParams.get('cursor')??0);
    assert.ok(Number.isSafeInteger(offset)&&offset>=0&&offset<10000&&offset%50===0);
    packet=snapshot({ids:Array.from({length:50},(_,index)=>offset+index+1),total:10000,next:offset+50<10000?String(offset+50):null});
  }else packet=detail(Number.parseInt(url.pathname.split('/').at(-1),16));
  packets.push({path:url.pathname,nodes:packet.nodes?.length??0,bytes:Buffer.byteLength(JSON.stringify(packet))});
  json(200,packet);return true;
};
const browser=await chromium.launch({headless:true});
const result={profile:'amphora-studio-performance-v1',status:'running',record_only:recordOnly,
  verified_at:new Intl.DateTimeFormat('sv-SE',{timeZone:'America/Chicago',dateStyle:'short',timeStyle:'medium'}).format(new Date()),timezone:'America/Chicago',
  machine:{platform:os.platform(),release:os.release(),arch:os.arch(),cpu:os.cpus()[0].model,logical_cpus:os.cpus().length,memory_gib:Math.round(os.totalmem()/2**30),node:process.version,browser:browser.version()},
  logical_nodes:10000,maximum_visible:200,maximum_response_nodes:50,fixture_delay_ms:25,samples:[],
  method:'Resource Timing measures request/response duration. Model-ready or native input event to matching DOM plus two animation frames measures a render-settlement proxy, not GPU/compositor frame time. Paged-200 records the final bounded append separately from navigation-to-200.',
  limits:['Synthetic source through production client/model/view, no scientific or live-owner throughput claim.','Fresh browser contexts are cold consumer contexts, not cold OS/process caches.','Local machine baseline, not DGX/Threadripper or universal performance.']};
try{
  for(const width of [1440,390]) for(let iteration=0;iteration<5;iteration++){
    const requestStart=packets.length;
    const context=await browser.newContext({viewport:{width,height:width===390?844:1000},reducedMotion:'reduce'});
    const page=await context.newPage(), errors=[];
    page.on('pageerror',error=>errors.push(error.message));
    await context.addInitScript(()=>{
      let harness;
      const probe={target:{kind:'graph',count:50,name:'cold_graph_50'},done:null};
      window.renderProbe=probe;
      const settle=target=>{
        if(target.modelReady!==undefined)return;
        target.modelReady=performance.now();
        const deadline=performance.now()+5000;
        const poll=()=>{
          const matches=target.kind==='detail'
            ? document.querySelector('[aria-label="Selected node"]')?.textContent.includes(target.label)
            : document.querySelectorAll('.react-flow__node').length===target.count;
          if(!matches){
            if(performance.now()>deadline){probe.done={error:'render_settlement_timeout'};return;}
            requestAnimationFrame(poll);return;
          }
          requestAnimationFrame(()=>requestAnimationFrame(()=>{
            const entry=performance.getEntriesByType('resource').filter(value=>value.initiatorType==='fetch'&&value.name.includes('/api/runtime/')).at(-1);
            const painted=performance.now();
            probe.done={name:target.name,model_to_paint_ms:painted-target.modelReady,
              request_ms:target.kind==='local'?0:entry.duration,
              response_to_model_ms:target.kind==='local'?null:target.modelReady-entry.responseEnd,
              navigation_to_paint_ms:painted,nodes:document.querySelectorAll('.react-flow__node').length};
          }));
        };
        requestAnimationFrame(poll);
      };
      Object.defineProperty(window,'observationHarness',{configurable:true,get:()=>harness,set:value=>{
        harness=value;value.model.subscribe(()=>{
          const view=value.model.snapshot,target=probe.target;
          if(target.kind==='graph'&&view.phase==='ready'&&view.window.nodes.length===target.count)settle(target);
          if(target.kind==='detail'&&view.detailPhase==='ready'&&view.detail?.node.activation_id===target.id)settle(target);
        });
      }});
      document.addEventListener('input',event=>{
        if(probe.target.kind==='local'&&event.target.id==='node-filter'&&event.target.value==='')settle(probe.target);
      },true);
    });
    const collect=async()=>{
      await page.waitForFunction(()=>window.renderProbe.done!==null);
      const sample=await page.evaluate(()=>window.renderProbe.done);assert.equal(sample.error,undefined);
      assert.ok(sample.model_to_paint_ms>=0&&sample.request_ms>=0);
      result.samples.push({...sample,width,iteration});return sample;
    };
    const arm=target=>page.evaluate(target=>{window.renderProbe.target=target;window.renderProbe.done=null;},target);
    await page.goto(host.url);await collect();
    for(const count of [100,150,200]){
      await arm({kind:'graph',count,name:count===200?'paged_graph_200':'intermediate_page'});
      await page.getByRole('button',{name:'Load next page',exact:true}).click();
      await collect();
    }
    assert.equal(await page.locator('.react-flow__node').count(),200);
    assert.equal(await page.getByRole('button',{name:'Load next page',exact:true}).isDisabled(),true);
    const loaded=await page.evaluate(()=>({nodes:window.observationHarness.model.snapshot.window.nodes.length,total:window.observationHarness.model.snapshot.window.snapshot.node_count}));
    assert.deepEqual(loaded,{nodes:200,total:10000});
    await page.getByRole('status').filter({hasText:'9800 outside this window'}).waitFor();
    const filter=page.getByLabel('Find in loaded nodes',{exact:true});
    const beforeLocal=packets.length;
    await filter.fill('absent-node');await page.waitForFunction(()=>document.querySelectorAll('.react-flow__node').length===0);
    await arm({kind:'local',count:200,name:'warm_graph_200'});await filter.fill('');await collect();
    assert.equal(packets.length,beforeLocal,'Local filtering fetched additional context');
    const index=100+iteration;
    await arm({kind:'detail',id:id(index),label:'node-'+index,name:'detail'});
    await page.locator(`.node-list button[data-node-id="${id(index)}"]`).focus();await page.keyboard.press('Enter');await collect();
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);
    assert.deepEqual(errors,[]);
    assert.equal(packets.length-requestStart,5,'Expected four50-node pages and one detail; no whole-universe download');
    if(iteration===0)await page.screenshot({path:resolve(output,`scene-${width}.png`),fullPage:true});
    await context.close();
  }
  result.packet_bounds={requests:packets.length,maximum_nodes:Math.max(...packets.map(value=>value.nodes)),maximum_bytes:Math.max(...packets.map(value=>value.bytes))};
  assert.ok(result.packet_bounds.maximum_nodes<=50&&result.packet_bounds.maximum_bytes<262144);
  const quantile=(values,p)=>[...values].sort((a,b)=>a-b)[Math.ceil(values.length*p)-1];
  result.summary=[];
  for(const width of [1440,390])for(const name of ['cold_graph_50','paged_graph_200','warm_graph_200','detail']){
    const samples=result.samples.filter(value=>value.width===width&&value.name===name);
    result.summary.push({width,name,count:samples.length,request_p95_ms:quantile(samples.map(value=>value.request_ms),.95),
      render_p50_ms:quantile(samples.map(value=>value.model_to_paint_ms),.5),render_p95_ms:quantile(samples.map(value=>value.model_to_paint_ms),.95)});
  }
  if(!recordOnly){
    const budget=JSON.parse(await readFile('tests/browser/performance_budget.json','utf8'));
    for(const field of ['platform','arch','cpu'])assert.equal(result.machine[field],budget.machine[field],'Performance profile changed; explicitly review/rebaseline');
    for(const row of result.summary){
      const ceiling=budget.render_p95_ms[row.name];assert.ok(row.render_p95_ms<=ceiling,`${row.name}/${row.width} render ${row.render_p95_ms.toFixed(1)}ms exceeds ${ceiling}ms`);
    }
    result.budget_profile=budget.profile;
  }
  result.status='passed';
}catch(error){result.status='failed';result.error=String(error);throw error;}
finally{
  await writeFile(resolve(output,'manifest.json'),JSON.stringify(result,null,2));
  await browser.close();host.server.closeAllConnections();await new Promise(resolve=>host.server.close(resolve));
  console.log(JSON.stringify({status:result.status,output,summary:result.summary,error:result.error}));
}
