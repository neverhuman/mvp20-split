import {test} from 'node:test';
import assert from 'node:assert/strict';
import {snapshot,detail,context,deferred} from '../../fixtures/observations.js';
import first from '../../fixtures/generation_comparison/first.json' with {type:'json'};
import {GenerationModel} from '../../../src/page_models/generation_comparison/model.js';
import {discover} from '../../../src/page_models/generation_comparison/discovery.js';
import type {ArtifactRef} from '../../../src/contracts/observations.js';
function setup(){
 const page=snapshot(),a=detail(1),b=detail(2),record=structuredClone(first);
 record.reference.scope=context.scope;record.checkpoint.specification.scope=context.scope;
 record.checkpoint.specification.evaluator.constraints.scope=context.scope;
 if(record.checkpoint.previous)record.checkpoint.previous.scope=context.scope;
 for(const o of record.checkpoint.observations){o.scope=context.scope;for(const e of o.outcome.evidence)e.scope=context.scope;}
 a.node=page.nodes[0]!;b.node=page.nodes[1]!;
 a.outputs=[{port:'checkpoint',kind:'artifact',item_count:1,missing_count:0,artifact:record.reference as ArtifactRef}];b.outputs=[];
 return {page,a,b,record,runtime:{snapshot:async()=>page,detail:async(_r:string,id:string)=>id===a.node.activation_id?a:b}};
}
test('discovery deduplicates exact artifacts while retaining source locations',async()=>{
 const f=setup();f.b.outputs=structuredClone(f.a.outputs);
 const result=await discover(context,f.runtime,new AbortController().signal);
 assert.equal(result.choices.length,1);assert.equal(result.choices[0]!.locations.length,2);assert.equal(result.incomplete,false);
});
test('collections are explicit incomplete coverage; wrong cut or node rejects discovery',async()=>{
 const f=setup();f.b.outputs=[{port:'batch',kind:'collection',item_count:3,missing_count:0,artifact:null}];
 assert.equal((await discover(context,f.runtime,new AbortController().signal)).incomplete,true);
 f.a.cut={...f.a.cut,revision:99};await assert.rejects(discover(context,f.runtime,new AbortController().signal));
 f.a.cut=f.page.snapshot.cut;f.a.node={...f.a.node,activation_id:'wrong'};await assert.rejects(discover(context,f.runtime,new AbortController().signal));
});
test('only selected discovered artifacts are read; denied content clears both panes',async()=>{
 const f=setup();let reads=0,deny=false;
 const model=new GenerationModel(context,f.runtime,{jsonArtifact:async()=>{reads++;if(deny)throw {kind:'denied'};return f.record.checkpoint;}});
 await model.refresh();assert.equal(reads,0);const key=model.snapshot.discovery!.choices[0]!.key;
 await model.select('left','invented');assert.equal(reads,0);
 await model.select('left',key);assert.equal(model.snapshot.left.phase,'ready');
 deny=true;await model.select('right',key);assert.equal(model.snapshot.phase,'denied');assert.equal(model.snapshot.left.value,null);assert.equal(model.snapshot.discovery,null);
});
test('refresh fences an uncancellable late content read',async()=>{
 const f=setup(),wait=deferred<unknown>(),model=new GenerationModel(context,f.runtime,{jsonArtifact:async()=>wait.promise});
 await model.refresh();const pending=model.select('left',model.snapshot.discovery!.choices[0]!.key);
 await model.refresh();wait.resolve(f.record.checkpoint);await pending;assert.equal(model.snapshot.left.value,null);
 model.dispose();await model.refresh();
});
test('failed selection clears its value while preserving an independent verified pane',async()=>{
 const f=setup();let failure=false;const model=new GenerationModel(context,f.runtime,{jsonArtifact:async()=>{if(failure)throw {kind:'network'};return f.record.checkpoint;}});
 await model.refresh();const key=model.snapshot.discovery!.choices[0]!.key;await model.select('left',key);
 failure=true;await model.select('right',key);assert.equal(model.snapshot.right.phase,'failed');assert.equal(model.snapshot.left.phase,'ready');assert.equal(model.comparison,null);
});
test('two-page discovery stops with explicit omitted-node scope',async()=>{
 const pages=[snapshot({ids:Array.from({length:50},(_,i)=>i+1),total:101,next:'second'}),snapshot({ids:Array.from({length:50},(_,i)=>i+51),total:101,next:'third'})];
 let reads=0,details=0;
 const result=await discover(context,{snapshot:async()=>pages[reads++]!,detail:async(_run,id)=>{details++;return detail(parseInt(id,16));}},new AbortController().signal);
 assert.equal(reads,2);assert.equal(details,100);assert.equal(result.incomplete,true);assert.equal(result.total,101);assert.equal(result.scanned,100);
});
