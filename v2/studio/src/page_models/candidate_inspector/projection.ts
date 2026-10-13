import {decodeCandidate,finiteStructureProfile,isStructure,type AcceptedToolExecution,type CandidateRevision,type StructureRequest,type StructureResult} from '../../contracts/candidate.js';
import type {ArtifactRef} from '../../contracts/observations.js';
import {requireReply,same} from '../../transport/scientific/identity.js';
import {EvidenceContext,artifactKey} from '../evidence_context.js';
import {suppliedStructureEvidence} from '../candidate_evidence/structure.js';

/** Establish the accepted output and original source before any content is rendered. */
export class CandidateExecution {
 readonly proof:AcceptedToolExecution;
 readonly input:ArtifactRef;
 readonly output:ArtifactRef;
 constructor(context:EvidenceContext,raw:unknown){
  const proof=structuredClone(decodeCandidate('producer',raw)),invocation=proof.invocation;
  const attempt=context.attempt(proof.completion.result.attempt_id);
  const completion=context.completion(attempt.attempt_id,proof.completion),outcome=completion.result.outcome;
  requireReply(completion.canonical_result&&attempt.settled&&attempt.worker_id===proof.worker_id);
  requireReply(invocation.activation_id===completion.activation_id&&invocation.invocation_id===completion.result.invocation_id);
  requireReply(invocation.node_id===context.detail.node.path.node_id);
  requireReply(invocation.tool.capability_id==='chemistry.chemical-structure'&&invocation.tool.release==='0.1.0'&&invocation.tool.contract_version==='1');
  requireReply((invocation.side_effects??'pure')==='pure'&&!invocation.checkpoint&&invocation.inputs.length===1);
  const input=invocation.inputs[0]!;
  requireReply(input.port==='structure'&&isStructure(input.artifact,'request'));
  requireReply(outcome.status==='succeeded'&&!outcome.checkpoint&&outcome.outputs.length===1);
  const output=outcome.outputs[0]!;
  requireReply(output.port==='result'&&isStructure(output.artifact));
  const summary=context.detail.outputs.find(item=>item.port==='result');
  requireReply(!!summary?.artifact&&summary.item_count===1&&summary.missing_count===0);
  context.artifact(output.artifact,summary.artifact);
  context.scopedArtifact(input.artifact);
  this.proof=proof;this.input=input.artifact;this.output=output.artifact;
 }
 contents(inputRaw:unknown,resultRaw:unknown){
  const input=structuredClone(decodeCandidate('request',inputRaw)),result=structuredClone(decodeCandidate('result',resultRaw));
  for(const record of [input,result]){
   requireReply(same(record.scope,this.output.scope)&&same(record.candidate.scope,record.scope)&&same(record.semantic_profile,finiteStructureProfile));
  }
  requireReply(same(input.candidate,result.candidate)&&result.source_sha256===this.input.sha256);
  return new CandidateContents(this,input,result);
 }
}

export class CandidateContents {
 constructor(readonly execution:CandidateExecution,readonly input:StructureRequest,readonly result:StructureResult){
  const outcome=result.outcome;
  if(outcome.status!=='derived')return;
  const atoms=outcome.graph.atoms,bonds=outcome.graph.bonds;
  requireReply(atoms.every((atom,i)=>atom.index===i));
  requireReply(atoms.reduce((sum,atom)=>sum+atom.formal_charge,0)===outcome.formula.net_formal_charge);
  const edges=new Set<string>(),neighbors=atoms.map(()=>[] as number[]);
  for(const bond of bonds){
   requireReply(bond.begin<atoms.length&&bond.end<atoms.length&&bond.begin!==bond.end&&bond.stereo_atoms.every(i=>i<atoms.length));
   const key=[bond.begin,bond.end].sort((a,b)=>a-b).join(':');requireReply(!edges.has(key));edges.add(key);
   neighbors[bond.begin]!.push(bond.end);neighbors[bond.end]!.push(bond.begin);
  }
  const visited=new Set<number>(),pending=[0];
  while(pending.length){const i=pending.pop()!;if(visited.has(i))continue;visited.add(i);pending.push(...neighbors[i]!);}
  requireReply(visited.size===atoms.length);
 }
 registration(raw:unknown){
  const candidate=structuredClone(decodeCandidate('candidate',raw));
  requireReply(same(candidate.reference,this.result.candidate)&&artifactKey(candidate.representation)===artifactKey(this.execution.output));
  if(candidate.supersedes)requireReply(same(candidate.supersedes.scope,candidate.reference.scope)&&candidate.supersedes.candidate_id===candidate.reference.candidate_id&&candidate.supersedes.revision+1===candidate.reference.revision);
  return {candidate,recommendation:suppliedStructureEvidence(candidate.reference,candidate.representation)};
 }
}
