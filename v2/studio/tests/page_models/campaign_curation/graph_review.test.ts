import test from 'node:test';
import assert from 'node:assert/strict';
import {CurationGraphReader,CurationGraphReview} from '../../../src/page_models/campaign_curation/graph_review.js';
import {curationGraphScene} from '../../../src/page_models/campaign_curation/graph_scene.js';
import {RecordedCuration} from '../../../src/page_models/campaign_curation/records.js';
import {DraftComparison} from '../../../src/page_models/design/draft_comparison.js';
import {graphFixture} from './graph_fixture.js';

test('exact original/proposed/validation reads preserve campaign identity changes',async()=>{
  const f=graphFixture(),calls:string[]=[];
  const reader=new CurationGraphReader({draft:async(id,rev)=>{calls.push(id+':'+rev);return id===f.original.head.draft_id?f.original:f.saved;},validation:async id=>{calls.push(id);return f.validation;}});
  const review=(await reader.read(f.record,new AbortController().signal))!;
  assert.deepEqual(calls,[f.original.head.draft_id+':1','proposed-draft:1','validation']);
  assert.ok(review.comparison.snapshot.changes.some(row=>row.path==='/definition/campaign_id'));
  assert.throws(()=>new DraftComparison({title:f.original.head.title,definition:f.original.definition},f.proposed),/context_mismatch/);
  assert.equal(review.validation?.plan_sha256,'f'.repeat(64));
});
test('foreign revisions, altered model graph or changed validation pins cannot enable review',()=>{
  for(const variant of ['original','saved','definition','validation','scope']){
    const f=graphFixture();
    if(variant==='original')f.original.head.revision=2;
    if(variant==='saved')f.saved.head.content_sha256='0'.repeat(64);
    if(variant==='definition')f.saved.definition.body.nodes[0]!.node_id='replacement';
    if(variant==='validation')f.validation.universe_sha256='0'.repeat(64);
    if(variant==='scope')f.validation.scope={...f.scope,project_id:'other'};
    assert.throws(()=>new CurationGraphReview(f.record,f.original,f.saved,f.validation),/binding/);
  }
});
test('uncompiled proposal stays inspectable without a saved or validated claim',async()=>{
  const f=graphFixture();f.curation.receipt.phase='compiling';f.curation.validated_draft=null;
  const record=new RecordedCuration(f.curation,f.selection);
  const reader=new CurationGraphReader({draft:async()=>f.original,validation:async()=>{throw Error('unexpected validation');}});
  const review=(await reader.read(record,new AbortController().signal))!;
  assert.equal(review.saved,null);assert.equal(review.validation,null);
});
test('graph preview projects real control and data links with explicit missing scope',()=>{
  const f=graphFixture(),review=new CurationGraphReview(f.record,f.original,f.saved,f.validation);
  const scene=curationGraphScene(review,'proposed')!;
  assert.equal(scene.nodes.length,2);assert.equal(scene.edges.length,2);
  assert.deepEqual(new Set(scene.edges.map(edge=>edge.label)),new Set(['next','data: material']));
  assert.match(scene.nodes[0]!.label,/synthetic.heat/);assert.match(scene.nodes[0]!.status,/added/);
  assert.equal(curationGraphScene(review,'original',['missing']),null);
});
test('cancelled source cannot publish a graph readback',async()=>{
  const f=graphFixture(),controller=new AbortController();
  const reader=new CurationGraphReader({draft:async()=>{controller.abort();return f.original;},validation:async()=>f.validation});
  await assert.rejects(()=>reader.read(f.record,controller.signal),/aborted/);
});

test('large graph pages disclose omitted nodes and cross-page connections',()=>{
  const f=graphFixture();
  f.proposed.definition.body={nodes:Array.from({length:205},(_,i)=>({kind:'finish',node_id:'n'+i,outputs:[]})),
    edges:[{source:'n0',target:'n204',route:'next'}]};
  f.curation.proposal!.outcome={kind:'propose_campaign',candidate:{kind:'future_campaign',...f.proposed,expected_evidence:[]},gaps:[]};
  f.curation.validated_draft=null;f.curation.receipt.phase='compiling';
  const review=new CurationGraphReview(new RecordedCuration(f.curation,f.selection),f.original,null,null);
  const first=curationGraphScene(review,'proposed')!,last=curationGraphScene(review,'proposed',[],200)!;
  assert.equal(first.nodes.length,200);assert.equal(first.omittedNodes,5);assert.equal(first.omittedEdges,1);
  assert.equal(last.nodes.length,5);assert.equal(last.omittedNodes,200);assert.equal(last.omittedEdges,1);
  assert.throws(()=>curationGraphScene(review,'proposed',[],1),/page/);
});

test('nested scopes preserve their own identities and duplicate identities suppress the canvas',()=>{
  const f=graphFixture();
  f.proposed.definition.body.nodes.push({kind:'iterate',node_id:'loop',body:{nodes:[{kind:'finish',node_id:'done',outputs:[]}]},
    captures:[],state:[{name:'value',value_type:{kind:'scalar',scalar:'number'},initial:{kind:'number',value:0},feedback_port:'value'}],
    max_iterations:2,on_limit:'finish',until:{kind:'constant',value:true}});
  f.curation.proposal!.outcome={kind:'propose_campaign',candidate:{kind:'future_campaign',...f.proposed,expected_evidence:[]},gaps:[]};
  f.curation.validated_draft=null;f.curation.receipt.phase='compiling';
  const review=()=>new CurationGraphReview(new RecordedCuration(f.curation,f.selection),f.original,null,null);
  const nested=curationGraphScene(review(),'proposed',['loop'])!;
  assert.equal(nested.total,1);assert.deepEqual(nested.edges,[]);assert.equal(nested.nodes[0]!.id,'done');
  assert.equal(curationGraphScene(review(),'original',['loop']),null);
  f.proposed.definition.body.nodes.push(structuredClone(f.proposed.definition.body.nodes[0]!));
  const ambiguous=curationGraphScene(review(),'proposed')!;
  assert.equal(ambiguous.ambiguous,true);assert.deepEqual(ambiguous.nodes,[]);assert.deepEqual(ambiguous.edges,[]);
});
