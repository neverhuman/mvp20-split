import type { GraphTopologyPage } from '../../contracts/observations.js';
import type { SceneNode, SceneEdge } from '../scene.js';
import type { InlineGroup } from './model.js';

/** Solid edges are owner control links; dashed edges explain nested scope boundaries. */
export function inlineScene(root:GraphTopologyPage, groups:Readonly<Record<string,InlineGroup>>) {
  const nodes:SceneNode[]=[],edges:SceneEdge[]=[],annotations:Record<string,string>={},owners:Record<string,string>={};
  const records:GraphTopologyPage['nodes']=[];const notes:string[]=[];let budget=200;
  function scope(page:GraphTopologyPage,depth:number) {
    const available=page.nodes.slice(0,Math.max(0,budget));budget-=available.length;
    const ids=new Set(available.map(n=>n.activation.activation_id));
    const occurrence=page.graph_scope.occurrences.at(-1);
    const context=occurrence ? `${occurrence.kind==='scatter'?'Branch':'Iteration'} ${occurrence.index+1}` : '';
    const outgoing=new Map<string,string>();
    for(const record of available) {
      const n=record.activation;records.push(record);owners[n.activation_id]=n.activation_id;
      nodes.push({id:n.activation_id,label:n.path.node_id,status:n.status,x:0,y:0});
      annotations[n.activation_id]=[context,record.child_scope_count ? `${record.child_scope_count} ${n.kind==='scatter'?'parallel branches':'iterations'}` : n.kind==='invoke'?'Tool invocation':n.kind.replaceAll('_',' ')].filter(Boolean).join(' / ');
      const group=groups[n.activation_id];
      if(group?.phase==='loading') notes.push(`${n.path.node_id}: loading siblings`);
      if(group?.phase==='failed') notes.push(`${n.path.node_id}: expansion unavailable (${group.error})`);
      if(group?.phase!=='ready' || !group.pages.length) continue;
      if(depth>=3) {notes.push(`${n.path.node_id}: deeper nesting requires isolated scope navigation`);continue;}
      const children=[...group.pages].sort((a,b)=>a.graph_scope.occurrences.at(-1)!.index-b.graph_scope.occurrences.at(-1)!.index);
      const need=children.reduce((sum,p)=>sum+p.nodes.length,0)+1;
      if(need>budget) {notes.push(`${n.path.node_id}: expansion exceeds the 200-node view limit`);continue;}
      const join='@scope-end:'+n.activation_id;
      budget--;owners[join]=n.activation_id;
      nodes.push({id:join,label:n.kind==='scatter'?'Rejoin branches':'Iteration group end',status:n.status,x:0,y:0});
      annotations[join]=`Group boundary / ${n.path.node_id}`;
      let previous:string[]=[n.activation_id];
      let loaded=0;
      for(const child of children) {
        const ends=scope(child,depth+1);loaded++;
        for(const source of n.kind==='scatter'?[n.activation_id]:previous)
          for(const target of ends.entries) edges.push({id:`nested:${source}:${target}`,source,target,label:'scope-boundary'});
        if(n.kind==='scatter') for(const source of ends.exits) edges.push({id:`nested:${source}:${join}`,source,target:join,label:'scope-boundary'});
        else previous=ends.exits;
      }
      if(n.kind==='iterate') for(const source of previous) edges.push({id:`nested:${source}:${join}`,source,target:join,label:'scope-boundary'});
      outgoing.set(n.activation_id,join);
      if(loaded<group.total) notes.push(`${n.path.node_id}: ${loaded} of ${group.total} siblings shown; ${group.total-loaded} omitted`);
      annotations[n.activation_id]=`${context ? context+' / ' : ''}${loaded}/${group.total} ${n.kind==='scatter'?'parallel branches':'sequential iterations'} shown`;
    }
    for(const edge of page.edges) if(ids.has(edge.source)&&ids.has(edge.target)) {
      const source=outgoing.get(edge.source)??edge.source;
      edges.push({id:`control:${edge.source}:${edge.route}:${edge.target}`,source,target:edge.target,
        ...(outgoing.has(edge.source)?{label:'scope-boundary'}:{})});
    }
    if(available.length<page.node_count) notes.push(`${context||'Root'}: ${available.length}/${page.node_count} nodes loaded; continuation may be incomplete`);
    return {entries:available.filter(n=>!page.edges.some(e=>e.target===n.activation.activation_id)).map(n=>n.activation.activation_id),
      exits:available.filter(n=>n.activation.kind==='finish').map(n=>outgoing.get(n.activation.activation_id)??n.activation.activation_id)};
  }
  scope(root,0);
  return {nodes,edges,annotations,owners,records,notes};
}
