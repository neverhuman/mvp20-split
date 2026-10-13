import retained from './retained.json' with {type:'json'};
import {decodeCandidate,structureProfiles,type AcceptedToolExecution,type CandidateRevision} from '../../../src/contracts/candidate.js';
import type {ArtifactRef} from '../../../src/contracts/observations.js';
import {completion,evidenceDetail} from '../../fixtures/evidence.js';
import {snapshot} from '../../fixtures/observations.js';
import type {CandidateSource} from '../../../src/page_models/candidate_inspector/model.js';

/** Actual P1 toolkit output; synthetic transport/cut wrappers for isolated failure oracles. */
export function fixture(){
 const result=decodeCandidate('result',structuredClone(retained.result)),request=decodeCandidate('request',structuredClone(retained.request));
 const scope=result.scope,anchor=snapshot().snapshot,detail=evidenceDetail(),record=completion();
 anchor.cut.scope=scope;detail.cut.scope=scope;record.scope=scope;
 const output:ArtifactRef={artifact_id:'chemical-output',scope,sha256:'a'.repeat(64),media_type:'application/json',size_bytes:16911,schema_ref:{...structureProfiles.result,version:'1'}};
 const input:ArtifactRef={...output,artifact_id:'chemical-input',sha256:result.source_sha256,size_bytes:650,schema_ref:{...structureProfiles.request,version:'1'}};
 detail.outputs[0]!.artifact=output;
 if(record.result.outcome.status!=='succeeded')throw Error('fixture');
 record.result.outcome.outputs=[{port:'result',artifact:output}];
 const proof:AcceptedToolExecution={wire_version:'1',authority:'accepted_execution',worker_id:'worker-1',completion:record,
  invocation:{node_id:detail.node.path.node_id,activation_id:record.activation_id,invocation_id:record.result.invocation_id,tool:{capability_id:'chemistry.chemical-structure',release:'0.1.0',contract_version:'1',image_sha256:'c'.repeat(64)},inputs:[{port:'structure',artifact:input}],checkpoint:null,timeout_seconds:60,side_effects:'pure'}};
 const candidate:CandidateRevision={wire_version:'1',reference:result.candidate,representation:output,supersedes:null};
 const source:CandidateSource={producer:async()=>structuredClone(proof),candidate:async()=>structuredClone(candidate),jsonArtifact:async ref=>structuredClone(ref.artifact_id===input.artifact_id?request:result)};
 return {anchor,detail,proof,candidate,result,request,input,output,source};
}
