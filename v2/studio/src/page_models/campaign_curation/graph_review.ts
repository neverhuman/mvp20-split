import {decodeAuthoring,type DraftRevision,type DraftValidation,type SaveDraft} from '../../contracts/authoring.js';
import type {AuthoringClient} from '../../transport/authoring.js';
import {sameScope} from '../../transport/campaign_curation/identity.js';
import {GraphDefinitionComparison} from '../design/draft_comparison.js';
import {immutable} from '../explore/context.js';
import {RecordedCuration,sameValue} from './records.js';

function requireBinding(condition:boolean){if(!condition)throw Error('curation_graph_binding');}
function bindDraft(raw:DraftRevision,expected:{draft_id:string;revision:number;content_sha256:string},scope:DraftRevision['scope']){
  const draft=decodeAuthoring('draft',raw);
  requireBinding(sameScope(draft.scope,scope)&&sameScope(draft.definition.scope,scope)&&draft.head.draft_id===expected.draft_id&&
    draft.head.revision===expected.revision&&draft.head.content_sha256===expected.content_sha256);
  return draft;
}

/** Same-scope original/model pair; campaign identity changes remain visible structural edits. */
export class CurationGraphReview {
  readonly original:DraftRevision;
  readonly proposed:Pick<SaveDraft,'title'|'definition'>;
  readonly saved:DraftRevision|null;
  readonly validation:DraftValidation|null;
  readonly comparison:GraphDefinitionComparison;
  constructor(readonly record:RecordedCuration,original:DraftRevision,saved:DraftRevision|null,validation:DraftValidation|null){
    const value=record.data, outcome=value.proposal?.outcome;
    requireBinding(outcome?.kind==='propose_campaign');
    if(outcome?.kind!=='propose_campaign')throw Error('curation_graph_unavailable');
    const scope=value.receipt.reference.scope;
    this.original=immutable(bindDraft(original,value.specification.context.draft,scope));
    requireBinding(sameScope(outcome.candidate.definition.scope,scope));
    this.proposed=immutable({title:outcome.candidate.title,definition:outcome.candidate.definition});
    const selection=value.validated_draft;
    if(selection){
      requireBinding(saved!==null&&validation!==null);
      const exact=bindDraft(saved!,selection,scope),checked=decodeAuthoring('validation',validation);
      requireBinding(sameValue(exact.definition,this.proposed.definition)&&exact.head.title===this.proposed.title);
      requireBinding(sameScope(checked.scope,scope)&&checked.draft_id===selection.draft_id&&checked.revision===selection.revision&&
        checked.content_sha256===selection.content_sha256&&checked.validation_id===selection.validation_id&&
        checked.universe_sha256===selection.universe_sha256&&checked.structurally_valid&&checked.plan_sha256!==null);
      this.saved=immutable(exact);this.validation=immutable(checked);
    }else{requireBinding(saved===null&&validation===null);this.saved=null;this.validation=null;}
    this.comparison=new GraphDefinitionComparison({title:this.original.head.title,definition:this.original.definition},this.proposed);
    Object.freeze(this);
  }
}

/** Exact public revision reads, not current heads or a browser reconstruction of the model graph. */
export class CurationGraphReader {
  constructor(private readonly source:Pick<AuthoringClient,'draft'|'validation'>){}
  async read(record:RecordedCuration,signal:AbortSignal){
    if(record.data.proposal?.outcome.kind!=='propose_campaign')return null;
    const original=record.data.specification.context.draft,selected=record.data.validated_draft;
    const before=await this.source.draft(original.draft_id,original.revision,signal);
    if(signal.aborted)throw Error('aborted');
    let saved:DraftRevision|null=null,validation:DraftValidation|null=null;
    if(selected){
      saved=await this.source.draft(selected.draft_id,selected.revision,signal);if(signal.aborted)throw Error('aborted');
      validation=await this.source.validation(selected.validation_id,signal);if(signal.aborted)throw Error('aborted');
    }
    return new CurationGraphReview(record,before,saved,validation);
  }
}
