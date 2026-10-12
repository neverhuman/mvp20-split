import test from 'node:test';
import assert from 'node:assert/strict';
import {SuccessorSources} from '../../../src/transport/successor_launch/sources.js';
const value={scope:{tenant_id:'internal',project_id:'demo'},predecessor:{run_id:'parent',plan_sha256:'a'.repeat(64),revision:3},predecessor_ready:true,sources:[]};
test('carry discovery reads only exact run exports with browser credentials',async()=>{
  const source=new SuccessorSources((async(url,options)=>{
    assert.equal(url,'/api/runtime/v1/graph-runs/parent/carry-sources');assert.equal(options?.method,'GET');assert.equal(options?.body,undefined);
    assert.equal(options?.credentials,'same-origin');return Response.json(value);
  }) as typeof fetch);
  assert.deepEqual(await source.read('parent',new AbortController().signal),value);
  await assert.rejects(source.read('../foreign',new AbortController().signal));
});
test('foreign carry cut, denial and late response after abort cannot publish sources',async()=>{
  for(const variant of ['foreign','denied','aborted']){
    const controller=new AbortController(),source=new SuccessorSources((async()=>{
      if(variant==='aborted')controller.abort();return variant==='denied'?Response.json({}, {status:403}):Response.json({...value,predecessor:{...value.predecessor,run_id:variant==='foreign'?'other':'parent'}});
    }) as typeof fetch);
    await assert.rejects(source.read('parent',controller.signal));
  }
});
