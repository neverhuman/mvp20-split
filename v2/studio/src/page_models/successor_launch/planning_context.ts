import type {ArtifactRef,GraphSnapshotPage} from '../../contracts/observations.js';
import type {SuccessorLaunchReceipt} from '../../contracts/successor_launch.js';
import {decodeAuthoring} from '../../contracts/authoring.js';
import type {AuthoringClient} from '../../transport/authoring.js';
import type {CurationClient} from '../../transport/campaign_curation/client.js';
import type {SuccessorSubmission} from '../../transport/successor_launch/submission.js';
import type {CampaignPlanningContext} from '../launch/planning_context.js';
import type {CurationGraphReview} from '../campaign_curation/graph_review.js';
import {RecordedCuration,sameValue} from '../campaign_curation/records.js';
import {isCampaignContext} from '../campaign_flow/context.js';

/** Accepted successor plus original curation pins; no single-Knowledge legacy projection. */
export class SuccessorPlanningContext implements CampaignPlanningContext{
  readonly receipt:SuccessorLaunchReceipt;
  constructor(readonly review:CurationGraphReview,readonly command:SuccessorSubmission,receipt:SuccessorLaunchReceipt,
    private readonly drafts:Pick<AuthoringClient,'draft'>,private readonly curations:Pick<CurationClient,'curation'>){
    this.receipt=command.verify(receipt);
    const payload=command.request.payload.admission.payload;
    if(!this.receipt.run_id||!review.saved||!review.validation||!sameValue(payload.draft,review.record.data.validated_draft)||
      payload.plan_sha256!==review.validation.plan_sha256||!sameValue(payload.predecessor,review.record.data.specification.context.predecessor)||
      !sameValue(command.request.identity.scope,review.record.data.receipt.reference.scope)||command.request.identity.actor_id!==review.record.selection.actor)
      throw Error('successor_planning_binding');
    Object.freeze(this);
  }
  selection(snapshot:GraphSnapshotPage['snapshot']){
    const request=this.command.request,payload=request.payload.admission.payload;
    if(snapshot.cut.run_id!==this.receipt.run_id||snapshot.cut.plan_sha256!==payload.plan_sha256||!sameValue(snapshot.cut.scope,request.identity.scope))throw Error('successor_observation_mismatch');
    return {scope:request.identity.scope,draft_id:payload.draft.draft_id,revision:payload.draft.revision,content_sha256:payload.draft.content_sha256};
  }
  private async draft(snapshot:GraphSnapshotPage['snapshot'],signal:AbortSignal){
    const selection=this.selection(snapshot),record=decodeAuthoring('draft',await this.drafts.draft(selection.draft_id,selection.revision,signal));
    if(signal.aborted)throw Error('aborted');
    if(!sameValue(record.scope,selection.scope)||record.head.draft_id!==selection.draft_id||record.head.revision!==selection.revision||
      record.head.content_sha256!==selection.content_sha256||!sameValue(record.definition,this.review.proposed.definition))throw Error('successor_draft_mismatch');
    return record;
  }
  async reference(snapshot:GraphSnapshotPage['snapshot'],signal:AbortSignal):Promise<ArtifactRef|null>{
    const record=await this.draft(snapshot,signal),inputs=this.command.request.payload.admission.payload.inputs,refs:ArtifactRef[]=[];
    for(const node of record.definition.body.nodes){if(node.kind!=='finish')continue;for(const output of node.outputs){
      const source=output.source,value=source.kind==='input'?inputs.find(input=>input.port===source.name)?.value:source;
      if(value?.kind==='artifact'&&isCampaignContext(value.artifact))refs.push(value.artifact);
    }}
    if(refs.length>1)throw Error('successor_context_ambiguous');return refs[0]??null;
  }
  async curationContext(snapshot:GraphSnapshotPage['snapshot'],signal:AbortSignal){
    const draft=this.selection(snapshot);await this.draft(snapshot,signal);
    const raw=await this.curations.curation(this.review.record.selection,signal);
    if(signal.aborted||!raw)throw Error('curation_origin_unavailable');
    const record=new RecordedCuration(raw,this.review.record.selection);this.review.record.reconcile(record);
    const original=record.data.specification.context;
    return {predecessor:{run_id:snapshot.cut.run_id,revision:snapshot.cut.revision,plan_sha256:snapshot.cut.plan_sha256},draft,
      knowledge:structuredClone(original.knowledge),questions:structuredClone(original.questions),needs:structuredClone(original.needs),artifacts:structuredClone(original.artifacts)};
  }
}
