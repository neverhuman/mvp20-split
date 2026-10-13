import test from 'node:test';
import assert from 'node:assert/strict';
import {CurationArtifactInputs} from '../../../src/page_models/campaign_curation/artifact_inputs.js';
import type {ArtifactRef} from '../../../src/contracts/observations.js';
import {local,scope} from '../../fixtures/authoring.js';

export const artifact=(id='parameters'):ArtifactRef=>({scope,artifact_id:id,sha256:'a'.repeat(64),
  schema_ref:{schema_id:'synthetic',version:'1',sha256:'d'.repeat(64)},media_type:'application/json',size_bytes:10});
const literal=(ref=artifact())=>({kind:'artifact' as const,artifact:ref,representation:'parameters',unit:'1'});
const invoke=(ref=artifact())=>({kind:'invoke' as const,node_id:'evaluate',inputs:[{port:'parameters',source:literal(ref)}],
  checkpoint:literal(artifact('checkpoint')),timeout_seconds:60,
  tool:{capability_id:'synthetic.evaluate',contract_version:'1' as const,release:'1.0.0',image_sha256:'b'.repeat(64)}});

test('nested declared input and checkpoint pins are deduplicated, sorted and immutable',()=>{
  const graph=local().definition, ref=artifact();
  graph.body.nodes.unshift({kind:'iterate',node_id:'loop',body:{nodes:[invoke(ref)]},
    captures:[],state:[],max_iterations:2,on_limit:'finish',until:{kind:'constant',value:true}});
  const pins=CurationArtifactInputs.collect(graph,[ref]);
  assert.deepEqual(pins.map(pin=>pin.artifact_id),['checkpoint','parameters']);
  ref.sha256='c'.repeat(64);assert.equal(pins[1]!.sha256,'a'.repeat(64));
  assert.throws(()=>pins.push(artifact('new')));
});

test('finish-only artifacts and runtime output references are not invented input evidence',()=>{
  const graph=local().definition;
  const node=invoke();const {checkpoint,...plain}=node;
  graph.body.nodes=[{kind:'finish',node_id:'done',outputs:[{port:'context',source:literal()}]},
    {...plain,inputs:[{port:'parameters',source:{kind:'output',node_id:'upstream',port:'result'}}]}];
  assert.deepEqual(CurationArtifactInputs.collect(graph),[]);
});

test('foreign scopes, conflicting pins, excess context and excessive nesting fail closed',()=>{
  const graph=local().definition;
  assert.throws(()=>CurationArtifactInputs.collect(graph,[{...artifact(),scope:{...scope,project_id:'foreign'}}]),/scope/);
  assert.throws(()=>CurationArtifactInputs.collect(graph,[artifact(),{...artifact(),sha256:'b'.repeat(64)}]),/conflict/);
  assert.throws(()=>CurationArtifactInputs.collect(graph,Array.from({length:17},(_,i)=>artifact('a'+i))),/limit/);
  let body=graph.body;
  for(let i=0;i<18;i++){
    const child={nodes:[]};body.nodes.push({kind:'iterate',node_id:'loop'+i,body:child,
      state:[],max_iterations:2,on_limit:'finish',until:{kind:'constant',value:true}});body=child;
  }
  assert.throws(()=>CurationArtifactInputs.collect(graph),/graph_limit/);
});
