/** Bounded synthetic branch topology; no execution or scientific validity claim. */
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { startObservationHost } from './host.mjs';
import { scopes, topology, catalog } from '../../dist/tests/fixtures/navigation.js';
import { snapshot, node, detail, id } from '../../dist/tests/fixtures/observations.js';

const output=resolve('../.test-results/studio-dense-navigation',new Date().toISOString().replace(/[:.]/g,'-'));
await mkdir(output,{recursive:true});
const host=await startObservationHost();
const nodes=Array.from({length:256},(_,i)=>node(i+1));
nodes[0].path.node_id='branch_'+ 'long_context_'.repeat(8);
nodes[0].kind='branch'; nodes[199].status='failed'; nodes[199].reason_code='synthetic_failure';
const edges=nodes.slice(1).map(n=>({source:id(1),target:n.activation_id,route:'true'}));
const group={...scopes().scopes[0],node_count:256};
host.state.hook=async(url,json)=>{
  if(url.pathname.endsWith('/views')){json(200,catalog());return true;}
  if(url.pathname.endsWith('/scopes')){json(200,{...scopes(),scopes:[group]});return true;}
  if(url.pathname.endsWith('/topology')){
    const offset=Number(url.searchParams.get('cursor')??0),end=Math.min(offset+50,256);
    json(200,{...topology(),graph_scope:group,node_count:256,edge_count:255,
      nodes:nodes.slice(offset,end).map(activation=>({activation,child_scope_count:0})),edges:offset===0?edges:[],next_cursor:end<256?String(end):null});return true;
  }
  if(url.pathname.endsWith('/nodes')){
    json(200,{...snapshot({ids:[],total:256,next:'inventory-next'}),nodes:nodes.slice(0,50)});return true;
  }
  if(url.pathname.includes('/nodes/')){
    const index=Number.parseInt(url.pathname.split('/').at(-1),16);
    json(200,{...detail(index),node:nodes[index-1]});return true;
  }
  return false;
};
const browser=await chromium.launch({headless:true});
const result={status:'running',browser:browser.version(),scenarios:[],limits:['Synthetic public HTTP peer; no target-host performance or scientific validity claim.']};
try{
  const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
  const page=await context.newPage();
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  await page.goto(host.url+'/?navigation=1');
  await page.getByRole('button',{name:'Authored graph',exact:true}).click();
  await page.getByRole('list',{name:'Occurrence groups',exact:true}).getByRole('button').click();
  await page.waitForFunction(()=>window.observationHarness.navigation.snapshot.topology?.page.nodes.length===50);
  await page.waitForFunction(() => document.querySelectorAll('.react-flow__edge').length === 49);
  assert.equal(await page.locator('.react-flow__edge').count(),49);
  for(const count of [100,150,200,250,256]){
    await page.getByRole('button',{name:'Load topology page',exact:true}).click();
    await page.waitForFunction(count=>window.observationHarness.navigation.snapshot.topology?.page.nodes.length===count,count);
  }
  await page.waitForFunction(() => document.querySelectorAll('.react-flow__node').length === 200);
  assert.equal(await page.locator('.react-flow__node').count(),200);
  await page.waitForFunction(() => document.querySelectorAll('.react-flow__edge').length === 199);
  assert.equal(await page.locator('.react-flow__edge').count(),199);
  await page.getByRole('list',{name:'Topology nodes',exact:true}).getByRole('button',{name:'node-200 failed',exact:true}).click();
  await page.getByRole('region',{name:'Selected node',exact:true}).getByRole('heading',{name:'node-200',exact:true}).waitFor();
  await page.getByRole('button',{name:'Next window',exact:true}).click();
  await page.waitForFunction(() => document.querySelectorAll('.react-flow__node').length === 56);
  assert.equal(await page.locator('.react-flow__node').count(),56);
  await page.waitForFunction(() => document.querySelectorAll('.react-flow__edge').length === 0);
  assert.equal(await page.locator('.react-flow__edge').count(),0);
  await page.getByText('Selected activation is outside this window.',{exact:true}).waitFor();
  await page.getByRole('button',{name:'First window',exact:true}).click();
  for(const viewport of [{width:1440,height:1000},{width:390,height:844}]){
    await page.setViewportSize(viewport);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    assert.deepEqual((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations.map(v=>v.id),[]);
    await page.screenshot({path:resolve(output,`dense-${viewport.width}.png`),fullPage:true});
  }
  assert.deepEqual(errors,[]);
  result.scenarios=['256-node branch in six bounded pages','long label','failed activation inspection','200/56 scene windows omit crossing edges and preserve selection'];
  result.status='passed';
}catch(error){result.status='failed';result.error=String(error);throw error;}
finally{await writeFile(resolve(output,'manifest.json'),JSON.stringify(result,null,2));await browser.close();host.server.closeAllConnections();await new Promise(resolve=>host.server.close(resolve));console.log(output);}
