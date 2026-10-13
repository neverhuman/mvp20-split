import type {ObservationSource} from '../../transport/observations.js';
import type {GraphNodeDetail,GraphSnapshotPage} from '../../contracts/observations.js';
import {isStructure} from '../../contracts/candidate.js';
import {GraphWindow,cutKey,type RunContext} from '../graph_window.js';
import {EvidenceContext} from '../evidence_context.js';
import {equalValue} from '../generation_comparison/checkpoint.js';
import {ReadFailure} from '../../transport/failure.js';
import {RequestLane} from '../request_lane.js';
export type StructureChoice=Readonly<{key:string;label:string;detail:GraphNodeDetail}>;
export type StructureDiscovery=Readonly<{anchor:GraphSnapshotPage['snapshot'];choices:readonly StructureChoice[];scanned:number;total:number;incomplete:boolean}>;

/** Bounded direct-output discovery, not a candidate/population index. */
export async function discoverStructures(run:RunContext,runtime:Pick<ObservationSource,'snapshot'|'detail'>,signal:AbortSignal):Promise<StructureDiscovery>{
 let window=GraphWindow.open(run,{},await runtime.snapshot(run.run,{},undefined,signal));
 if(window.next)window=window.append(await runtime.snapshot(run.run,{},window.next,signal));
 const nodes=window.nodes.slice(0,100),choices:StructureChoice[]=[];
 let incomplete=!!window.next||window.nodes.length>100;
 for(let offset=0;offset<nodes.length;offset+=4){
  if(signal.aborted)throw new ReadFailure('aborted');
  const batch=nodes.slice(offset,offset+4),details=await Promise.all(batch.map(node=>runtime.detail(run.run,node.activation_id,window.snapshot.snapshot_token,undefined,signal)));
  for(let i=0;i<details.length;i++){
   const detail=details[i]!,node=batch[i]!;
   if(cutKey(detail.cut)!==cutKey(window.snapshot.cut))throw new ReadFailure('resnapshot');
   if(!equalValue(detail.node,node))throw new ReadFailure('invalid_response');
   const context=new EvidenceContext(window.snapshot,detail);
   if(detail.outputs.some(o=>o.kind==='collection'&&o.item_count>0))incomplete=true;
   if(!detail.outputs.some(o=>o.artifact&&isStructure(o.artifact)))continue;
   for(const output of detail.outputs)if(output.artifact)context.scopedArtifact(output.artifact);
   choices.push({key:node.activation_id,label:node.path.node_id+(node.path.occurrences??[]).map(o=>` / ${o.node_id} ${o.index}`).join(''),detail:structuredClone(detail)});
  }
 }
 if(signal.aborted)throw new ReadFailure('aborted');
 return {anchor:structuredClone(window.snapshot),choices,scanned:nodes.length,total:window.snapshot.node_count,incomplete};
}
type View=Readonly<{phase:'idle'|'loading'|'ready'|'failed'|'denied';discovery:StructureDiscovery|null;message:string|null}>;
export class CandidateDiscoveryModel {
 private lane=new RequestLane();private listeners=new Set<()=>void>();private disposed=false;
 private view:View={phase:'idle',discovery:null,message:null};
 constructor(private run:RunContext,private runtime:Pick<ObservationSource,'snapshot'|'detail'>){}
 get snapshot(){return this.view;}
 subscribe(listener:()=>void){this.listeners.add(listener);return()=>{this.listeners.delete(listener);};}
 private patch(view:View){if(this.disposed)return;this.view=Object.freeze(view);for(const listener of this.listeners)listener();}
 async refresh(){
  if(this.disposed)return;const ticket=this.lane.begin();this.patch({phase:'loading',discovery:null,message:null});
  try{const discovery=await discoverStructures(this.run,this.runtime,ticket.signal);if(ticket.current())this.patch({phase:'ready',discovery,message:null});}
  catch(error){if(ticket.current())this.patch({phase:(error as {kind?:string})?.kind==='denied'?'denied':'failed',discovery:null,message:'Candidate outputs could not be read at one execution snapshot. Refresh to try again.'});}
 }
 clear(){this.lane.cancel();this.patch({phase:'idle',discovery:null,message:null});}
 dispose(){this.clear();this.disposed=true;this.listeners.clear();}
}
