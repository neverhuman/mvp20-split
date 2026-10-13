import { decodeCurationRequest, type CurationRequest } from '../../contracts/campaign_curation.js';
import type { ArtifactRef,GraphSnapshotPage } from '../../contracts/observations.js';
import type { OriginDraft } from '../../contracts/campaign_origin.js';
import type { ObservationSource } from '../../transport/observations.js';
import type { OriginReader } from '../campaign_origin/reader.js';
import { same } from '../../transport/scientific/identity.js';
import { sameScope } from '../../transport/campaign_curation/identity.js';
import { immutable } from '../explore/context.js';
import { RequestLane } from '../request_lane.js';
import type { CurationActor } from './journal.js';
import {CurationArtifactInputs} from './artifact_inputs.js';

type Snapshot=GraphSnapshotPage['snapshot'];
type Context=CurationRequest['payload']['context'];
export interface CampaignDraftBinding { selection(snapshot:Snapshot):OriginDraft; inputArtifacts?(snapshot:Snapshot):ArtifactRef[] }

/** Retained original provenance supplies explicit next-request pins, not consumed-context claims. */
export class OriginalCurationContext {
  constructor(private readonly binding:CampaignDraftBinding,private readonly origin:Pick<OriginReader,'readBound'>) {}
  async read(snapshot:Snapshot,signal:AbortSignal):Promise<Context> {
    const draft=this.binding.selection(snapshot), bound=await this.origin.readBound(draft,signal),record=bound?.origin;
    if(signal.aborted)throw Error('aborted');
    if(!record)throw Error('curation_origin_unavailable');
    if(!same(record.origin.draft,draft))throw Error('curation_origin_mismatch');
    const knowledge=record.origin.knowledge, research=record.origin.research.selection;
    if(knowledge&&(knowledge.status!=='available'||!knowledge.head))throw Error('curation_knowledge_unavailable');
    return {predecessor:{run_id:snapshot.cut.run_id,revision:snapshot.cut.revision,plan_sha256:snapshot.cut.plan_sha256},
      draft,knowledge:knowledge?.head?[knowledge.head]:[],questions:research?.questions??[],needs:research?.needs??[],
      artifacts:CurationArtifactInputs.collect(bound!.draft.definition,this.binding.inputArtifacts?.(snapshot)??[])};
  }
}

/** Bounded reviewed context can carry all eight Knowledge heads; no first-item selection. */
export class PreparedCuration {
  readonly context:Context;
  readonly actor:CurationActor;
  constructor(actor:CurationActor,readonly policyId:string,context:Context) {
    this.actor=immutable(actor);this.context=immutable(context);
    const probe=this.request('Check the next campaign context','preparation');
    decodeCurationRequest(probe);
    const scopes=[context.draft.scope,...context.knowledge.flatMap(head=>[head.snapshot.graph.scope,head.change.graph.scope]),
      ...[...context.questions,...context.needs,...context.artifacts].map(ref=>ref.scope)];
    if(context.predecessor.run_id!==actor.run_id||scopes.some(scope=>!sameScope(scope,actor.scope)))throw Error('curation_context_scope');
    if(context.knowledge.some(head=>!same(head.snapshot.graph,head.change.graph)))throw Error('curation_context_graph');
    for(const keys of [context.knowledge.map(head=>head.snapshot.graph.graph_id),context.questions.map(ref=>ref.question_id),
      context.needs.map(ref=>ref.need_id),context.artifacts.map(ref=>ref.artifact_id)])
      if(new Set(keys).size!==keys.length)throw Error('curation_context_duplicate');
    Object.freeze(this);
  }
  request(direction:string,commandId:string):CurationRequest {
    return decodeCurationRequest({encoding:'amphora-command-v2',identity:{schema_version:'1',scope:structuredClone(this.actor.scope),
      actor_id:this.actor.actor_id,command_family:'planning.curate_campaign',command_id:commandId},
      payload:{direction,policy_id:this.policyId,context:structuredClone(this.context)}});
  }
}

interface PreparationView {phase:'idle'|'loading'|'ready'|'running'|'denied'|'failed';prepared:PreparedCuration|null;reason:string|null}
/** Fresh Runtime terminal cut plus exact launch-bound draft; no command or model call. */
export class CurationPreparation {
  private readonly lane=new RequestLane();private readonly listeners=new Set<()=>void>();private disposed=false;
  private view:Readonly<PreparationView>=Object.freeze({phase:'idle',prepared:null,reason:null});
  constructor(private readonly actor:CurationActor,private readonly policyId:string,
    private readonly runtime:Pick<ObservationSource,'snapshot'>,private readonly source:{read(snapshot:Snapshot,signal:AbortSignal):Promise<Context>}){this.actor=immutable(actor);}
  get snapshot(){return this.view;}
  subscribe(listener:()=>void){this.listeners.add(listener);return()=>{this.listeners.delete(listener);};}
  private patch(view:PreparationView){if(this.disposed)return;this.view=Object.freeze(view);for(const listener of this.listeners)listener();}
  async load(){
    if(this.disposed)return;const lane=this.lane.begin();this.patch({phase:'loading',prepared:null,reason:null});
    if(!lane.current())return;
    try{
      const page=await this.runtime.snapshot(this.actor.run_id,{scope_key:null,frontier_only:false},undefined,lane.signal);
      if(!lane.current())return;
      const snapshot=page.snapshot;
      if(!sameScope(snapshot.cut.scope,this.actor.scope)||snapshot.cut.run_id!==this.actor.run_id)throw Error('curation_predecessor_mismatch');
      if(!['completed','failed','cancelled','blocked'].includes(snapshot.status)) {this.patch({phase:'running',prepared:null,reason:'predecessor_not_terminal'});return;}
      const context=await this.source.read(snapshot,lane.signal);if(!lane.current())return;
      if(!same(context.predecessor,{run_id:snapshot.cut.run_id,revision:snapshot.cut.revision,plan_sha256:snapshot.cut.plan_sha256}))throw Error('curation_predecessor_mismatch');
      this.patch({phase:'ready',prepared:new PreparedCuration(this.actor,this.policyId,context),reason:null});
    }catch(error){
      if(!lane.current())return;
      const denied=error!==null&&typeof error==='object'&&'kind' in error&&error.kind==='denied';
      const reason=error instanceof Error&&['curation_origin_unavailable','curation_knowledge_unavailable'].includes(error.message)?error.message:'context_unavailable';
      this.patch({phase:denied?'denied':'failed',prepared:null,reason:denied?'denied':reason});
    }
  }
  clear(){this.lane.cancel();this.patch({phase:'idle',prepared:null,reason:null});}
  dispose(){this.disposed=true;this.lane.cancel();this.view=Object.freeze({phase:'idle',prepared:null,reason:null});this.listeners.clear();}
}
