import {test} from 'node:test';
import assert from 'node:assert/strict';
import {CampaignKnowledge} from '../../../src/page_models/campaign_flow/knowledge.js';
import {polymerProposal} from '../../../src/page_models/evaluation_review/polymer_proposal.js';
import {scope} from '../../fixtures/observations.js';
const value=()=>({role:'planning_context',revision:{graph:{scope,graph_id:'polymer-domain'},revision:1,sha256:'a'.repeat(64)},methods:[{method_id:'solvency',entity_ids:['hansen-screening']}]});
test('Knowledge planning association pins scope and revision without claiming tool consumption',()=>{
 const raw=value(),link=new CampaignKnowledge(raw,scope,polymerProposal());
 raw.methods[0]!.entity_ids.push('later');
 assert.deepEqual(link.entities('solvency'),['hansen-screening']);
 assert.deepEqual(link.entities('missing'),[]);
 assert.equal(link.role,'planning_context');assert.equal(link.pins.graph!.revision,1);
 assert.ok(Object.isFrozen(link.methods[0]!.entity_ids));
});
test('Knowledge association rejects scope drift, unsupported roles and ambiguous method mappings',()=>{
 for(const bad of [
  {...value(),role:'consumed_by_tool'},
  {...value(),revision:{...value().revision,revision:0}},
  {...value(),revision:{...value().revision,graph:{scope:{...scope,project_id:'other'},graph_id:'polymer-domain'}}},
  {...value(),methods:[{method_id:'missing',entity_ids:['x']}]},
  {...value(),methods:[...value().methods,...value().methods]},
  {...value(),methods:[{method_id:'solvency',entity_ids:['x','x']}]},
  {...value(),methods:[]}, {...value(),unexpected:true},
 ])assert.throws(()=>new CampaignKnowledge(bad,scope,polymerProposal()));
});
