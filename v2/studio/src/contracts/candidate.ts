import compiled from './generated/candidate/validators.js';
import profiles from './generated/candidate/profiles.json' with {type:'json'};
import type {StructureRequest} from './generated/candidate/request.js';
import type {StructureResult} from './generated/candidate/result.js';
import type {CandidateRevision} from './generated/candidate/candidate.js';
import type {AcceptedToolExecution} from './generated/candidate/producer.js';
import type {ArtifactRef} from './observations.js';
import {decoder} from './scientific/validation.js';
export type {StructureRequest, StructureResult, CandidateRevision, AcceptedToolExecution};
export type CandidateReference=CandidateRevision['reference'];
export const decodeCandidate=decoder<{request:StructureRequest;result:StructureResult;candidate:CandidateRevision;producer:AcceptedToolExecution}>(compiled);
export const structureProfiles=Object.freeze(profiles);
export const finiteStructureProfile=Object.freeze({schema_id:'chemical-structure.finite-smiles-2d',version:'1',sha256:'537435b380c2f36ffb5b7b404e352379beb0b14e899a560b554d5b588c70bc73'});
export function isStructure(ref:ArtifactRef,kind:'request'|'result'='result'){
 const pin=structureProfiles[kind];
 return ref.schema_ref.schema_id===pin.schema_id&&ref.schema_ref.version===pin.version&&ref.schema_ref.sha256===pin.sha256;
}
