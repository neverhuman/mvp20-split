import type {ArtifactRef} from '../../contracts/observations.js';
import type {MaterialStateRevision} from '../../contracts/scientific/provenance.js';
import {ReadFailure} from '../../transport/failure.js';
import {equalValue} from '../generation_comparison/checkpoint.js';
import type {RetainedSelection} from './selection.js';

type CandidateReference=MaterialStateRevision['candidate'];
export type StructureRecommendation=Readonly<{status:'unranked';reason:'no_molecular_selection_policy'|'numeric_selection_inapplicable';candidate:CandidateReference;representation:ArtifactRef;properties:'not_available';synthesis:'not_available'}>;

/** A structural formula/depiction has no evaluation or recommendation authority. */
export function suppliedStructureEvidence(candidate:CandidateReference,representation:ArtifactRef,numeric:RetainedSelection|null=null):StructureRecommendation {
 if(!equalValue(candidate.scope,representation.scope)||!candidate.candidate_id||!Number.isSafeInteger(candidate.revision)||candidate.revision<1)
  throw new ReadFailure('invalid_response');
 return Object.freeze({status:'unranked',reason:numeric?'numeric_selection_inapplicable':'no_molecular_selection_policy',
  candidate:structuredClone(candidate),representation:structuredClone(representation),properties:'not_available',synthesis:'not_available'});
}
