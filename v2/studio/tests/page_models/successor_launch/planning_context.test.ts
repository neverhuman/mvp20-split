import test from 'node:test';
import assert from 'node:assert/strict';
import {SuccessorPlanningContext} from '../../../src/page_models/successor_launch/planning_context.js';
import {CurationGraphReview} from '../../../src/page_models/campaign_curation/graph_review.js';
import {RecordedCuration} from '../../../src/page_models/campaign_curation/records.js';
import {SuccessorSubmission} from '../../../src/transport/successor_launch/submission.js';
import {graphFixture} from '../campaign_curation/graph_fixture.js';
import {successorReceipt} from '../../fixtures/successor_launch.js';
import {snapshot} from '../../fixtures/observations.js';

function setup(){
  const f=graphFixture();f.curation.specification.context.knowledge=Array.from({length:8},(_,index)=>{
    const graph={scope:f.scope,graph_id:'domain-'+index};return {snapshot:{graph,revision:1,sha256:'a'.repeat(64)},change:{graph,change_id:'change',position:1,sha256:'b'.repeat(64)}};
  });
  const review=new CurationGraphReview(new RecordedCuration(f.curation,f.selection),f.original,f.saved,f.validation);
  const command=SuccessorSubmission.create({...f.curation.receipt.identity,command_family:'campaign.launch_successor',command_id:'next'},
    {plan_sha256:f.validation.plan_sha256!,draft:f.curation.validated_draft!,predecessor:f.curation.specification.context.predecessor,inputs:[],carried:[],budget:{limit:4}},
    {profile_id:'local',version:'1',sha256:'8'.repeat(64)});
  const receipt=successorReceipt(command);receipt.revision=1;receipt.phase='engaged';receipt.run_id='child';
  receipt.admission={outcome:{status:'accepted',binding:{identity:command.request.payload.admission.identity,operation_id:'op',request_sha256:'3'.repeat(64)},committed:{kind:'run',object_id:'child',revision:0}}};
  const observed=snapshot().snapshot;observed.cut={...observed.cut,scope:f.scope,run_id:'child',plan_sha256:f.validation.plan_sha256!,revision:12};
  const model=new SuccessorPlanningContext(review,command,receipt,{draft:async()=>f.saved},{curation:async()=>f.curation});
  return {...f,review,command,receipt,observed,model};
}
test('successor iteration preserves all original Knowledge selections with the new run and draft',async()=>{
  const f=setup(),context=await f.model.curationContext(f.observed,new AbortController().signal);
  assert.deepEqual(context.knowledge,f.curation.specification.context.knowledge);assert.equal(context.knowledge.length,8);
  assert.equal(context.predecessor.run_id,'child');assert.equal(context.predecessor.revision,12);assert.equal(context.draft.draft_id,f.saved.head.draft_id);
  assert.equal(await f.model.reference(f.observed,new AbortController().signal),null);
});
test('wrong run, modified saved definition or changed original curation cannot supply successor context',async()=>{
  for(const variant of ['run','draft','curation']){
    const f=setup();if(variant==='run')f.observed.cut.run_id='wrong';
    if(variant==='draft')f.saved.definition.body.nodes[0]!.node_id='replacement';
    if(variant==='curation')f.curation.specification.context.knowledge.pop();
    await assert.rejects(f.model.curationContext(f.observed,new AbortController().signal));
  }
});
