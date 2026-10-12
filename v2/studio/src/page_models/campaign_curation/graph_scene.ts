import type {ExecutableScopeV4} from '../../contracts/generated/authoring/save.js';
import type {SceneEdge,SceneNode} from '../scene.js';
import type {CurationGraphReview} from './graph_review.js';
import {sameValue} from './records.js';

type Node=ExecutableScopeV4['nodes'][number];
function nested(body:ExecutableScopeV4,path:readonly string[]){
  if(path.length>16)throw Error('curation_scope_depth');
  for(const id of path){
    const matches=body.nodes.filter(node=>node.node_id===id);
    if(matches.length!==1)return null;
    const node=matches[0]!;if(node.kind!=='scatter'&&node.kind!=='iterate')return null;body=node.body;
  }
  return body;
}
function inputs(node:Node):unknown[]{
  // Never descend into a child scope: those references have their own identity space.
  return Object.entries(node).filter(([key])=>key!=='body').map(([,value])=>value);
}
function links(body:ExecutableScopeV4):SceneEdge[]{
  const result:SceneEdge[]=(body.edges??[]).map((edge,index)=>({id:'control-'+index,source:edge.source,target:edge.target,label:edge.route??'next'}));
  for(const node of body.nodes){
    const pending=inputs(node);let index=0;
    while(pending.length){
      const value=pending.pop();if(!value||typeof value!=='object')continue;
      if(Array.isArray(value)){pending.push(...value);continue;}
      const item=value as Record<string,unknown>;
      if(item.kind==='output'&&typeof item.node_id==='string'&&typeof item.port==='string'){
        result.push({id:'data-'+node.node_id+'-'+index++,source:item.node_id,target:node.node_id,label:'data: '+item.port});
      }else pending.push(...Object.values(item));
    }
  }
  return result;
}
const label=(node:Node)=>node.kind==='invoke'?node.tool.capability_id+' · '+node.node_id:node.node_id;

/** Bounded one-scope projection of actual control edges and explicit data references. */
export function curationGraphScene(review:CurationGraphReview,side:'original'|'proposed',path:readonly string[]=[],offset=0){
  if(!Number.isSafeInteger(offset)||offset<0||offset%200!==0)throw Error('curation_graph_page');
  const before=nested(review.original.definition.body,path),after=nested(review.proposed.definition.body,path);
  const body=side==='original'?before:after,other=side==='original'?after:before;
  if(!body)return null;
  const ids=new Set(body.nodes.map(node=>node.node_id)),ambiguous=ids.size!==body.nodes.length;
  const page=body.nodes.slice(offset,offset+200),visible=new Set(page.map(node=>node.node_id));
  const allLinks=links(body),edges=ambiguous?[]:allLinks.filter(edge=>visible.has(edge.source)&&visible.has(edge.target));
  const nodes:SceneNode[]=page.map(node=>{const prior=other?.nodes.find(item=>item.node_id===node.node_id);
    const change=!prior?(side==='original'?'removed':'added'):sameValue(prior,node)?'unchanged':'changed';
    return {id:node.node_id,label:label(node),status:node.kind+' · '+change,x:0,y:0};});
  return {nodes:ambiguous?[]:nodes,edges,total:body.nodes.length,offset,omittedNodes:body.nodes.length-page.length,
    omittedEdges:allLinks.length-edges.length,ambiguous,
    choices:page.map(node=>({id:node.node_id,label:label(node),nested:node.kind==='scatter'||node.kind==='iterate'})),
    details:page};
}
