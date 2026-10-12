import type {ObservationSource} from '../../transport/observations.js';
import type {ArtifactRef} from '../../contracts/observations.js';
import {isCheckpoint} from '../../contracts/search.js';
import {GraphWindow,cutKey,type RunContext} from '../graph_window.js';
import {EvidenceContext,artifactKey} from '../evidence_context.js';
import {ReadFailure} from '../../transport/failure.js';
import {equalValue} from './checkpoint.js';

export type CheckpointChoice=Readonly<{key:string;reference:ArtifactRef;locations:readonly string[]}>;
export type Discovery=Readonly<{choices:readonly CheckpointChoice[];scanned:number;total:number;incomplete:boolean}>;
/** Bounded direct-output traversal at one Runtime read cut. Never a full result index. */
export async function discover(run:RunContext,runtime:Pick<ObservationSource,'snapshot'|'detail'>,signal:AbortSignal):Promise<Discovery>{
 let window=GraphWindow.open(run,{},await runtime.snapshot(run.run,{},undefined,signal));
 for(let pages=1;window.next&&pages<2;pages++)window=window.append(await runtime.snapshot(run.run,{},window.next,signal));
 const nodes=window.nodes.slice(0,100),found=new Map<string,CheckpointChoice>();
 let incomplete=Boolean(window.next)||window.nodes.length>100;
 for(let offset=0;offset<nodes.length;offset+=4){
  if(signal.aborted)throw new ReadFailure('aborted');
  const batch=nodes.slice(offset,offset+4);
  const details=await Promise.all(batch.map(node=>runtime.detail(run.run,node.activation_id,window.snapshot.snapshot_token,undefined,signal)));
  for(let i=0;i<details.length;i++){
   const d=details[i]!,node=batch[i]!;
   if(cutKey(d.cut)!==cutKey(window.snapshot.cut))throw new ReadFailure('resnapshot');
   if(!equalValue(d.node,node))throw new ReadFailure('invalid_response');
   const context=new EvidenceContext(window.snapshot,d);
   for(const output of d.outputs){
    if(output.kind==='collection'&&output.item_count>0)incomplete=true;
    const ref=output.artifact;if(!ref||!isCheckpoint(ref))continue;
    context.scopedArtifact(ref);
    const key=artifactKey(ref),previous=found.get(key);
    if(!previous&&found.size>=128){incomplete=true;continue;}
    const location=node.path.node_id+(node.path.occurrences??[]).map(o=>' / '+o.node_id+' '+o.index).join('')+' / '+output.port;
    found.set(key,{key,reference:structuredClone(ref),locations:Object.freeze([...(previous?.locations??[]),location])});
   }
  }
 }
 if(signal.aborted)throw new ReadFailure('aborted');
 return Object.freeze({choices:Object.freeze([...found.values()]),scanned:nodes.length,total:window.snapshot.node_count,incomplete});
}
