import {decodeSearch,isCheckpoint,type SearchCheckpoint} from '../../contracts/search.js';
import type {ArtifactRef} from '../../contracts/observations.js';
import {ReadFailure} from '../../transport/failure.js';

/** Structural comparison of decoded scientific numbers, never a wire digest. */
export function equalValue(a:unknown,b:unknown):boolean {
 if(a===b)return true;
 if(Array.isArray(a)||Array.isArray(b))return Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((v,i)=>equalValue(v,b[i]));
 if(!a||!b||typeof a!=='object'||typeof b!=='object')return false;
 const x=a as Record<string,unknown>,y=b as Record<string,unknown>;
 return Object.keys(x).length===Object.keys(y).length&&Object.keys(x).every(k=>Object.hasOwn(y,k)&&equalValue(x[k],y[k]));
}
function requireValid(value:boolean):asserts value{if(!value)throw new ReadFailure('invalid_response');}
function unique(values:readonly string[]){return new Set(values).size===values.length;}
export type CandidateRow=Readonly<{id:string;generation:number;genes:readonly number[];parents:readonly string[];retained:boolean;selected:boolean;status:string;quality:string|null;values:Readonly<Record<string,number>>;violation:number|null}>;
export type ObjectiveSummary=Readonly<{id:string;unit:string;direction:'minimize'|'maximize';best:number|null;count:number}>;

/** Read-only consistency projection. The evolution tool remains the resume/ranking authority. */
export class RetainedGeneration {
 readonly record:SearchCheckpoint;
 readonly reference:ArtifactRef;
 readonly candidates:readonly CandidateRow[];
 readonly objectives:readonly ObjectiveSummary[];
 constructor(reference:ArtifactRef,raw:unknown){
  requireValid(isCheckpoint(reference)&&reference.media_type==='application/json'&&reference.size_bytes<=262144);
  const c=structuredClone(decodeSearch('checkpoint',raw)),s=c.specification;
  requireValid(equalValue(s.scope,reference.scope));
  requireValid(unique(s.objectives.map(o=>o.objective_id))&&unique(s.variables.map(v=>v.variable_id)));
  requireValid(s.variables.every(v=>v.lower<=v.upper));
  const refs=[s.evaluator.constraints,...s.evaluator.context,...c.observations.flatMap(o=>o.outcome.evidence),...(c.previous?[c.previous]:[])];
  requireValid(refs.every(r=>equalValue(r.scope,reference.scope)));
  requireValid(unique(c.attempts.map(a=>a.candidate_id))&&unique(c.population));
  const attempts=new Map(c.attempts.map(a=>[a.candidate_id,a]));
  requireValid(c.population.every(id=>attempts.has(id)));
  requireValid(c.attempts.every(a=>a.generation<=c.generation&&a.genes.length===s.variables.length&&a.genes.every((v,i)=>Number.isFinite(v)&&v>=s.variables[i]!.lower&&v<=s.variables[i]!.upper)));
  requireValid(unique(c.pending.map(p=>p.evaluation_id))&&unique(c.pending.map(p=>p.candidate_id)));
  requireValid(c.pending.every(p=>attempts.has(p.candidate_id)));
  requireValid(unique(c.observations.map(o=>o.evaluation_id))&&unique(c.observations.map(o=>o.candidate_id)));
  for(const o of c.observations){
   requireValid(attempts.has(o.candidate_id)&&equalValue(o.scope,s.scope));
   const pending=c.pending.find(p=>p.evaluation_id===o.evaluation_id);
   if(pending)requireValid(pending.candidate_id===o.candidate_id&&pending.request_sha256===o.request_sha256);
   if(o.outcome.status==='evaluated'){
    const f=o.outcome;
    requireValid(equalValue(f.evaluator,s.evaluator.tool)&&f.constraints_sha256===s.evaluator.constraints.sha256);
    requireValid(Number.isFinite(f.constraint_violation)&&unique(f.objectives.map(v=>v.objective_id))&&f.objectives.length===s.objectives.length);
    requireValid(f.objectives.every(v=>Number.isFinite(v.value)&&s.objectives.some(d=>d.objective_id===v.objective_id&&d.unit===v.unit)));
   }
  }
  if(c.selection){
   requireValid(unique(c.selection.selected)&&unique(c.selection.ranks.map(r=>r.candidate_id)));
   requireValid(c.selection.selected.every(id=>attempts.has(id))&&c.selection.ranks.every(r=>attempts.has(r.candidate_id)));
   requireValid(c.selection.selected.every(id=>c.selection!.ranks.some(r=>r.candidate_id===id&&r.feasible)));
  }
  this.record=c;this.reference=structuredClone(reference);
  this.candidates=Object.freeze(c.attempts.map(a=>{
   const outcome=c.observations.find(o=>o.candidate_id===a.candidate_id)?.outcome;
   const fitness=outcome?.status==='evaluated'?outcome:null;
   return Object.freeze({id:a.candidate_id,generation:a.generation,genes:Object.freeze(a.genes),parents:Object.freeze(a.parents),retained:c.population.includes(a.candidate_id),selected:c.selection?.selected.includes(a.candidate_id)??false,status:outcome?.status??(c.pending.some(p=>p.candidate_id===a.candidate_id)?'pending':a.disposition),quality:fitness?.quality??null,values:Object.freeze(Object.fromEntries(fitness?.objectives.map(v=>[v.objective_id,v.value])??[])),violation:fitness?.constraint_violation??null});
  }));
  this.objectives=Object.freeze(s.objectives.map(o=>{
   const values=this.candidates.filter(r=>r.retained&&r.violation===0&&r.status==='evaluated').map(r=>r.values[o.objective_id]!);
   return Object.freeze({id:o.objective_id,unit:o.unit,direction:o.direction,count:values.length,best:values.length?(o.direction==='minimize'?Math.min(...values):Math.max(...values)):null});
  }));
 }
 get evaluated(){return this.candidates.filter(c=>c.retained&&c.status==='evaluated').length;}
 get unresolved(){return this.candidates.filter(c=>c.retained&&c.status!=='evaluated').length;}
}

export class GenerationComparison {
 readonly compatible:boolean;readonly reason:string|null;
 constructor(readonly left:RetainedGeneration,readonly right:RetainedGeneration){
  this.reason=left.record.specification_sha256!==right.record.specification_sha256||!equalValue(left.record.specification,right.record.specification)?'Different search specifications':left.record.generation===right.record.generation?'Same generation; these may be different stages':!['selected','stopped'].includes(left.record.phase)||!['selected','stopped'].includes(right.record.phase)?'Selection is not complete in both checkpoints':null;
  this.compatible=this.reason===null;
 }
 /** Signed improvement from A to B; positive means better. No aggregate fitness. */
 improvement(objective:string):number|null {
  if(!this.compatible)return null;
  const a=this.left.objectives.find(o=>o.id===objective),b=this.right.objectives.find(o=>o.id===objective);
  if(!a||!b||a.best===null||b.best===null)return null;
  const delta=a.direction==='minimize'?a.best-b.best:b.best-a.best;
  return Number.isFinite(delta)?delta:null;
 }
}
