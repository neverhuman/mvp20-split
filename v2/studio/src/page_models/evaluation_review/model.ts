import type { SceneNode, SceneEdge } from '../scene.js';

export type ReviewStep = Readonly<{
  id:string; title:string; kind:'objective'|'criterion'|'method'|'selection'|'iteration';
  rationale:string; method:string; procedure:readonly string[]; inputs:readonly string[]; outputs:readonly string[];
  applicability:string; assumptions:readonly string[]; rule:string;
  evidence:string; availability:string; alternatives:readonly string[]; sources:readonly string[];
}>;
export type EvaluationDesign = Readonly<{
  format:'amphora.evaluation-review.v1'; id:string; revision:number; title:string;
  provenance:Readonly<{author:string; origin:'design_proposal'; description:string}>;
  nodes:readonly ReviewStep[]; edges:readonly {source:string;target:string;relationship:string}[];
}>;
export const concerns=['inappropriate_method','unsupported_assumption','missing_criterion','misleading_aggregation','other'] as const;
export type Concern = typeof concerns[number];
export type ReviewNote = Readonly<{node:string;concern:Concern;change:string}>;
const obj=(x:unknown):Record<string,unknown>=>{if(!x||typeof x!=='object'||Array.isArray(x))throw Error('Expected an object');return x as Record<string,unknown>;};
function exact(x:Record<string,unknown>,keys:readonly string[]) {if(Object.keys(x).length!==keys.length||keys.some(k=>!(k in x)))throw Error('Unexpected or missing fields');}
function str(x:unknown,max=4096):string {if(typeof x!=='string'||!x.trim()||x.length>max)throw Error('Missing or oversized text');return x;}
function list(x:unknown,max=32):string[] {if(!Array.isArray(x)||x.length>max)throw Error('Invalid list');return x.map(v=>str(v));}
function id(x:unknown):string {const s=str(x,96);if(!/^[a-zA-Z0-9_.-]+$/.test(s))throw Error('Invalid identifier');return s;}
function freeze<T>(value:T):T {if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;}
/** Local design boundary. No executable graph, provider attestation or scientific verdict. */
export function parseDesign(raw:string):EvaluationDesign {
  if(new TextEncoder().encode(raw).length>262144)throw Error('Review document exceeds 256 KiB');
  const d=obj(JSON.parse(raw));exact(d,['format','id','revision','title','provenance','nodes','edges']);
  if(d.format!=='amphora.evaluation-review.v1'||!Number.isSafeInteger(d.revision)||(d.revision as number)<1)throw Error('Unsupported review version');
  const p=obj(d.provenance);exact(p,['author','origin','description']);if(p.origin!=='design_proposal')throw Error('Only unexecuted design proposals are supported');
  if(!Array.isArray(d.nodes)||!d.nodes.length||d.nodes.length>64||!Array.isArray(d.edges)||d.edges.length>128)throw Error('Review graph bounds exceeded');
  const nodes=d.nodes.map(v=>{const n=obj(v);exact(n,['id','title','kind','rationale','method','procedure','inputs','outputs','applicability','assumptions','rule','evidence','availability','alternatives','sources']);
    if(!['objective','criterion','method','selection','iteration'].includes(String(n.kind)))throw Error('Unknown step kind');
    return {id:id(n.id),title:str(n.title,160),kind:n.kind as ReviewStep['kind'],rationale:str(n.rationale),method:str(n.method),procedure:list(n.procedure),inputs:list(n.inputs),outputs:list(n.outputs),applicability:str(n.applicability),assumptions:list(n.assumptions),rule:str(n.rule),evidence:str(n.evidence),availability:str(n.availability),alternatives:list(n.alternatives),sources:list(n.sources)};
  });
  const ids=new Set(nodes.map(n=>n.id));if(ids.size!==nodes.length||nodes.filter(n=>n.kind==='objective').length!==1)throw Error('Review requires unique nodes and one objective');
  const pairs=new Set<string>();const edges=d.edges.map(v=>{const e=obj(v);exact(e,['source','target','relationship']);const source=id(e.source),target=id(e.target),key=JSON.stringify([source,target]);if(!ids.has(source)||!ids.has(target)||source===target||pairs.has(key))throw Error('Invalid or duplicate relationship');pairs.add(key);return {source,target,relationship:str(e.relationship,200)};});
  // A bounded dependency DAG; next-generation intent is a terminal node, never a pretend running loop.
  const seen=new Set<string>(),visiting=new Set<string>();function visit(key:string){if(visiting.has(key))throw Error('Design dependency cycle');if(seen.has(key))return;visiting.add(key);for(const e of edges.filter(e=>e.source===key))visit(e.target);visiting.delete(key);seen.add(key);}
  visit(nodes.find(n=>n.kind==='objective')!.id);if(seen.size!==nodes.length)throw Error('Every step must be reachable from the objective');
  return freeze({format:d.format,id:id(d.id),revision:d.revision as number,title:str(d.title,200),provenance:{author:str(p.author,160),origin:p.origin,description:str(p.description)},nodes,edges});
}
export class EvaluationReview {
  readonly design:EvaluationDesign;
  private notes:ReviewNote[]=[];
  constructor(design:EvaluationDesign){this.design=parseDesign(JSON.stringify(design));}
  get feedback():readonly ReviewNote[]{return freeze(this.notes.map(n=>({...n})));}
  scene():{nodes:SceneNode[];edges:SceneEdge[]} {return {nodes:this.design.nodes.map(n=>({id:n.id,label:n.title,status:n.kind,x:0,y:0})),edges:this.design.edges.map((e,i)=>({id:`review-${i}`,source:e.source,target:e.target,label:e.relationship}))};}
  save(node:string,concern:Concern,change:string){if(!this.design.nodes.some(n=>n.id===node)||!concerns.includes(concern))throw Error('Unknown review target');const note=freeze({node,concern,change:str(change,2048)});const i=this.notes.findIndex(n=>n.node===node&&n.concern===concern);if(i<0){if(this.notes.length>=64)throw Error('Review contains 64 concerns');this.notes.push(note);}else this.notes[i]=note;}
  remove(node:string,concern:Concern){this.notes=this.notes.filter(n=>n.node!==node||n.concern!==concern);}
  export():string{return JSON.stringify({format:'amphora.evaluation-feedback.v1',authority:'local_unsubmitted',target:'future_campaign_only',design:this.design,notes:this.notes},null,2);}
  static import(raw:string):EvaluationReview {
    if(new TextEncoder().encode(raw).length>524288)throw Error('Review file exceeds 512 KiB');
    const d=obj(JSON.parse(raw));
    if(d.format==='amphora.evaluation-review.v1')return new EvaluationReview(parseDesign(raw));
    exact(d,['format','authority','target','design','notes']);if(d.format!=='amphora.evaluation-feedback.v1'||d.authority!=='local_unsubmitted'||d.target!=='future_campaign_only'||!Array.isArray(d.notes)||d.notes.length>64)throw Error('Unsupported feedback document');
    const review=new EvaluationReview(parseDesign(JSON.stringify(d.design))),keys=new Set<string>();
    for(const value of d.notes){const n=obj(value);exact(n,['node','concern','change']);const key=JSON.stringify([n.node,n.concern]);if(keys.has(key))throw Error('Duplicate concern');keys.add(key);review.save(str(n.node),n.concern as Concern,str(n.change,2048));}return review;
  }
}
