import {parseDesign,type EvaluationDesign} from '../evaluation_review/model.js';
import type {ArtifactRef} from '../../contracts/observations.js';
import type {RunContext} from '../graph_window.js';
import {contextSchema} from './schema_pin.js';
export type MethodBinding=Readonly<{method_id:string;node_id:string;candidate_id:string;tool:Readonly<Record<string,unknown>>}>;
export type CampaignContext=Readonly<{design:EvaluationDesign;bindings:readonly MethodBinding[];limitations:readonly string[];reference:ArtifactRef}>;
const equal=(a:unknown,b:unknown)=>JSON.stringify(a)===JSON.stringify(b);
function object(value:unknown):Record<string,unknown>{if(!value||typeof value!=='object'||Array.isArray(value))throw Error('Invalid campaign context');return value as Record<string,unknown>;}
function keys(value:Record<string,unknown>,names:string[]){if(Object.keys(value).sort().join()!==names.sort().join())throw Error('Unexpected campaign context fields');}
function identifier(value:unknown):string{if(typeof value!=='string'||!value.length||value.length>128)throw Error('Invalid identity');return value;}
export function isCampaignContext(reference:ArtifactRef){const s=reference.schema_ref;return s.schema_id===contextSchema.schema_id&&s.version===contextSchema.version&&s.sha256===contextSchema.sha256;}
export function readCampaignContext(raw:unknown,reference:ArtifactRef,run:RunContext):CampaignContext {
 if(!isCampaignContext(reference)||reference.scope.tenant_id!==run.scope.tenant_id||reference.scope.project_id!==run.scope.project_id)throw Error('Wrong campaign context');
 const d=object(raw);keys(d,['format','scope','design','bindings','limitations']);
 const scope=object(d.scope);if(d.format!=='amphora.demo-campaign-context.v1'||scope.tenant_id!==run.scope.tenant_id||scope.project_id!==run.scope.project_id)throw Error('Context scope mismatch');
 const design=parseDesign(JSON.stringify(d.design));
 if(!Array.isArray(d.bindings)||!d.bindings.length||d.bindings.length>32||!Array.isArray(d.limitations)||d.limitations.length>16)throw Error('Context bounds exceeded');
 const bindings=d.bindings.map(value=>{const b=object(value);keys(b,['method_id','node_id','candidate_id','tool']);const method_id=identifier(b.method_id);
  if(!design.nodes.some(n=>n.id===method_id&&n.kind==='method'))throw Error('Missing planned method');
  const tool=object(b.tool);keys(tool,['capability_id','contract_version','image_sha256','release']);
  for(const key of ['capability_id','contract_version','release'])identifier(tool[key]);
  if(typeof tool.image_sha256!=='string'||!/^[a-f0-9]{64}$/.test(tool.image_sha256))throw Error('Invalid declared tool image');
  return Object.freeze({method_id,node_id:identifier(b.node_id),candidate_id:identifier(b.candidate_id),tool:Object.freeze({...tool})});});
 if(new Set(bindings.map(b=>b.node_id)).size!==bindings.length)throw Error('Duplicate execution binding');
 const limitations=d.limitations.map(s=>{if(typeof s!=='string'||s.length>2048)throw Error('Invalid limitation');return s;});
 return Object.freeze({design,bindings:Object.freeze(bindings),limitations:Object.freeze(limitations),reference:structuredClone(reference)});
}
