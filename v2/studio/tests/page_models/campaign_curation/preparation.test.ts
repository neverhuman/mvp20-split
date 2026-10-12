import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { CurationPreparation,OriginalCurationContext,PreparedCuration } from '../../../src/page_models/campaign_curation/preparation.js';
import type { CurationRequest } from '../../../src/contracts/campaign_curation.js';
import type { GraphSnapshotPage } from '../../../src/contracts/observations.js';
import type { CampaignOrigin } from '../../../src/contracts/campaign_origin.js';
const request=JSON.parse(readFileSync('tests/fixtures/campaign_curation/commands.json','utf8'))[0].request as CurationRequest;
const actor={actor_id:request.identity.actor_id,scope:request.identity.scope,run_id:request.payload.context.predecessor.run_id};
function fixture(status='completed'){
  const context=structuredClone(request.payload.context);
  const page={snapshot:{cut:{scope:actor.scope,...context.predecessor},status}} as GraphSnapshotPage;
  const calls:string[]=[];
  const runtime={snapshot:async()=>{calls.push('snapshot');return page;}};
  const source={read:async()=>{calls.push('context');return context;}};
  return {context,page,calls,runtime,source,model:new CurationPreparation(actor,'synthetic',runtime,source)};
}
test('terminal cut is read before exact requested context is prepared',async()=>{
  const f=fixture();await f.model.load();assert.equal(f.model.snapshot.phase,'ready');assert.deepEqual(f.calls,['snapshot','context']);
  const command=f.model.snapshot.prepared!.request('Change the heating approach','revise');
  assert.deepEqual(command.payload.context,f.context);assert.equal(command.identity.actor_id,actor.actor_id);
  f.context.predecessor.revision=100;assert.equal(command.payload.context.predecessor.revision,9);
});
test('active predecessor does not read context or prepare a mutation',async()=>{
  const f=fixture('running');await f.model.load();assert.equal(f.model.snapshot.phase,'running');assert.deepEqual(f.calls,['snapshot']);assert.equal(f.model.snapshot.prepared,null);
});
test('foreign and changed predecessor cuts cannot be prepared',async()=>{
  for(const variant of ['foreign','changed']){
    const f=fixture();if(variant==='foreign')f.page.snapshot.cut.scope={...actor.scope,project_id:'other'};
    else f.source.read=async()=>({...f.context,predecessor:{...f.context.predecessor,revision:8}});
    await f.model.load();assert.equal(f.model.snapshot.phase,'failed');assert.equal(f.model.snapshot.prepared,null);
  }
});
test('all selected Knowledge heads survive and duplicate or oversized contexts reject',()=>{
  const context=structuredClone(request.payload.context);
  context.knowledge=Array.from({length:8},(_,index)=>{
    const graph={scope:actor.scope,graph_id:'domain-'+index};return {snapshot:{graph,revision:1,sha256:'a'.repeat(64)},change:{graph,change_id:'change',position:1,sha256:'b'.repeat(64)}};
  });
  const prepared=new PreparedCuration(actor,'synthetic',context);
  assert.equal(prepared.request('Review across domains','revise').payload.context.knowledge.length,8);
  assert.throws(()=>new PreparedCuration(actor,'synthetic',{...context,knowledge:[...context.knowledge,context.knowledge[0]!]}));
  assert.throws(()=>new PreparedCuration(actor,'synthetic',{...context,knowledge:[context.knowledge[0]!,context.knowledge[0]!]}));
});
test('legacy original context keeps unavailable Knowledge explicit',async()=>{
  const origin=JSON.parse(readFileSync('tests/fixtures/campaign_origin/record.json','utf8')).origin as CampaignOrigin;
  const f=fixture();const draft=origin.origin.draft;
  const reader=new OriginalCurationContext({selection:()=>draft},{read:async()=>origin});
  const context=await reader.read(f.page.snapshot,new AbortController().signal);
  assert.equal(context.knowledge.length,origin.origin.knowledge?1:0);
  assert.deepEqual(context.questions,origin.origin.research.selection?.questions??[]);
  const missing=new OriginalCurationContext({selection:()=>draft},{read:async()=>null});
  await assert.rejects(()=>missing.read(f.page.snapshot,new AbortController().signal),/origin_unavailable/);
  if(origin.origin.knowledge){origin.origin.knowledge.head=null;await assert.rejects(()=>reader.read(f.page.snapshot,new AbortController().signal),/knowledge_unavailable/);}
});
test('clearing or disposal fences late context and removes prior preparation',async()=>{
  for(const action of ['clear','dispose'] as const){
    const f=fixture();let release:((value:typeof f.context)=>void)|undefined;
    f.source.read=async()=>new Promise(resolve=>{release=resolve;});
    const pending=f.model.load();while(!release)await new Promise(resolve=>setTimeout(resolve,1));
    f.model[action]();release(f.context);await pending;assert.equal(f.model.snapshot.prepared,null);assert.equal(f.model.snapshot.phase,'idle');
  }
});
