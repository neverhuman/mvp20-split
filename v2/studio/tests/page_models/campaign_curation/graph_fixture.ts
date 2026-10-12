import {fixture} from '../../transport/campaign_curation/fixtures.js';
import {local,revision} from '../../fixtures/authoring.js';
import {RecordedCuration} from '../../../src/page_models/campaign_curation/records.js';
import type {DraftValidation} from '../../../src/contracts/authoring.js';

export function graphFixture(){
  const f=fixture(),content=local();content.definition.scope=f.scope;
  const original=revision(1,content);original.scope=f.scope;
  original.head={...original.head,draft_id:f.curation.specification.context.draft.draft_id,content_sha256:f.curation.specification.context.draft.content_sha256};
  const proposed=structuredClone(content);proposed.definition.campaign_id='next-campaign';proposed.title='Revised heating sequence';
  proposed.definition.body.nodes.unshift({kind:'invoke',node_id:'heat-mixture',inputs:[],timeout_seconds:60,
    tool:{capability_id:'synthetic.heat',contract_version:'1',release:'1.0.0',image_sha256:'a'.repeat(64)}});
  proposed.definition.body.edges=[{source:'heat-mixture',target:'done',route:'next'}];
  const finish=proposed.definition.body.nodes[1]!;if(finish.kind==='finish')finish.outputs=[{port:'material',source:{kind:'output',node_id:'heat-mixture',port:'material'}}];
  const saved=revision(1,proposed);saved.scope=f.scope;saved.head.draft_id='proposed-draft';
  const selected={draft_id:saved.head.draft_id,revision:1,content_sha256:saved.head.content_sha256,validation_id:'validation',universe_sha256:'e'.repeat(64)};
  const validation:DraftValidation={...selected,scope:f.scope,structurally_valid:true,plan_sha256:'f'.repeat(64),pending_checks:['current_execution_eligibility'],findings:[]};
  f.curation.receipt.phase='ready';f.curation.receipt.reason_code=null;
  f.curation.proposal!.outcome={kind:'propose_campaign',candidate:{kind:'future_campaign',...proposed,expected_evidence:[]},gaps:[]};
  f.curation.capability_requests=[];f.curation.validated_draft=selected;
  return {...f,original,proposed,saved,validation,record:new RecordedCuration(f.curation,f.selection)};
}
