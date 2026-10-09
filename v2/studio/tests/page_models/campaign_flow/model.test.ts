import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {CampaignFlowModel} from '../../../src/page_models/campaign_flow/model.js';
import {readCampaignContext} from '../../../src/page_models/campaign_flow/context.js';
import {contextSchema} from '../../../src/page_models/campaign_flow/schema_pin.js';
import {knowledgeContextSchema} from '../../../src/page_models/campaign_flow/knowledge_schema_pin.js';
import {polymerProposal} from '../../../src/page_models/evaluation_review/polymer_proposal.js';
import {snapshot,detail,context,scope,deferred} from '../../fixtures/observations.js';
import type {ArtifactRef,GraphTopologyPage} from '../../../src/contracts/observations.js';
const ref:ArtifactRef={scope,artifact_id:'review-plan',schema_ref:contextSchema,sha256:'b'.repeat(64),size_bytes:20,media_type:'application/json'};
const value={format:'amphora.demo-campaign-context.v1',scope,design:polymerProposal(),bindings:[{method_id:'solvency',node_id:'node-1',candidate_id:'fixture-A',tool:{capability_id:'materials.hansen-solvency',contract_version:'1',release:'0.1.0',image_sha256:'a'.repeat(64)}}],limitations:['Synthetic']};
test('versioned Knowledge context preserves v1 and rejects schema/body disagreement',()=>{
 assert.equal(readCampaignContext(value,ref,context).knowledge,null);
 assert.equal(createHash('sha256').update(readFileSync('src/page_models/campaign_flow/context.v2.schema.json')).digest('hex'),knowledgeContextSchema.sha256);
 const next={...value,format:'amphora.demo-campaign-context.v2',knowledge:{role:'planning_context',revision:{graph:{scope,graph_id:'polymer'},revision:1,sha256:'a'.repeat(64)},methods:[{method_id:'solvency',entity_ids:['hansen']}]}};
 const nextRef={...ref,schema_ref:knowledgeContextSchema};
 assert.deepEqual(readCampaignContext(next,nextRef,context).knowledge!.entities('solvency'),['hansen']);
 assert.throws(()=>readCampaignContext(next,ref,context));
 assert.throws(()=>readCampaignContext(value,nextRef,context));
 assert.throws(()=>readCampaignContext(next,{...nextRef,schema_ref:{...knowledgeContextSchema,sha256:'0'.repeat(64)}},context));
});
function fixture(){const page=snapshot();page.nodes[1]!.kind='finish';const a=detail(1),b=detail(2);b.node=page.nodes[1]!;b.outputs=[{port:'campaign_context',kind:'artifact',item_count:1,missing_count:0,artifact:ref}];return {page,a,b};}
test('context publication pin, exact methods, scope and unique bindings are enforced',()=>{
 assert.equal(createHash('sha256').update(readFileSync('src/page_models/campaign_flow/context.schema.json')).digest('hex'),contextSchema.sha256);
 assert.equal(readCampaignContext(value,ref,context).bindings.length,1);
 for(const bad of [{...value,scope:{...scope,project_id:'wrong'}},{...value,bindings:[...value.bindings,...value.bindings]},{...value,bindings:[{...value.bindings[0],method_id:'absent'}]}])assert.throws(()=>readCampaignContext(bad,ref,context));
});
test('bounded discovery never claims completeness for a paged graph',async()=>{
 const model=new CampaignFlowModel(context,{snapshot:async()=>snapshot({total:100,next:'next'}),detail:async()=>{throw Error('Should not scan');},topology:async()=>{throw Error('Should not scan');}},{jsonArtifact:async()=>value});
 await model.refresh();assert.equal(model.snapshot.phase,'limited');assert.equal(model.snapshot.context,null);
});
test('retained plan links real activations while absent science remains unknown',async()=>{
 const {page,a,b}=fixture();const topology={cut:page.snapshot.cut,next_cursor:null,nodes:[a,b].map(d=>({activation:d.node,child_scope_count:0})),edges:[{source:a.node.activation_id,target:b.node.activation_id,route:'next'}]} as GraphTopologyPage;
 const model=new CampaignFlowModel(context,{snapshot:async()=>page,detail:async(_r,id)=>id===a.node.activation_id?a:b,topology:async()=>topology},{jsonArtifact:async()=>value});
 await model.refresh();assert.equal(model.snapshot.phase,'ready');assert.equal(model.snapshot.results[0]!.result,null);assert.match(model.snapshot.results[0]!.problem!,/No supported/);assert.equal(model.snapshot.scene!.edges.filter(e=>e.label==='next').length,1);
});
test('changed read cuts and denied content clear context; late reads stay hidden',async()=>{
 const {page,a,b}=fixture();const wait=deferred<unknown>();let phase='waiting';const model=new CampaignFlowModel(context,{snapshot:async()=>page,detail:async(_r,id)=>id===a.node.activation_id?a:b,topology:async()=>{throw Error('No topology after cancellation');}},{jsonArtifact:async()=>{if(phase==='denied')throw {kind:'denied'};return wait.promise;}});
 const first=model.refresh();await new Promise(resolve=>setTimeout(resolve,0));phase='denied';await model.refresh();assert.equal(model.snapshot.phase,'denied');wait.resolve(value);await first;assert.equal(model.snapshot.phase,'denied');assert.equal(model.snapshot.context,null);
 a.cut={...a.cut,revision:99};await model.refresh();assert.equal(model.snapshot.phase,'failed');
});
