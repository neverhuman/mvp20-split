import {decodeLaunch,type LaunchProfileCatalog} from '../../contracts/launch.js';
import {decodeSuccessor,type CarrySources,type AdmitDraftSuccessor} from '../../contracts/successor_launch.js';
import type {LaunchClient} from '../../transport/launch/client.js';
import type {SuccessorSources} from '../../transport/successor_launch/sources.js';
import {SuccessorSubmission} from '../../transport/successor_launch/submission.js';
import type {CurationGraphReview} from '../campaign_curation/graph_review.js';
import {same} from '../../transport/scientific/identity.js';
import {immutable} from '../explore/context.js';
import {RequestLane} from '../request_lane.js';

type Profile=LaunchProfileCatalog['profiles'][number];
function tools(review:CurationGraphReview){
  const pending=[review.proposed.definition.body],result=[];
  while(pending.length){for(const node of pending.pop()!.nodes){
    if(node.kind==='invoke')result.push(node.tool);
    if(node.kind==='scatter'||node.kind==='iterate')pending.push(node.body);
  }}return result;
}
/** Explicit mapping from committed exports to required inputs. Runtime rechecks value compatibility. */
export class PreparedSuccessor{
  readonly sources:CarrySources;readonly profiles:readonly Profile[];
  readonly inputs:ReadonlyArray<{name:string;description:string}>;
  constructor(readonly review:CurationGraphReview,sources:CarrySources,catalog:LaunchProfileCatalog){
    const record=review.record.data,scope=record.receipt.reference.scope;
    if(record.receipt.phase!=='ready'||!review.saved||!review.validation||!record.validated_draft)throw Error('successor_validated_proposal_required');
    decodeSuccessor('sources',sources);decodeLaunch('catalog',catalog);
    if(!same(sources.scope,scope)||!same(catalog.scope,scope)||!same(sources.predecessor,record.specification.context.predecessor))throw Error('successor_predecessor_changed');
    if(!sources.predecessor_ready)throw Error('successor_predecessor_unsettled');
    const keys=sources.sources.map(item=>JSON.stringify(item.source));
    if(new Set(keys).size!==keys.length||sources.sources.some(item=>item.source.kind==='node_output'))throw Error('successor_sources_invalid');
    if(catalog.profiles.some(profile=>!same(profile.scope,scope))||new Set(catalog.profiles.map(profile=>profile.reference.profile_id)).size!==catalog.profiles.length)throw Error('successor_profiles_invalid');
    const required=tools(review);
    this.profiles=immutable(catalog.profiles.filter(profile=>required.every(tool=>profile.tools.some(candidate=>same(candidate,tool)))));
    this.sources=immutable(sources);
    const ports=review.proposed.definition.body.inputs??[];
    if(new Set(ports.map(port=>port.name)).size!==ports.length)throw Error('successor_inputs_ambiguous');
    this.inputs=immutable(ports.map(port=>({name:port.name,description:port.value_type.kind==='scalar'?port.value_type.scalar:port.value_type.kind})));
    Object.freeze(this);
  }
  command(id:string,profileId:string,selections:Readonly<Record<string,number>>){
    const profile=this.profiles.find(item=>item.reference.profile_id===profileId);
    if(!profile||Object.keys(selections).length!==this.inputs.length||Object.keys(selections).some(name=>!this.inputs.some(port=>port.name===name)))throw Error('successor_inputs_required');
    const carried=this.inputs.map(port=>{
      const index=selections[port.name],source=index!==undefined&&Number.isSafeInteger(index)?this.sources.sources[index]:undefined;
      if(!source)throw Error('successor_inputs_required');
      return {target_port:port.name,source:structuredClone(source.source),expected_value_sha256:source.value_sha256};
    });
    const record=this.review.record.data;
    const payload:AdmitDraftSuccessor={draft:record.validated_draft!,plan_sha256:this.review.validation!.plan_sha256!,predecessor:this.sources.predecessor,
      inputs:[],carried,budget:{limit:profile.maximum_invocations,max_attempts_per_activation:2},
      limits:{max_activations:10000,deadline_seconds:profile.maximum_deadline_seconds}};
    return SuccessorSubmission.create({...record.receipt.identity,command_id:id,command_family:'campaign.launch_successor'},payload,profile.reference);
  }
}

interface View{phase:'idle'|'loading'|'ready'|'denied'|'failed';prepared:PreparedSuccessor|null;reason:string|null}
export class SuccessorPreparation{
  private readonly lane=new RequestLane();private readonly listeners=new Set<()=>void>();private disposed=false;
  private view:Readonly<View>=Object.freeze({phase:'idle',prepared:null,reason:null});
  constructor(private readonly sources:Pick<SuccessorSources,'read'>,private readonly profiles:Pick<LaunchClient,'profiles'>){}
  get snapshot(){return this.view;}
  subscribe(listener:()=>void){this.listeners.add(listener);return()=>{this.listeners.delete(listener);};}
  private patch(view:View){if(this.disposed)return;this.view=Object.freeze(view);for(const listener of this.listeners)listener();}
  async load(review:CurationGraphReview){
    if(this.disposed)return;const lane=this.lane.begin();this.patch({phase:'loading',prepared:null,reason:null});if(!lane.current())return;
    try{
      const sources=await this.sources.read(review.record.data.specification.context.predecessor.run_id,lane.signal);if(!lane.current())return;
      const profiles=await this.profiles.profiles(lane.signal);if(!lane.current())return;
      this.patch({phase:'ready',prepared:new PreparedSuccessor(review,sources,profiles),reason:null});
    }catch(error){
      if(!lane.current())return;const denied=error!==null&&typeof error==='object'&&'kind'in error&&error.kind==='denied';
      const reason=error instanceof Error&&['successor_predecessor_changed','successor_predecessor_unsettled'].includes(error.message)?error.message:'preparation_unavailable';
      this.patch({phase:denied?'denied':'failed',prepared:null,reason:denied?'denied':reason});
    }
  }
  clear(){this.lane.cancel();this.patch({phase:'idle',prepared:null,reason:null});}
  dispose(){this.disposed=true;this.lane.cancel();this.view=Object.freeze({phase:'idle',prepared:null,reason:null});this.listeners.clear();}
}
