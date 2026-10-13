import {test} from 'node:test';
import assert from 'node:assert/strict';
import first from '../../fixtures/generation_comparison/first.json' with {type:'json'};
import {RetainedGeneration} from '../../../src/page_models/generation_comparison/checkpoint.js';
import {RetainedSelection} from '../../../src/page_models/candidate_evidence/selection.js';
import {suppliedStructureEvidence} from '../../../src/page_models/candidate_evidence/structure.js';
import type {ArtifactRef} from '../../../src/contracts/observations.js';
const make=(fixture:unknown=first)=>{const f=fixture as typeof first;return new RetainedSelection(new RetainedGeneration(f.reference as ArtifactRef,f.checkpoint));};

test('explicit retained receipt supplies selection, policy, context and objective direction',()=>{
 const view=make();assert.equal(view.policy,first.checkpoint.selection.policy);
 assert.deepEqual(view.selected,first.checkpoint.selection.selected);
 assert.deepEqual(view.objectives,first.checkpoint.specification.objectives);
 assert.deepEqual(view.evaluator,first.checkpoint.specification.evaluator);
 for(const id of view.selected)assert.equal(view.forCandidate(id).state,'selected');
 assert.equal(view.membershipSha256,first.checkpoint.selection.membership_sha256);
});
test('same recorded front preserves the set and does not create a unique winner',()=>{
 const f=structuredClone(first);for(const rank of f.checkpoint.selection.ranks)rank.front=0;
 const view=make(f),id=view.selected[0]!;
 assert.ok(view.forCandidate(id).sameFront.length>1);
 assert.deepEqual(view.selected,f.checkpoint.selection.selected);
 assert.equal(Object.hasOwn(view,'winner'),false);
});
test('missing selection receipt is distinct from configured policy and pending stage',()=>{
 const missing:any=structuredClone(first);missing.checkpoint.selection=null;
 const id=first.checkpoint.population[0]!;assert.equal(make(missing).forCandidate(id).state,'selection_unavailable');assert.equal(make(missing).configuredPolicy,first.checkpoint.specification.operators.selection);
 const pending=structuredClone(first);pending.checkpoint.phase='ready_to_select';
 const view=make(pending);assert.equal(view.forCandidate(id).state,'selection_pending');assert.deepEqual(view.selected,[]);
});
test('insufficient evidence preserves a partial selection without claiming a winner',()=>{
 const f=structuredClone(first);f.checkpoint.selection.requested=128;f.checkpoint.selection.disposition='insufficient_feasible_candidates';
 const view=make(f);assert.equal(view.forCandidate(view.selected[0]!).state,'insufficient_evidence');
 assert.deepEqual(view.selected,f.checkpoint.selection.selected);
});
test('no feasible observations retain unknown values rather than zero',()=>{
 const f:any=structuredClone(first);f.checkpoint.selection.disposition='no_feasible_candidates';f.checkpoint.selection.selected=[];
 for(const rank of f.checkpoint.selection.ranks)rank.feasible=false;
 for(const row of f.checkpoint.observations)row.outcome={status:'unknown',reason_code:'missing',evidence:[]};
 const evidence=make(f).forCandidate(f.checkpoint.population[0]);assert.equal(evidence.state,'insufficient_evidence');assert.deepEqual(evidence.values,{});assert.equal(evidence.quality,null);assert.equal(evidence.front,null);assert.deepEqual(evidence.sameFront,[]);assert.equal(evidence.constraintViolation,null);
});
test('zero requested is distinct from unavailable fitness',()=>{
 const f=structuredClone(first);f.checkpoint.selection.requested=0;f.checkpoint.selection.selected=[];f.checkpoint.selection.disposition='zero_requested';
 assert.equal(make(f).forCandidate(f.checkpoint.population[0]!).state,'zero_requested');
});
test('different specifications or stages are not comparable',()=>{
 const a=make(),f=structuredClone(first);f.checkpoint.specification.seed='f'.repeat(64);
 assert.equal(a.comparableTo(make(f)),false);const b=structuredClone(first);b.checkpoint.phase='ready_to_select';
 assert.equal(a.comparableTo(make(b)),false);assert.equal(a.comparableTo(make()),true);
});
test('contradictory selected or feasible claims reject rather than fabricate a recommendation',()=>{
 for(const mutate of [(f:any)=>f.checkpoint.selection.requested=0,
  (f:any)=>f.checkpoint.observations[0].outcome.constraint_violation=1,
  (f:any)=>f.checkpoint.selection.disposition='no_feasible_candidates']){
   const f=structuredClone(first);mutate(f);assert.throws(()=>make(f));
 }
 assert.throws(()=>make().forCandidate('missing'));
});
test('caller changes cannot repin the selection snapshot',()=>{
 const retained=new RetainedGeneration(first.reference as ArtifactRef,first.checkpoint),view=new RetainedSelection(retained);
 const before=[...view.selected];retained.record.selection!.selected.length=0;
 assert.deepEqual(view.selected,before);
});
test('supplied molecular structure is unranked, including with numeric selection attached',()=>{
 const ref=structuredClone(first.reference) as ArtifactRef;
 const candidate={scope:ref.scope,candidate_id:first.checkpoint.population[0]!,revision:1};
 const without=suppliedStructureEvidence(candidate,ref);assert.equal(without.status,'unranked');assert.equal(without.reason,'no_molecular_selection_policy');
 const withNumeric=suppliedStructureEvidence(candidate,ref,make());assert.equal(withNumeric.reason,'numeric_selection_inapplicable');assert.equal(withNumeric.properties,'not_available');assert.equal(withNumeric.synthesis,'not_available');
 candidate.revision=2;assert.equal(withNumeric.candidate.revision,1);
 assert.throws(()=>suppliedStructureEvidence({...candidate,scope:{...candidate.scope,project_id:'foreign'}},ref));
});

test('equal recorded objective values preserve multiple selected candidates',()=>{
 const f=structuredClone(first);const value=f.checkpoint.observations[0]!.outcome.objectives[0]!.value;
 for(const o of f.checkpoint.observations)o.outcome.objectives[0]!.value=value;
 for(const rank of f.checkpoint.selection.ranks)rank.front=0;
 const view=make(f);assert.ok(view.selected.length>1);
 assert.equal(view.forCandidate(view.selected[0]!).values.cost,view.forCandidate(view.selected[1]!).values.cost);
 assert.equal(view.forCandidate(view.selected[0]!).sameFront.length,view.selected.length);
});
