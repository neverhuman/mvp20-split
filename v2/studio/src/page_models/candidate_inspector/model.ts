import type {AcceptedToolExecution,CandidateReference,CandidateRevision,StructureResult} from '../../contracts/candidate.js';
import {isStructure} from '../../contracts/candidate.js';
import type {ArtifactRef,GraphNodeDetail,GraphSnapshotPage} from '../../contracts/observations.js';
import type {StructureRecommendation} from '../candidate_evidence/structure.js';
import {EvidenceContext} from '../evidence_context.js';
import {RequestLane} from '../request_lane.js';
import {CandidateExecution} from './projection.js';
import {verifiedPNG} from './png.js';

export interface CandidateSource {
 producer(run:string,completion:string,signal:AbortSignal):Promise<AcceptedToolExecution>;
 candidate(reference:CandidateReference,signal:AbortSignal):Promise<CandidateRevision>;
 jsonArtifact(reference:ArtifactRef,signal:AbortSignal):Promise<unknown>;
}
export type CandidateInspection=Readonly<{result:StructureResult;candidate:CandidateRevision|null;recommendation:StructureRecommendation|null;
 depiction:string|null;execution:AcceptedToolExecution;source:ArtifactRef;representation:ArtifactRef}>;
type View=Readonly<{phase:'idle'|'loading'|'ready'|'failed'|'denied';inspection:CandidateInspection|null;error:string|null}>;

/** One selected activation at a pinned read cut. Never reuses content after hide/rebind. */
export class CandidateInspectorModel {
 private lane=new RequestLane();private listeners=new Set<()=>void>();private disposed=false;
 private view:View={phase:'idle',inspection:null,error:null};
 constructor(private readonly source:CandidateSource){}
 get snapshot(){return this.view;}
 subscribe(listener:()=>void){this.listeners.add(listener);return()=>{this.listeners.delete(listener);};}
 private patch(view:View){if(this.disposed)return;this.view=Object.freeze(view);for(const listener of this.listeners)listener();}
 async read(anchor:GraphSnapshotPage['snapshot']|null,detail:GraphNodeDetail|null){
  this.lane.cancel();if(this.disposed)return;
  if(!anchor||!detail||!detail.outputs.some(output=>output.artifact&&isStructure(output.artifact))){this.patch({phase:'idle',inspection:null,error:null});return;}
  const ticket=this.lane.begin();this.patch({phase:'loading',inspection:null,error:null});
  try{
   const context=new EvidenceContext(anchor,detail),attempts=context.detail.attempts.filter(a=>a.canonical_result&&a.settled&&a.completion_id);
   if(attempts.length!==1)throw Error('canonical_attempt_not_in_page');
   const proof=await this.source.producer(context.anchor.cut.run_id,attempts[0]!.completion_id!,ticket.signal);
   if(!ticket.current())return;
   const execution=new CandidateExecution(context,proof);
   const [input,output]=await Promise.all([this.source.jsonArtifact(execution.input,ticket.signal),this.source.jsonArtifact(execution.output,ticket.signal)]);
   if(!ticket.current())return;
   const contents=execution.contents(input,output),result=contents.result;
   let candidate:CandidateRevision|null=null,recommendation:StructureRecommendation|null=null,depiction:string|null=null;
   if(result.outcome.status==='derived'){
    const record=await this.source.candidate(result.candidate,ticket.signal);
    if(!ticket.current())return;
    ({candidate,recommendation}=contents.registration(record));
    depiction=await verifiedPNG(result.outcome.depiction,ticket.signal);
   }
   if(ticket.current())this.patch({phase:'ready',inspection:{result,candidate,recommendation,depiction,execution:proof,source:execution.input,representation:execution.output},error:null});
  }catch(error){if(ticket.current())this.patch({phase:(error as {kind?:string})?.kind==='denied'?'denied':'failed',inspection:null,
   error:'Candidate evidence could not be verified. No structure is displayed. Refresh the execution snapshot or inspect the accepted attempt.'});}
 }
 dispose(){this.lane.cancel();this.disposed=true;this.listeners.clear();this.view={phase:'idle',inspection:null,error:null};}
}
