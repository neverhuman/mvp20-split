import {test} from 'node:test';
import assert from 'node:assert/strict';
import {EvaluationReview,parseDesign} from '../../../src/page_models/evaluation_review/model.js';
import {polymerProposal} from '../../../src/page_models/evaluation_review/polymer_proposal.js';
import {layoutGraph} from '../../../src/page_models/graph_layout/layout.js';

test('SME concerns survive export with the exact unexecuted design',()=>{
  const review=new EvaluationReview(polymerProposal());
  review.save('solvency','inappropriate_method','Material state is outside the method domain.');
  review.save('objective','missing_criterion','Define the biological context before claiming bioavailability.');
  review.save('selection','misleading_aggregation','Declare how unknown synthesis evidence affects selection.');
  const recovered=EvaluationReview.import(review.export());
  assert.deepEqual(recovered.design,review.design);assert.deepEqual(recovered.feedback,review.feedback);
  const raw=JSON.parse(review.export());assert.equal(raw.authority,'local_unsubmitted');assert.equal(raw.target,'future_campaign_only');
  assert.equal(review.design.provenance.origin,'design_proposal');assert.ok(review.design.nodes.every(n=>n.evidence&&!n.evidence.includes('succeeded')));
});
test('rejects malformed relationships, hidden extra fields and claimed execution authority',()=>{
  for(const mutate of [(d:any)=>d.edges[0].target='missing',(d:any)=>d.nodes.push(d.nodes[0]),(d:any)=>d.provenance.origin='executed',
    (d:any)=>d.nodes[0].score=1,(d:any)=>d.edges.push({source:'iteration',target:'objective',relationship:'fake running loop'}),
    (d:any)=>d.edges=d.edges.filter((e:any)=>e.target!=='solvency'),(d:any)=>d.nodes[1].kind='objective']){
    const d=JSON.parse(JSON.stringify(polymerProposal()));mutate(d);assert.throws(()=>parseDesign(JSON.stringify(d)));
  }
});
test('imports are bounded and feedback cannot retarget an unknown node or future policy',()=>{
  const r=new EvaluationReview(polymerProposal());r.save('solvency','unsupported_assumption','Verify parameter availability.');
  for(const mutate of [(d:any)=>d.target='running_campaign',(d:any)=>d.notes[0].node='elsewhere',(d:any)=>d.notes[0].concern='approved',
    (d:any)=>d.notes.push(d.notes[0]),(d:any)=>d.notes[0].change=' ',(d:any)=>d.design.nodes[0].title='x'.repeat(161)]){
    const d=JSON.parse(r.export());mutate(d);assert.throws(()=>EvaluationReview.import(JSON.stringify(d)));
  }
  assert.throws(()=>EvaluationReview.import(' '.repeat(524289)));assert.throws(()=>parseDesign(' '.repeat(262145)));
  assert.equal(EvaluationReview.import(JSON.stringify(polymerProposal())).feedback.length,0);
});
test('same node supports distinct concerns and deliberate updates/removal',()=>{
  const r=new EvaluationReview(polymerProposal());r.save('solvency','inappropriate_method','First');r.save('solvency','inappropriate_method','Revised');r.save('solvency','unsupported_assumption','Second');
  assert.equal(r.feedback.length,2);assert.equal(r.feedback[0]!.change,'Revised');
  assert.throws(()=>r.save('absent','other','Unknown'));assert.throws(()=>r.save('objective','other','x'.repeat(2049)));
  r.remove('solvency','inappropriate_method');assert.equal(r.feedback.length,1);assert.ok(Object.isFrozen(r.design.nodes[0]));
});
test('review graph decomposes criteria and independent methods before aggregation',async()=>{
  const r=new EvaluationReview(polymerProposal()),s=r.scene(),g=await layoutGraph(s.nodes,s.edges);
  const a=g.nodes.find(n=>n.id==='solvency')!,b=g.nodes.find(n=>n.id==='viscosity')!,join=g.nodes.find(n=>n.id==='selection')!;
  assert.equal(a.y,b.y);assert.notEqual(a.x,b.x);assert.ok(join.y>a.y);
  assert.equal(s.nodes.find(n=>n.id==='synthesis')!.status,'method'); // Never an executed/failed status.
  assert.equal(r.design.nodes.find(n=>n.id==='selection')!.rule.includes('NOT specified'),true);
});
