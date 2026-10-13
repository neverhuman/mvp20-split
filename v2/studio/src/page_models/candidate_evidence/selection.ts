import type {ArtifactRef} from '../../contracts/observations.js';
import type {SearchCheckpoint} from '../../contracts/search.js';
import {ReadFailure} from '../../transport/failure.js';
import {RetainedGeneration,equalValue,type CandidateRow} from '../generation_comparison/checkpoint.js';

export type SelectionState='selected'|'not_selected'|'selection_pending'|'selection_unavailable'|'insufficient_evidence'|'zero_requested';
export type CandidateSelection=Readonly<{candidateId:string;state:SelectionState;selected:boolean;front:number|null;sameFront:readonly string[];quality:string|null;evaluationStatus:string;constraintViolation:number|null;values:Readonly<Record<string,number>>}>;
function requireEvidence(value:boolean):asserts value {if(!value)throw new ReadFailure('invalid_response');}

/** Projects an explicit tool receipt; never calculates ranks, dominance or a winner. */
export class RetainedSelection {
 readonly reference:ArtifactRef;
 readonly generation:number;
 readonly policy:string|null;
 readonly configuredPolicy:string;
 readonly requested:number|null;
 readonly selected:readonly string[];
 readonly disposition:NonNullable<SearchCheckpoint['selection']>['disposition']|null;
 readonly objectives:SearchCheckpoint['specification']['objectives'];
 readonly evaluator:SearchCheckpoint['specification']['evaluator'];
 readonly membershipSha256:string|null;
 private readonly checkpoint:SearchCheckpoint;
 private readonly rows:readonly CandidateRow[];
 constructor(retained:RetainedGeneration){
  const snapshot=new RetainedGeneration(retained.reference,retained.record);
  this.checkpoint=snapshot.record;this.rows=snapshot.candidates;
  this.reference=structuredClone(snapshot.reference);this.generation=snapshot.record.generation;
  const selection=this.checkpoint.selection;
  this.configuredPolicy=this.checkpoint.specification.operators.selection;
  this.policy=selection?.policy??null;this.requested=selection?.requested??null;
  this.disposition=selection?.disposition??null;this.membershipSha256=selection?.membership_sha256??null;
  this.objectives=structuredClone(this.checkpoint.specification.objectives);
  this.evaluator=structuredClone(this.checkpoint.specification.evaluator);
  const final=['selected','stopped'].includes(this.checkpoint.phase);
  if(selection){
   requireEvidence(selection.policy===this.checkpoint.specification.operators.selection);
   requireEvidence(selection.selected.length<=selection.requested);
   for(const rank of selection.ranks){
    const row=this.rows.find(r=>r.id===rank.candidate_id);
    requireEvidence(!!row);
    if(rank.feasible)requireEvidence(row.status==='evaluated'&&row.violation===0);
   }
   const count=selection.selected.length;
   if(selection.disposition==='selected')requireEvidence(selection.requested>0&&count===selection.requested);
   if(selection.disposition==='zero_requested')requireEvidence(selection.requested===0&&count===0);
   if(selection.disposition==='no_feasible_candidates')requireEvidence(count===0&&!selection.ranks.some(r=>r.feasible));
   if(selection.disposition==='insufficient_feasible_candidates')requireEvidence(selection.requested>count);
  }
  this.selected=Object.freeze(final?[...(selection?.selected??[])]:[]);
 }
 forCandidate(id:string):CandidateSelection {
  const row=this.rows.find(r=>r.id===id);requireEvidence(!!row);
  const selection=this.checkpoint.selection;
  const final=['selected','stopped'].includes(this.checkpoint.phase);
  const rank=final?selection?.ranks.find(r=>r.candidate_id===id):undefined;
  let state:SelectionState;
  if(!selection)state='selection_unavailable';
  else if(!final)state='selection_pending';
  else if(selection.disposition==='zero_requested')state='zero_requested';
  else if(selection.disposition==='no_feasible_candidates'||selection.disposition==='insufficient_feasible_candidates')state='insufficient_evidence';
  else if(row.status!=='evaluated'||row.violation===null)state='insufficient_evidence';
  else state=this.selected.includes(id)?'selected':'not_selected';
  return Object.freeze({candidateId:id,state,selected:this.selected.includes(id),front:rank?.feasible?rank.front:null,
   sameFront:Object.freeze(rank?.feasible?selection!.ranks.filter(r=>r.feasible&&r.front===rank.front).map(r=>r.candidate_id):[]),
   quality:row.quality,evaluationStatus:row.status,constraintViolation:row.violation,values:row.values});
 }
 /** Scope/specification equality is required before cross-snapshot comparison. */
 comparableTo(other:RetainedSelection):boolean {
  return this.checkpoint.specification_sha256===other.checkpoint.specification_sha256
   &&equalValue(this.checkpoint.specification,other.checkpoint.specification)
   &&['selected','stopped'].includes(this.checkpoint.phase)&&['selected','stopped'].includes(other.checkpoint.phase)
   &&this.policy!==null&&this.policy===other.policy;
 }
}
