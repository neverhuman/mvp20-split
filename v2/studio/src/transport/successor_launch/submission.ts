import {decodeSuccessor,type SuccessorLaunchRequest,type SuccessorLaunchReceipt,type AdmitDraftSuccessor} from '../../contracts/successor_launch.js';
import type {CommandIdentity} from '../../contracts/authoring.js';
import {checkJSON,numericJSON} from '../command_wire.js';
import {same as sameValue} from '../scientific/identity.js';

const identityKey=(value:CommandIdentity)=>JSON.stringify([value.scope.tenant_id,value.scope.project_id,value.actor_id,value.command_family,value.command_id]);
const fixed=<T>(value:T):T=>{if(value&&typeof value==='object'){Object.values(value).forEach(fixed);Object.freeze(value);}return value;};

/** Original numerical wire bytes. Deployment/Runtime, not JavaScript, own canonical hashes. */
export class SuccessorSubmission{
  private constructor(readonly body:string){
    if(new TextEncoder().encode(body).byteLength>262144)throw Error('successor_request_too_large');
    const request=decodeSuccessor('request',JSON.parse(body)),inner=request.payload.admission;
    checkJSON(request,true);
    if(numericJSON(request)!==body)throw Error('successor_original_bytes_invalid');
    if(request.identity.command_family!=='campaign.launch_successor'||inner.identity.command_family!=='graph.admit_draft_successor'||
      identityKey(request.identity)!==identityKey({...inner.identity,command_family:'campaign.launch_successor'}))throw Error('successor_identity_mismatch');
    const payload=inner.payload,scope=request.identity.scope;
    const targets=payload.carried.map(item=>item.target_port);
    if(new Set(targets).size!==targets.length)throw Error('successor_duplicate_carry');
    for(const binding of payload.inputs){
      const items=binding.value.kind==='collection'?binding.value.items:[binding.value];
      if(items.some(item=>item.kind==='artifact'&&!sameValue(item.artifact.scope,scope)))throw Error('successor_artifact_scope');
    }
    Object.freeze(this);
  }
  static create(identity:CommandIdentity,payload:AdmitDraftSuccessor,profile:SuccessorLaunchRequest['payload']['profile']){
    if(identity.command_family!=='campaign.launch_successor')throw Error('successor_identity_mismatch');
    const request={encoding:'amphora-command-v2',identity,payload:{profile,admission:{encoding:'amphora-command-v2',
      identity:{...identity,command_family:'graph.admit_draft_successor'},payload}}};
    checkJSON(request,true);return new SuccessorSubmission(numericJSON(request));
  }
  static restore(body:string){return new SuccessorSubmission(body);}
  get request():SuccessorLaunchRequest{return JSON.parse(this.body);}
  query(previous:SuccessorLaunchReceipt){
    this.verify(previous);return decodeSuccessor('query',{identity:this.request.identity,request_sha256:previous.request_sha256});
  }
  verify(raw:unknown,previous?:SuccessorLaunchReceipt){
    const receipt=decodeSuccessor('receipt',raw),request=this.request,inner=request.payload.admission;
    if(identityKey(receipt.identity)!==identityKey(request.identity)||!sameValue(receipt.profile,request.payload.profile)||
      !sameValue(receipt.predecessor,inner.payload.predecessor)||receipt.workers.ready>receipt.workers.expected)throw Error('successor_receipt_mismatch');
    const outcome=receipt.admission?.outcome;
    if(outcome&&identityKey(outcome.binding.identity)!==identityKey(inner.identity))throw Error('successor_admission_mismatch');
    if(receipt.run_id!==null&&(!outcome||outcome.status!=='accepted'||outcome.committed.kind!=='run'||
      outcome.committed.revision!==0||outcome.committed.object_id!==receipt.run_id||receipt.run_id===receipt.predecessor.run_id))throw Error('successor_run_mismatch');
    if(outcome?.status==='accepted'&&receipt.run_id!==outcome.committed.object_id)throw Error('successor_run_missing');
    if(['admitted_not_engaged','engaging','engaged','draining','released'].includes(receipt.phase)&&!receipt.run_id)throw Error('successor_admission_missing');
    if(previous){
      if(receipt.revision<previous.revision||receipt.request_sha256!==previous.request_sha256||receipt.created_at!==previous.created_at||
        previous.run_id!==null&&receipt.run_id!==previous.run_id||receipt.revision===previous.revision&&!sameValue(receipt,previous))throw Error('successor_binding_changed');
      const prior=previous.admission?.outcome;
      if(prior&&(!outcome||!sameValue(prior.binding,outcome.binding)||prior.status!=='pending'&&!sameValue(prior,outcome)))throw Error('successor_admission_changed');
      if(['released','rejected'].includes(previous.phase)&&receipt.phase!==previous.phase)throw Error('successor_terminal_changed');
    }
    return fixed(structuredClone(receipt));
  }
}
