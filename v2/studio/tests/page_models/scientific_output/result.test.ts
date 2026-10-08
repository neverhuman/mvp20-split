import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {scientificResult,supported,ScientificOutputModel} from '../../../src/page_models/scientific_output/model.js';
import {scientificSchemas} from '../../../src/page_models/scientific_output/schemas.js';
import {DataProvenanceClient} from '../../../src/transport/provenance/data.js';
import type {ArtifactRef} from '../../../src/contracts/observations.js';
import {deferred} from '../../fixtures/observations.js';

const value={schema_version:'1',candidate_id:'fixture-A',scientific_status:'unvalidated_screen',
  input_parameters:{schema_version:'1',candidate_id:'fixture-A',parameter_context:'Explicit fixture',polymer:{dispersion:18,polar:8,hydrogen_bond:6},solvent:{dispersion:17,polar:6,hydrogen_bond:4},interaction_radius:4},
  distance_squared:12,distance:Math.sqrt(12),relative_energy_difference:Math.sqrt(12)/4,sphere_position:'inside',procedure:['Compute the declared screen.'],limitation:'Not measured compatibility.'};
const body=JSON.stringify(value);
const ref:ArtifactRef={scope:{tenant_id:'synthetic',project_id:'studio-spike'},artifact_id:'fixture-result',sha256:createHash('sha256').update(body).digest('hex'),size_bytes:Buffer.byteLength(body),media_type:'application/json',schema_ref:{schema_id:'materials.hansen-solvency.output',version:'1',sha256:scientificSchemas['materials.hansen-solvency.output'].sha256}};
test('published tool schema hashes match the reviewed public snapshots',()=>{
  for(const [name,folder] of [['materials.hansen-solvency.output','hansen_solvency'],['materials.arrhenius-viscosity.output','arrhenius_viscosity']] as const){
    const raw=readFileSync(`src/page_models/scientific_output/schemas/${folder.replaceAll('_','-')}.json`);
    assert.equal(createHash('sha256').update(raw).digest('hex'),scientificSchemas[name].sha256);
    assert.deepEqual(JSON.parse(raw.toString()),scientificSchemas[name].schema);
  }
});
test('scientific quantities require exact schema and consistent candidate identity',()=>{
  const result=scientificResult(ref,value);assert.equal(result.candidate,'fixture-A');assert.equal(result.quantities[2]!.value,Math.sqrt(12)/4);
  assert.throws(()=>scientificResult(ref,{...value,candidate_id:'another'}));assert.throws(()=>scientificResult(ref,{...value,scientific_status:'proven'}));
  assert.equal(supported({...ref,schema_ref:{...ref.schema_ref,sha256:'a'.repeat(64)}}),false);
});
test('content transport checks metadata, byte identity and current permission',async()=>{
  for(const condition of ['valid','tampered','denied'] as const){
    const client=new DataProvenanceClient(async path=>String(path).endsWith('/content')?new Response(condition==='tampered'?body.replace('inside','outsid'):body,{status:condition==='denied'?403:200,headers:{'Content-Type':'application/json'}}):Response.json(ref));
    if(condition==='valid')assert.deepEqual(await client.jsonArtifact(ref,new AbortController().signal),value);
    else await assert.rejects(client.jsonArtifact(ref,new AbortController().signal));
  }
});
test('late reads cannot resurrect a hidden scientific result; denial clears it',async()=>{
  const pending=deferred<unknown>();let mode='pending';
  const model=new ScientificOutputModel({jsonArtifact:async()=>{if(mode==='denied')throw {kind:'denied'};return mode==='valid'?value:pending.promise;}});
  const loading=model.read(ref);await model.read(null);pending.resolve(value);await loading;assert.equal(model.snapshot.result,null);
  mode='valid';await model.read(ref);assert.equal(model.snapshot.phase,'ready');mode='denied';await model.read(ref);assert.equal(model.snapshot.phase,'denied');assert.equal(model.snapshot.result,null);model.dispose();
});
