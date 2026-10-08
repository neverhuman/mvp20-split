import type {ObservationClient} from '../../transport/observations.js';
import type {DataProvenanceClient} from '../../transport/provenance/data.js';
import type {GraphNodeDetail,ArtifactRef,GraphSnapshotPage} from '../../contracts/observations.js';
import {GraphWindow,cutKey,type RunContext} from '../graph_window.js';
import {RequestLane} from '../request_lane.js';
import {scientificResult,supported,type ScientificResult} from '../scientific_output/model.js';
import {readCampaignContext,isCampaignContext,type CampaignContext,type MethodBinding} from './context.js';
import type {SceneNode,SceneEdge} from '../scene.js';
export type BoundResult=Readonly<{binding:MethodBinding;detail:GraphNodeDetail;artifact:ArtifactRef|null;result:ScientificResult|null;problem:string|null}>;
type View=Readonly<{phase:'idle'|'loading'|'ready'|'absent'|'limited'|'failed'|'denied';context:CampaignContext|null;results:readonly BoundResult[];snapshot:GraphSnapshotPage['snapshot']|null;message:string|null;scene?:{nodes:readonly SceneNode[];edges:readonly SceneEdge[]}}>; 
/** Bounded existing-owner read composition; never a result index or scientific authority. */
export class CampaignFlowModel {
 private lane=new RequestLane();private listeners=new Set<()=>void>();private disposed=false;
 private view:View={phase:'idle',context:null,results:[],snapshot:null,message:null};
 constructor(private readonly run:RunContext,private readonly runtime:Pick<ObservationClient,'snapshot'|'detail'|'topology'>,private readonly data:Pick<DataProvenanceClient,'jsonArtifact'>){}
 get snapshot(){return this.view;}
 subscribe(listener:()=>void){this.listeners.add(listener);return()=>{this.listeners.delete(listener);};}
 private patch(view:View){if(this.disposed)return;this.view=Object.freeze(view);for(const listener of this.listeners)listener();}
 async refresh(){if(this.disposed)return;const ticket=this.lane.begin();this.patch({phase:'loading',context:null,results:[],snapshot:null,message:null});
  try {
   const page=await this.runtime.snapshot(this.run.run,{},undefined,ticket.signal),window=GraphWindow.open(this.run,{},page);
   if(!ticket.current())return;
   if(window.next||window.nodes.length>32){this.patch({phase:'limited',context:null,results:[],snapshot:page.snapshot,message:'This demo view scans at most 32 steps. Use execution inspection for this larger campaign.'});return;}
   const details:GraphNodeDetail[]=[];
   for(const node of window.nodes){const detail=await this.runtime.detail(this.run.run,node.activation_id,window.snapshot.snapshot_token,undefined,ticket.signal);
    if(cutKey(detail.cut)!==cutKey(window.snapshot.cut)||detail.node.activation_id!==node.activation_id)throw Error('Observation changed');details.push(detail);}
   const refs=details.filter(d=>d.node.kind==='finish').flatMap(d=>d.outputs.flatMap(o=>o.artifact&&isCampaignContext(o.artifact)?[o.artifact]:[]));
   if(!ticket.current())return;
   if(!refs.length){this.patch({phase:'absent',context:null,results:[],snapshot:page.snapshot,message:'No retained planning context is available for this campaign.'});return;}
   if(refs.length!==1)throw Error('Ambiguous context');
   const context=readCampaignContext(await this.data.jsonArtifact(refs[0]!,ticket.signal),refs[0]!,this.run),results:BoundResult[]=[];
   for(const binding of context.bindings){
    const matches=details.filter(d=>d.node.path.node_id===binding.node_id&&!d.node.path.occurrences?.length);
    if(matches.length!==1||matches[0]!.node.kind!=='invoke')throw Error('Bound execution missing');const detail=matches[0]!;
    const artifacts=detail.outputs.flatMap(o=>o.artifact&&supported(o.artifact)?[o.artifact]:[]);let artifact:ArtifactRef|null=null,result:ScientificResult|null=null,problem:string|null=null;
    if(artifacts.length===1){artifact=artifacts[0]!;if(artifact.scope.tenant_id!==this.run.scope.tenant_id||artifact.scope.project_id!==this.run.scope.project_id)throw Error('Output scope mismatch');
     try{result=scientificResult(artifact,await this.data.jsonArtifact(artifact,ticket.signal));if(result.candidate!==binding.candidate_id||result.method!==binding.tool.capability_id+'.output')throw Error('Wrong candidate or declared method');}
     catch(error){if((error as {kind?:string}).kind==='denied')throw error;result=null;problem='Result could not be verified.';}
    }else problem=artifacts.length?'Multiple recognized outputs; select an exact artifact.':'No supported retained scientific result.';
    results.push(Object.freeze({binding,detail,artifact,result,problem}));
   }
   const topology=await this.runtime.topology(this.run.run,details[0]!.scope_key,window.snapshot.snapshot_token,{},undefined,ticket.signal);
   if(cutKey(topology.cut)!==cutKey(window.snapshot.cut)||topology.next_cursor||topology.nodes.length!==details.length)throw Error('Incomplete root topology');
   const nodes:SceneNode[]=context.design.nodes.map(n=>({id:'plan:'+n.id,label:n.title,status:n.id==='synthesis'?'evidence missing':'planning context',x:0,y:0}));
   nodes.push(...details.map(d=>({id:d.node.activation_id,label:d.node.path.node_id.replaceAll('_',' '),status:d.node.status,x:0,y:0})));
   const edges:SceneEdge[]=context.design.edges.map((e,i)=>({id:'planning:'+i,source:'plan:'+e.source,target:'plan:'+e.target,label:'planning-context'}));
   edges.push(...results.map(r=>({id:'binding:'+r.binding.node_id,source:'plan:'+r.binding.method_id,target:r.detail.node.activation_id,label:'planning-context'})));
   edges.push(...topology.edges.map((e,i)=>({id:'execution:'+i,source:e.source,target:e.target,label:e.route})));
   if(ticket.current())this.patch({phase:'ready',context,results:Object.freeze(results),snapshot:page.snapshot,message:null,scene:{nodes,edges}});
  }catch(error){if(ticket.current())this.patch({phase:(error as {kind?:string}).kind==='denied'?'denied':'failed',context:null,results:[],snapshot:null,message:'Campaign context could not be verified. Previous results are hidden.'});}
 }
 dispose(){this.disposed=true;this.lane.cancel();this.listeners.clear();}
}
