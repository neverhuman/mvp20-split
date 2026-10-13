import {test} from 'node:test';
import assert from 'node:assert/strict';
import {CandidateDiscoveryModel,discoverStructures} from '../../../src/page_models/candidate_inspector/discovery.js';
import {fixture} from './fixture.js';
import {deferred} from '../../fixtures/observations.js';
import type {GraphSnapshotPage} from '../../../src/contracts/observations.js';
function peers(){const f=fixture(),page:GraphSnapshotPage={schema_version:'1',snapshot:{...f.anchor,node_count:1},nodes:[f.detail.node],next_cursor:null};return {...f,page,runtime:{snapshot:async()=>structuredClone(page),detail:async()=>structuredClone(f.detail)},context:{scope:f.anchor.cut.scope,run:f.anchor.cut.run_id}};}
test('discovery retains exact read cut and producing activation without a candidate rank',async()=>{
 const f=peers(),result=await discoverStructures(f.context,f.runtime,new AbortController().signal);
 assert.equal(result.choices.length,1);assert.equal(result.choices[0]?.key,f.detail.node.activation_id);assert.deepEqual(result.anchor,f.page.snapshot);assert.equal(result.incomplete,false);
});
test('scalar outputs are not converted into molecules and collections remain a partial scan',async()=>{
 const f=peers();f.detail.outputs[0]!.artifact!.schema_ref.schema_id='materials.hansen-solvency.output';
 f.detail.outputs.push({port:'population',kind:'collection',item_count:20,missing_count:0,artifact:null});
 const result=await discoverStructures(f.context,f.runtime,new AbortController().signal);assert.equal(result.choices.length,0);assert.equal(result.incomplete,true);
});
test('mismatched detail cut or graph node is rejected',async()=>{
 for(const mutate of [(f:ReturnType<typeof peers>)=>{f.detail.cut.revision++;},(f:ReturnType<typeof peers>)=>{f.runtime.detail=async()=>({...f.detail,node:{...f.detail.node,activation_id:'b'.repeat(64)}});}]){
  const f=peers();f.page=structuredClone(f.page);const page=structuredClone(f.page);f.runtime.snapshot=async()=>page;mutate(f);
  await assert.rejects(()=>discoverStructures(f.context,f.runtime,new AbortController().signal));
 }
});
test('hidden results discard late discovery and denied refresh clears prior choices',async()=>{
 const f=peers(),held=deferred<GraphSnapshotPage>();f.runtime.snapshot=()=>held.promise;
 const m=new CandidateDiscoveryModel(f.context,f.runtime),pending=m.refresh();m.clear();held.resolve(f.page);await pending;assert.ok(m.snapshot.discovery===null);
 f.runtime.snapshot=async()=>f.page;await m.refresh();assert.equal((m.snapshot.discovery as import('../../../src/page_models/candidate_inspector/discovery.js').StructureDiscovery|null)?.choices.length,1);
 f.runtime.snapshot=async()=>{throw {kind:'denied'};};await m.refresh();assert.equal(m.snapshot.phase,'denied');assert.equal(m.snapshot.discovery,null);
});
