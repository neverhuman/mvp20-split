import test from 'node:test';
import assert from 'node:assert/strict';
import {PreparedSuccessor,SuccessorPreparation} from '../../../src/page_models/successor_launch/preparation.js';
import {CurationGraphReview} from '../../../src/page_models/campaign_curation/graph_review.js';
import {RecordedCuration} from '../../../src/page_models/campaign_curation/records.js';
import {graphFixture} from '../campaign_curation/graph_fixture.js';
import type {CarrySources} from '../../../src/contracts/successor_launch.js';
import type {LaunchProfileCatalog} from '../../../src/contracts/launch.js';

export function preparationFixture(){
  const f=graphFixture();
  const review=new CurationGraphReview(f.record,f.original,f.saved,f.validation);
  const sources:CarrySources={scope:f.scope,predecessor:f.curation.specification.context.predecessor,predecessor_ready:true,
    sources:[{source:{kind:'run_output',port:'material'},value_sha256:'9'.repeat(64)}]};
  const node=f.proposed.definition.body.nodes[0]!;if(node.kind!=='invoke')throw Error('fixture');
  const catalog:LaunchProfileCatalog={scope:f.scope,profiles:[{scope:f.scope,reference:{profile_id:'local',version:'1',sha256:'8'.repeat(64)},
    title:'Local reviewed tools',maximum_invocations:8,maximum_deadline_seconds:300,tools:[node.tool]}]};
  return {...f,review,sources,catalog};
}

test('successor preparation retains exact validated proposal and supported managed profile',()=>{
  const f=preparationFixture(),prepared=new PreparedSuccessor(f.review,f.sources,f.catalog);
  const command=prepared.command('launch-next','local',{}).request;
  assert.deepEqual(command.payload.admission.payload.draft,f.curation.validated_draft);
  assert.equal(command.payload.admission.payload.plan_sha256,f.validation.plan_sha256);
  assert.deepEqual(command.payload.admission.payload.predecessor,f.sources.predecessor);
  assert.deepEqual(command.payload.admission.payload.carried,[]);
  assert.equal(command.payload.admission.payload.budget.limit,8);
});

test('explicit input mapping carries original committed hash; no implicit name or type inference',()=>{
  const f=preparationFixture();f.proposed.definition.body.inputs=[{name:'feed',value_type:{kind:'scalar',scalar:'number'}}];
  f.curation.proposal!.outcome={kind:'propose_campaign',candidate:{kind:'future_campaign',...f.proposed,expected_evidence:[]},gaps:[]};
  f.saved.definition=structuredClone(f.proposed.definition);
  const review=new CurationGraphReview(new RecordedCuration(f.curation,f.selection),f.original,f.saved,f.validation);
  const prepared=new PreparedSuccessor(review,f.sources,f.catalog);
  assert.throws(()=>prepared.command('next','local',{}),/inputs_required/);
  assert.throws(()=>prepared.command('next','local',{feed:99}),/inputs_required/);
  const command=prepared.command('next','local',{feed:0});
  assert.deepEqual(command.request.payload.admission.payload.carried,[{target_port:'feed',source:f.sources.sources[0]!.source,expected_value_sha256:'9'.repeat(64)}]);
});

test('changed or unsettled predecessor and unsupported tool profile cannot enable launch',()=>{
  const f=preparationFixture();
  assert.throws(()=>new PreparedSuccessor(f.review,{...f.sources,predecessor_ready:false},f.catalog),/unsettled/);
  assert.throws(()=>new PreparedSuccessor(f.review,{...f.sources,predecessor:{...f.sources.predecessor,revision:99}},f.catalog),/changed/);
  const catalog=structuredClone(f.catalog);catalog.profiles[0]!.tools[0]!.release='2.0.0';
  const prepared=new PreparedSuccessor(f.review,f.sources,catalog);assert.equal(prepared.profiles.length,0);
  assert.throws(()=>prepared.command('next','local',{}));
});

test('hidden preparation cannot publish late source or start profile lookup',async()=>{
  const f=preparationFixture();let finish!:(value:CarrySources)=>void,calls=0;
  const model=new SuccessorPreparation({read:async()=>new Promise(resolve=>{finish=resolve;})},{profiles:async()=>{calls++;return f.catalog;}});
  const pending=model.load(f.review);model.clear();finish(f.sources);await pending;
  assert.equal(calls,0);assert.equal(model.snapshot.prepared,null);assert.equal(model.snapshot.phase,'idle');
});
