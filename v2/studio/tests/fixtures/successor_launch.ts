import {SuccessorSubmission} from '../../src/transport/successor_launch/submission.js';
import type {AdmitDraftSuccessor,SuccessorLaunchReceipt} from '../../src/contracts/successor_launch.js';
export function successorCommand(id='next',number='1.25'){
  const scope={tenant_id:'internal',project_id:'demo'};
  const payload:AdmitDraftSuccessor={plan_sha256:'b'.repeat(64),inputs:[{port:'input',value:{kind:'number',value:number}}],budget:{limit:3},
    draft:{draft_id:'draft',revision:2,content_sha256:'c'.repeat(64),validation_id:'validated',universe_sha256:'d'.repeat(64)},
    predecessor:{run_id:'parent',plan_sha256:'e'.repeat(64),revision:4},
    carried:[{target_port:'value',source:{kind:'run_output',port:'value'},expected_value_sha256:'f'.repeat(64)}]};
  return SuccessorSubmission.create({scope,actor_id:'owner',command_family:'campaign.launch_successor',command_id:id},payload,
    {profile_id:'synthetic',version:'1',sha256:'a'.repeat(64)});
}
export function successorReceipt(command=successorCommand()):SuccessorLaunchReceipt{
  const request=command.request;
  return {wire_version:'1',profile_kind:'campaign-successor-launch.v1',identity:{schema_version:'1',...request.identity},request_sha256:'1'.repeat(64),
    profile:request.payload.profile,predecessor:request.payload.admission.payload.predecessor,revision:0,phase:'preparing',reason_code:null,
    created_at:'2026-10-12T08:00:00Z',updated_at:'2026-10-12T08:00:00Z',admission:null,run_id:null,workers:{ready:0,expected:2}};
}
