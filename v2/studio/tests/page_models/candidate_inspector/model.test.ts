import {test} from 'node:test';
import assert from 'node:assert/strict';
import {CandidateInspectorModel} from '../../../src/page_models/candidate_inspector/model.js';
import {CandidateExecution} from '../../../src/page_models/candidate_inspector/projection.js';
import {EvidenceContext} from '../../../src/page_models/evidence_context.js';
import {ScientificReadFailure} from '../../../src/transport/scientific/failure.js';
import {deferred} from '../../fixtures/observations.js';
import {fixture} from './fixture.js';

test('accepted supplied structure remains unranked with formula and verified PNG',async()=>{
 const f=fixture(),model=new CandidateInspectorModel(f.source);await model.read(f.anchor,f.detail);
 assert.equal(model.snapshot.phase,'ready');const value=model.snapshot.inspection!;
 assert.equal(value.result.outcome.status,'derived');
 if(value.result.outcome.status==='derived')assert.equal(value.result.outcome.formula.text,'C4H10O3');
 assert.ok(value.depiction?.startsWith('data:image/png;base64,'));
 assert.equal(value.recommendation?.status,'unranked');assert.equal(value.recommendation?.synthesis,'not_available');
});

test('producer must match selected execution, worker, release, original input and sole retained output',()=>{
 const mutations:Array<(f:ReturnType<typeof fixture>)=>void>=[
  f=>{f.proof.worker_id='other';},f=>{f.proof.invocation.activation_id='b'.repeat(64);},
  f=>{f.proof.invocation.node_id='other';},f=>{f.proof.invocation.tool.release='0.2.0';},
  f=>{f.proof.completion.canonical_result=false;},f=>{f.proof.completion.accepted_run_revision=99;},
  f=>{f.proof.invocation.inputs[0]!.port='wrong';},f=>{f.proof.invocation.inputs.push(f.proof.invocation.inputs[0]!);},
  f=>{f.proof.invocation.inputs[0]!.artifact.schema_ref.sha256='0'.repeat(64);},
  f=>{f.detail.outputs[0]!.artifact={...f.output,sha256:'b'.repeat(64)};},
 ];
 for(const mutate of mutations){const f=fixture();mutate(f);assert.throws(()=>new CandidateExecution(new EvidenceContext(f.anchor,f.detail),f.proof));}
});

test('cross-candidate, source hash, semantic profile, graph and registration mismatches cannot render',async()=>{
 const mutations:Array<(f:ReturnType<typeof fixture>)=>void>=[
  f=>{f.result.candidate.revision=2;},f=>{f.result.source_sha256='0'.repeat(64);},
  f=>{f.result.scope={...f.result.scope,project_id:'other'};},f=>{f.request.semantic_profile.sha256='0'.repeat(64);},
  f=>{f.candidate.reference={...f.candidate.reference,candidate_id:'other'};},
  f=>{f.candidate.representation={...f.output,artifact_id:'other'};},
  f=>{if(f.result.outcome.status==='derived')f.result.outcome.graph.atoms[0]!.index=1;},
  f=>{if(f.result.outcome.status==='derived')f.result.outcome.graph.bonds=[];},
  f=>{if(f.result.outcome.status==='derived')f.result.outcome.formula.net_formal_charge=1;},
 ];
 for(const mutate of mutations){const f=fixture();mutate(f);const m=new CandidateInspectorModel(f.source);await m.read(f.anchor,f.detail);assert.equal(m.snapshot.phase,'failed');assert.equal(m.snapshot.inspection,null);}
});

test('owner denial clears previously visible formula and depiction',async()=>{
 const f=fixture(),m=new CandidateInspectorModel(f.source);await m.read(f.anchor,f.detail);assert.equal(m.snapshot.phase,'ready');
 f.source.jsonArtifact=async()=>{throw new ScientificReadFailure('denied');};
 await m.read(f.anchor,f.detail);assert.equal(m.snapshot.phase,'denied');assert.equal(m.snapshot.inspection,null);
});

test('hide, rebind and disposal fence an uncancellable owner response',async()=>{
 for(const action of ['hide','dispose','rebind']){
  const f=fixture(),held=deferred<typeof f.proof>();f.source.producer=()=>held.promise;
  const m=new CandidateInspectorModel(f.source),pending=m.read(f.anchor,f.detail);
  if(action==='dispose')m.dispose();else if(action==='hide')await m.read(null,null);else{f.source.producer=async()=>{throw new ScientificReadFailure('denied');};await m.read(f.anchor,f.detail);}
  held.resolve(f.proof);await pending;assert.equal(m.snapshot.inspection,null);assert.notEqual(m.snapshot.phase,'ready');
 }
});

test('unsupported structure failure is retained evidence, never a guessed formula',async()=>{
 const f=fixture();f.result.outcome={status:'unsupported',code:'unsupported_representation'};
 f.source.candidate=async()=>{throw Error('must not read registration for failure');};
 const m=new CandidateInspectorModel(f.source);await m.read(f.anchor,f.detail);
 assert.equal(m.snapshot.phase,'ready');assert.equal(m.snapshot.inspection?.depiction,null);assert.equal(m.snapshot.inspection?.candidate,null);
});
