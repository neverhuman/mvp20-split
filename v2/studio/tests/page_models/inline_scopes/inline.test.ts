import {test} from 'node:test';
import assert from 'node:assert/strict';
import {snapshot,id} from '../../fixtures/observations.js';
import {topology} from '../../fixtures/navigation.js';
import {InlineScopes} from '../../../src/page_models/inline_scopes/model.js';
import {inlineScene} from '../../../src/page_models/inline_scopes/projection.js';
import {layoutGraph,fitGeometry} from '../../../src/page_models/graph_layout/layout.js';
import {ReadFailure} from '../../../src/transport/failure.js';
import type {GraphTopologyPage,GraphScopePage} from '../../../src/contracts/observations.js';

function fixture(count=2,kind:'scatter'|'iterate'='scatter') {
  const root=topology(),parent=root.nodes[0]!;
  parent.activation.kind=kind;parent.child_scope_count=count;
  const pages=Array.from({length:count},(_,i)=>{
    const page=topology();
    page.graph_scope={...page.graph_scope,scope_key:id(110+i),parent_activation_id:parent.activation.activation_id,
      occurrences:[kind==='scatter'?{kind:'scatter',node_id:parent.activation.path.node_id,index:i,membership_sha256:id(900)}:{kind:'loop',node_id:parent.activation.path.node_id,index:i}],definition_path:[parent.activation.path.node_id]};
    page.nodes.forEach((n,j)=>{n.activation.activation_id=id(200+i*10+j);n.activation.path={...n.activation.path,occurrences:page.graph_scope.occurrences};n.activation.kind=j?'finish':'invoke';n.activation.status=i?'issued':'succeeded';});
    page.edges=[{source:page.nodes[0]!.activation.activation_id,target:page.nodes[1]!.activation.activation_id,route:'next'}];return page;
  });
  const groups:GraphScopePage={schema_version:'1',cut:root.cut,parent_activation_id:parent.activation.activation_id,scope_count:count,scopes:pages.map(p=>p.graph_scope),next_cursor:null};
  return {root,parent,pages,groups};
}
test('parallel siblings share one cut and render side-by-side with a derived rejoin',async()=>{
  const f=fixture(),calls:string[]=[];
  const model=new InlineScopes({scopes:async()=>f.groups,topology:async(run,scope,token)=>{
    assert.equal(token,snapshot().snapshot.snapshot_token);calls.push(scope);return f.pages.find(p=>p.graph_scope.scope_key===scope)!;
  }},()=>assert.fail());model.bind(snapshot().snapshot);await model.expand(f.parent);
  assert.equal(calls.length,2);
  const scene=inlineScene(f.root,model.snapshot),layout=await layoutGraph(scene.nodes,scene.edges);
  assert.equal(scene.nodes.length,7);assert.equal(scene.records.length,6);
  const a=layout.nodes.find(n=>n.id===f.pages[0]!.nodes[0]!.activation.activation_id)!;
  const b=layout.nodes.find(n=>n.id===f.pages[1]!.nodes[0]!.activation.activation_id)!;
  assert.equal(a.y,b.y);assert.notEqual(a.x,b.x);
  assert.equal(a.status,'succeeded');assert.equal(b.status,'issued');
  assert.ok(scene.edges.some(e=>e.target.startsWith('@scope-end:')&&e.label==='scope-boundary'));
  assert.equal(scene.edges.filter(e=>!e.label).length,2);
});
test('bounded expansion discloses omitted siblings and never supplies their outcomes',async()=>{
  const f=fixture(7);let reads=0;
  const model=new InlineScopes({scopes:async()=>f.groups,topology:async(_,scope)=>{reads++;return f.pages.find(p=>p.graph_scope.scope_key===scope)!;}},()=>assert.fail());
  model.bind(snapshot().snapshot);await model.expand(f.parent);
  assert.equal(reads,4);assert.match(inlineScene(f.root,model.snapshot).notes.join(' '),/4 of 7.*3 omitted/);
});
test('iterations connect in order rather than imply sibling parallelism',()=>{
  const f=fixture(2,'iterate');const scene=inlineScene(f.root,{[f.parent.activation.activation_id]:{phase:'ready',total:2,pages:f.pages,error:null}});
  assert.ok(scene.edges.some(e=>e.source===f.pages[0]!.nodes[1]!.activation.activation_id&&e.target===f.pages[1]!.nodes[0]!.activation.activation_id));
  assert.ok(!scene.edges.some(e=>e.source===f.parent.activation.activation_id&&e.target===f.pages[1]!.nodes[0]!.activation.activation_id));
});
test('denial clears every expanded group and reports loss of authority',async()=>{
  const f=fixture();let denied=false,error='';
  const model=new InlineScopes({scopes:async()=>{if(denied)throw new ReadFailure('denied');return f.groups;},topology:async(_,scope)=>f.pages.find(p=>p.graph_scope.scope_key===scope)!},e=>{error=e.kind;});
  model.bind(snapshot().snapshot);await model.expand(f.parent);denied=true;await model.expand(f.parent);
  assert.equal(error,'denied');assert.deepEqual(model.snapshot,{});
});
test('late sibling reads cannot resurrect hidden or replaced observations',async()=>{
  const f=fixture();let finish!:(page:GraphScopePage)=>void;
  const model=new InlineScopes({scopes:()=>new Promise(resolve=>{finish=resolve;}),topology:async()=>{assert.fail('Cancelled scope must not read children');}},()=>assert.fail());
  model.bind(snapshot().snapshot);const pending=model.expand(f.parent);model.bind(null);finish(f.groups);await pending;
  assert.deepEqual(model.snapshot,{});
});
test('wrong cut, parent and occurrence identity fail closed',async()=>{
  for(const fault of ['cut','parent','occurrence']) {
    const f=fixture();let error='';
    if(fault==='cut')f.groups.cut={...f.groups.cut,revision:f.groups.cut.revision+1};
    if(fault==='parent')f.groups.scopes[0]!.parent_activation_id=id(999);
    if(fault==='occurrence')f.pages[0]!.graph_scope.occurrences[0]!.node_id='foreign';
    const model=new InlineScopes({scopes:async()=>f.groups,topology:async(_,scope)=>f.pages.find(p=>p.graph_scope.scope_key===scope)!},e=>{error=e.kind;});
    model.bind(snapshot().snapshot);await model.expand(f.parent);
    assert.ok(error==='resnapshot'||model.snapshot[f.parent.activation.activation_id]?.phase==='failed');
  }
});

test('refresh restores chosen expansions; explicit collapse stays collapsed; replacement clears choices',async()=>{
  const f=fixture();let reads=0;
  const model=new InlineScopes({scopes:async()=>{reads++;return f.groups;},topology:async(_,scope)=>f.pages.find(p=>p.graph_scope.scope_key===scope)!},()=>assert.fail());
  const anchor=snapshot().snapshot;model.bind(anchor);await model.expand(f.parent);
  model.bind(null);model.bind(anchor);model.restore(f.root.nodes,false);await new Promise(resolve=>setImmediate(resolve));
  assert.equal(reads,2);assert.equal(model.snapshot[f.parent.activation.activation_id]?.phase,'ready');
  model.collapse(f.parent.activation.activation_id);model.restore(f.root.nodes,true);await new Promise(resolve=>setImmediate(resolve));assert.equal(reads,2);
  model.reset();model.bind(anchor);model.restore(f.root.nodes,false);await new Promise(resolve=>setImmediate(resolve));assert.equal(reads,2);
});

test('failed and waiting branches preserve exact states rather than turning them into successes',()=>{
  const f=fixture();f.parent.activation.status='blocked';f.pages[1]!.nodes[0]!.activation.status='failed';f.pages[1]!.nodes[1]!.activation.status='waiting';
  const scene=inlineScene(f.root,{[f.parent.activation.activation_id]:{phase:'ready',total:2,pages:f.pages,error:null}});
  assert.equal(scene.nodes.find(n=>n.id===f.pages[0]!.nodes[0]!.activation.activation_id)?.status,'succeeded');
  assert.equal(scene.nodes.find(n=>n.id===f.pages[1]!.nodes[0]!.activation.activation_id)?.status,'failed');
  assert.equal(scene.nodes.find(n=>n.id===f.pages[1]!.nodes[1]!.activation.activation_id)?.status,'waiting');
  assert.equal(scene.nodes.find(n=>n.id.startsWith('@scope-end:'))?.status,'blocked');
});

test('focus uses only selected geometry and remains readable independently of the whole campaign',async()=>{
  const f=fixture();const scene=inlineScene(f.root,{[f.parent.activation.activation_id]:{phase:'ready',total:2,pages:f.pages,error:null}});
  const geometry=await layoutGraph(scene.nodes,scene.edges),ids=f.pages.flatMap(p=>p.nodes.map(n=>n.activation.activation_id));
  const fit=fitGeometry(geometry,1000,700,ids)!;assert.equal(fit.zoom,1);
  for(const n of geometry.nodes.filter(n=>ids.includes(n.id))) {
    assert.ok(n.x*fit.zoom+fit.x>=0);assert.ok((n.x+208)*fit.zoom+fit.x<=1000);
    assert.ok(n.y*fit.zoom+fit.y>=0);assert.ok((n.y+72)*fit.zoom+fit.y<=700);
  }
  assert.equal(fitGeometry(geometry,0,700),null);assert.equal(fitGeometry(geometry,1000,700,['missing']),null);
});
