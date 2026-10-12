import {test} from 'node:test';
import assert from 'node:assert/strict';
import first from '../../fixtures/generation_comparison/first.json' with {type:'json'};
import second from '../../fixtures/generation_comparison/second.json' with {type:'json'};
import {RetainedGeneration,GenerationComparison} from '../../../src/page_models/generation_comparison/checkpoint.js';
import type {ArtifactRef} from '../../../src/contracts/observations.js';
const read=(f:{reference:unknown;checkpoint:unknown}=first)=>new RetainedGeneration(f.reference as ArtifactRef,f.checkpoint);
test('tool-produced generations retain objectives, candidate ancestry and synthetic quality',()=>{
 const a=read(),b=read(second),c=new GenerationComparison(a,b);
 assert.equal(a.record.generation,0);assert.equal(b.record.generation,1);assert.equal(c.compatible,true);
 assert.equal(a.evaluated,a.record.population.length);assert.ok(b.candidates.some(r=>r.parents.length));
 assert.ok(a.candidates.every(r=>r.quality==='synthetic'));assert.equal(a.objectives[0]!.direction,'minimize');
 assert.equal(c.improvement('cost'),a.objectives[0]!.best!-b.objectives[0]!.best!);
});
test('same generation, changed specification and incomplete stage do not yield improvement',()=>{
 assert.equal(new GenerationComparison(read(),read()).improvement('cost'),null);
 const f=structuredClone(second);f.checkpoint.specification.seed='a'.repeat(64);
 assert.equal(new GenerationComparison(read(),read(f)).compatible,false);
 const g=structuredClone(second);g.checkpoint.phase='awaiting_evaluations';
 assert.equal(new GenerationComparison(read(),read(g)).improvement('cost'),null);
});
test('unknown values stay unknown rather than zero',()=>{
 const f=structuredClone(first) as any;
 for(const o of f.checkpoint.observations)o.outcome={status:'unknown',reason_code:'missing',evidence:[]};
 const a=read(f);assert.equal(a.objectives[0]!.best,null);assert.equal(a.evaluated,0);assert.equal(a.unresolved,a.record.population.length);
 assert.equal(new GenerationComparison(a,read(second)).improvement('cost'),null);
});
test('constraint violations exclude a result from feasible objective extrema',()=>{
 const f=structuredClone(first);for(const o of f.checkpoint.observations)o.outcome.constraint_violation=1;
 assert.equal(read(f).objectives[0]!.best,null);
});
test('foreign scopes, duplicate identities, wrong units, evaluator and missing candidates are rejected',()=>{
 for(const mutate of [
  (f:any)=>f.reference.scope.project_id='other',
  (f:any)=>f.checkpoint.attempts.push(f.checkpoint.attempts[0]),
  (f:any)=>f.checkpoint.observations[0].outcome.objectives[0].unit='wrong',
  (f:any)=>f.checkpoint.observations[0].outcome.evaluator.release='wrong',
  (f:any)=>f.checkpoint.population.push('a'.repeat(64)),
  (f:any)=>f.reference.schema_ref.sha256='a'.repeat(64),
 ]){const f=structuredClone(first);mutate(f);assert.throws(()=>read(f));}
});
test('caller mutations do not change the retained projection',()=>{
 const f=structuredClone(first),a=read(f);f.checkpoint.generation=99;assert.equal(a.record.generation,0);
});
test('maximize preserves direction and never treats an absent objective as zero',()=>{
 const f=structuredClone(first),g=structuredClone(second);
 f.checkpoint.specification.objectives[0]!.direction='maximize';g.checkpoint.specification.objectives[0]!.direction='maximize';
 const a=read(f),b=read(g),comparison=new GenerationComparison(a,b);
 assert.equal(comparison.improvement('cost'),b.objectives[0]!.best!-a.objectives[0]!.best!);
 assert.equal(comparison.improvement('absent'),null);
});
