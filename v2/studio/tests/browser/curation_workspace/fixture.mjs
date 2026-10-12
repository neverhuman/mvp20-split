/** Scripted public owners for the actual Studio entry; no provider/science claim. */
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {snapshot,detail} from '../../../dist/tests/fixtures/observations.js';
import {topology} from '../../../dist/tests/fixtures/navigation.js';
import {receipt as launchReceipt,profile} from '../../../dist/tests/fixtures/launch.js';
import {fixture as curationFixture} from '../../../dist/tests/transport/campaign_curation/fixtures.js';
import {Submission} from '../../../dist/src/transport/submission.js';
import {LaunchSubmission} from '../../../dist/src/transport/launch/submission.js';
import {CurationSubmission} from '../../../dist/src/transport/campaign_curation/submission.js';
import {SuccessorSubmission} from '../../../dist/src/transport/successor_launch/submission.js';
import {canonical} from '../../../dist/src/transport/scientific/identity.js';
import {polymerProposal} from '../../../dist/src/page_models/evaluation_review/polymer_proposal.js';
import {contextSchema} from '../../../dist/src/page_models/campaign_flow/schema_pin.js';

export async function workspaceFixture(publicDir){
  const base=JSON.parse(await readFile('tests/fixtures/campaign_origin/record.json','utf8'));
  const scope=base.draft.scope,actor_id='researcher',original=base.draft,tool=original.definition.body.nodes[0].tool;
  const plan={format:'amphora.demo-campaign-context.v1',scope,design:polymerProposal(),bindings:[{method_id:'solvency',node_id:'node-1',candidate_id:'fixture-A',tool}],limitations:['Scripted public peers; no actual calculation.']};
  const bytes=Buffer.from(JSON.stringify(plan)),artifact={scope,artifact_id:'launch-plan',schema_ref:contextSchema,sha256:createHash('sha256').update(bytes).digest('hex'),size_bytes:bytes.length,media_type:'application/json'};
  original.definition.body={nodes:[{kind:'invoke',node_id:'node-1',tool,inputs:[],timeout_seconds:60},
    {kind:'finish',node_id:'node-2',outputs:[{port:'campaign_context',source:{kind:'artifact',artifact,representation:'campaign-review-context',unit:'1'}}]}],edges:[{source:'node-1',target:'node-2',route:'next'}]};
  const origin=base.origin;origin.origin.tools[0].node.node_id='node-1';
  origin.origin_sha256=createHash('sha256').update(canonical(origin.origin)).digest('hex');
  const proposed=structuredClone(original);proposed.head={...proposed.head,draft_id:'revised-draft',title:'Revised research sequence',content_sha256:'b'.repeat(64)};
  proposed.definition.campaign_id='revised-campaign';
  const validated={scope,draft_id:'revised-draft',revision:1,content_sha256:proposed.head.content_sha256,validation_id:'next-validation',universe_sha256:'c'.repeat(64),
    structurally_valid:true,plan_sha256:'d'.repeat(64),pending_checks:['current_execution_eligibility'],findings:[]};
  const initial=LaunchSubmission.from(new Submission('admit',{scope,actor_id,command_family:'graph.admit_draft',command_id:'original-launch'},
    {inputs:[],budget:{limit:8},plan_sha256:'a'.repeat(64),draft:{draft_id:original.head.draft_id,revision:1,content_sha256:original.head.content_sha256,validation_id:'original-validation',universe_sha256:'c'.repeat(64)}}),profile);
  const originalReceipt=launchReceipt(initial,true);originalReceipt.phase='released';originalReceipt.workers={expected:1,ready:0};
  const storageKey='amphora.launch.v1:'+JSON.stringify([scope.tenant_id,scope.project_id,actor_id]);
  const seed={key:storageKey,value:JSON.stringify({version:1,body:initial.body,receipt:originalReceipt})};
  let successor=null,childComplete=false;const curations=new Map(),capabilities=new Map(),counts={curation:0,successor:0,fresh:0},requests=[],errors=[];
  const pageWire=run=>{
    const page=snapshot({run});page.snapshot.cut.scope=scope;page.snapshot.cut.plan_sha256=run==='actual-run'?'a'.repeat(64):validated.plan_sha256;
    page.nodes[1].kind='finish';if(run==='actual-run'||childComplete){page.snapshot.status='completed';page.nodes.forEach(node=>node.status='succeeded');}return page;
  };
  const intake=async body=>{
    const command=await CurationSubmission.restore(body),request=command.request;
    assert.deepEqual(request.identity.scope,scope);assert.equal(request.identity.actor_id,actor_id);counts.curation++;
    const f=curationFixture(),missing=counts.curation>1;
    const receipt={wire_version:'1',identity:request.identity,request_sha256:command.sha256,reference:command.selection.reference,revision:0,phase:'queued',reason_code:null,
      created_at:'2026-10-12T08:00:00Z',updated_at:'2026-10-12T08:00:00Z'};
    const value=f.curation;value.specification=request.payload;value.receipt={...receipt,revision:3,phase:missing?'proposed':'ready',reason_code:missing?'capabilities_requested':null};
    value.provider.attempt.engagement={scope,engagement_id:'curation-call-'+command.sha256};
    if(missing){
      const ref={scope,request_id:'capability-'+command.curationId.slice('curation-'.length)+'-00'};
      value.capability_requests=[ref];value.validated_draft=null;
      const capability={...f.capability,reference:ref,curation:command.selection.reference};capabilities.set(ref.request_id,capability);
    }else{
      value.proposal.outcome={kind:'propose_campaign',candidate:{kind:'future_campaign',title:proposed.head.title,definition:proposed.definition,expected_evidence:[]},gaps:[]};
      value.capability_requests=[];value.validated_draft={draft_id:validated.draft_id,revision:validated.revision,content_sha256:validated.content_sha256,validation_id:validated.validation_id,universe_sha256:validated.universe_sha256};
    }
    curations.set(command.curationId,{command,receipt,value,reads:0});return receipt;
  };
  const handle=async(req,res)=>{
    try{
      const url=new URL(req.url,'http://localhost'),path=url.pathname;let body='';for await(const chunk of req)body+=chunk;
      requests.push([req.method,path]);const send=(value,status=200)=>{res.writeHead(status,{'Content-Type':'application/json'});res.end(JSON.stringify(value));};
      if(path==='/session')return send({scope,actor_id,run_id:'actual-run',synthetic:true});
      if(path==='/api/deployment/v1/campaign-launch-profiles')return send({scope,profiles:[{scope,reference:profile,title:'Synthetic installed research tools',tools:[tool],maximum_invocations:8,maximum_deadline_seconds:300}]});
      if(path==='/api/deployment/v1/campaign-launches'){counts.fresh++;throw Error('unexpected fresh admission');}
      if(path.startsWith('/api/deployment/v1/campaign-launches/'))return send(originalReceipt);
      if(path==='/api/runtime/v1/definition-drafts')return send({scope,drafts:[original.head,proposed.head],next_after:null});
      if(path.startsWith('/api/runtime/v1/definition-drafts/'))return send(path.endsWith('/revised-draft')?proposed:original);
      if(path==='/api/runtime/v1/definition-validations/next-validation')return send(validated);
      if(path.startsWith('/api/runtime/v1/definition-commands/'))return send(origin.origin.save.receipt);
      if(path.startsWith('/api/planning/v1/campaign-origins/'))return path.endsWith('/'+original.head.draft_id)?send(origin):send({reason_code:'campaign_origin_not_recorded'},404);
      if(path==='/api/planning/v1/campaign-curations'&&req.method==='POST')return send(await intake(body),202);
      if(path==='/api/planning/v1/campaign-curations/receipts/query'){
        const query=JSON.parse(body),row=[...curations.values()].find(item=>item.command.request.identity.command_id===query.identity.command_id);
        assert.ok(row);assert.equal(query.request_sha256,row.command.sha256);return send(row.receipt);
      }
      if(path.startsWith('/api/planning/v1/campaign-curations/')){
        const row=curations.get(path.split('/').at(-1));assert.ok(row);row.reads++;
        return send(row.reads===1?{...row.value,receipt:row.receipt,provider:null,proposal:null,capability_requests:[],validated_draft:null}:row.value);
      }
      if(path.startsWith('/api/planning/v1/capability-requests/'))return send(capabilities.get(path.split('/').at(-1)));
      if(path.endsWith('/carry-sources')){const run=path.split('/').at(-2),cut=pageWire(run).snapshot.cut;return send({scope,predecessor:{run_id:run,revision:cut.revision,plan_sha256:cut.plan_sha256},predecessor_ready:true,sources:[]});}
      if(path==='/api/deployment/v1/campaign-successor-launches'&&req.method==='POST'){
        const command=SuccessorSubmission.restore(body),request=command.request;counts.successor++;
        assert.deepEqual(request.payload.admission.payload.draft,[...curations.values()][0].value.validated_draft);
        successor={profile_kind:'campaign-successor-launch.v1',identity:request.identity,request_sha256:'8'.repeat(64),profile,predecessor:request.payload.admission.payload.predecessor,
          revision:3,phase:'engaged',reason_code:null,created_at:'2026-10-12T08:00:00Z',updated_at:'2026-10-12T08:01:00Z',run_id:'successor-run',workers:{expected:1,ready:1},
          admission:{outcome:{status:'accepted',binding:{identity:request.payload.admission.identity,operation_id:'successor-admission',request_sha256:'9'.repeat(64)},committed:{kind:'run',object_id:'successor-run',revision:0}}}};
        return send(successor,202);
      }
      if(path.startsWith('/api/deployment/v1/campaign-successor-launches/'))return send(successor);
      if(path==='/api/data/v1/artifacts/launch-plan')return send(artifact);
      if(path==='/api/data/v1/artifacts/launch-plan/content'){res.writeHead(200,{'Content-Type':'application/json','Content-Length':bytes.length});return res.end(bytes);}
      const graph=/\/graph-observations\/(actual-run|successor-run)\/nodes(?:\/([0-9a-f]+))?$/.exec(path);
      if(graph){const run=graph[1],page=pageWire(run);if(!graph[2])return send(page);
        const index=Number.parseInt(graph[2],16),node=detail(index);node.cut=page.snapshot.cut;node.node=page.nodes[index-1];
        if(page.snapshot.status==='completed'&&index===2)node.outputs=[{port:'campaign_context',kind:'artifact',item_count:1,missing_count:0,artifact}];return send(node);}
      if(path.endsWith('/topology')){const run=path.includes('successor-run')?'successor-run':'actual-run',page=pageWire(run),value=topology();value.cut=page.snapshot.cut;value.nodes.forEach((node,index)=>node.activation=page.nodes[index]);return send(value);}
      if(path.startsWith('/api/'))return send({},404);
      const name=path==='/'?'index.html':path.slice(1);if(!['index.html','app.js','app.css'].includes(name))return send({},404);
      res.writeHead(200,{'Content-Type':name.endsWith('.js')?'text/javascript':name.endsWith('.css')?'text/css':'text/html'});res.end(await readFile(resolve(publicDir,name)));
    }catch(error){errors.push(String(error));res.writeHead(500);res.end('fixture failure');}
  };
  return {handle,seed,counts,requests,errors,completeChild:()=>{childComplete=true;},curations};
}
