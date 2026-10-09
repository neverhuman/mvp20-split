import {ExploreContext, immutable, type ExplorePins} from '../explore/context.js';
import type {EvaluationDesign} from '../evaluation_review/model.js';

export type KnowledgeMethodLink=Readonly<{method_id:string;entity_ids:readonly string[]}>;

/** Retained planning association; never an assertion that an evaluator consumed a claim. */
export class CampaignKnowledge {
 readonly pins:ExplorePins;
 readonly methods:readonly KnowledgeMethodLink[];
 readonly role='planning_context' as const;
 constructor(raw:unknown,scope:object,design:EvaluationDesign){
  const value=record(raw);
  exact(value,['role','revision','methods']);
  if(value.role!=='planning_context')throw Error('Unsupported Knowledge association');
  const context=new ExploreContext({graph:value.revision as ExplorePins['graph'],experiment:null,observations:[]});
  context.scope(scope);
  if(!Array.isArray(value.methods)||!value.methods.length||value.methods.length>32)throw Error('Invalid Knowledge method bounds');
  const methods=value.methods.map(raw=>{
   const link=record(raw);exact(link,['method_id','entity_ids']);
   if(typeof link.method_id!=='string'||!design.nodes.some(n=>n.id===link.method_id&&n.kind==='method'))throw Error('Unknown Knowledge method');
   if(!Array.isArray(link.entity_ids)||!link.entity_ids.length||link.entity_ids.length>32||link.entity_ids.some(id=>typeof id!=='string'||!id.length||id.length>128)||new Set(link.entity_ids).size!==link.entity_ids.length)throw Error('Invalid Knowledge entity links');
   return {method_id:link.method_id,entity_ids:link.entity_ids as string[]};
  });
  if(new Set(methods.map(m=>m.method_id)).size!==methods.length)throw Error('Duplicate Knowledge method');
  this.pins=context.pins;this.methods=immutable(methods);Object.freeze(this);
 }
 entities(method:string):readonly string[]{return this.methods.find(m=>m.method_id===method)?.entity_ids??[];}
}
function record(value:unknown):Record<string,unknown>{if(!value||typeof value!=='object'||Array.isArray(value))throw Error('Invalid Knowledge association');return value as Record<string,unknown>;}
function exact(value:Record<string,unknown>,keys:string[]){if(Object.keys(value).sort().join()!==keys.sort().join())throw Error('Unexpected Knowledge association fields');}
