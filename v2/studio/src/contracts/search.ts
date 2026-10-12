import compiled from './generated/search/validators.js';
import profiles from './generated/search/profiles.json' with {type:'json'};
import type {SearchCheckpoint} from './generated/search/checkpoint.js';
import type {ArtifactRef} from './observations.js';
import {decoder} from './scientific/validation.js';
export type {SearchCheckpoint};
export const decodeSearch=decoder<{checkpoint:SearchCheckpoint}>(compiled);
export const checkpointProfile=Object.freeze(profiles.checkpoint);
export function isCheckpoint(ref:ArtifactRef){return ref.schema_ref.schema_id===checkpointProfile.schema_id&&ref.schema_ref.version===checkpointProfile.version&&ref.schema_ref.sha256===checkpointProfile.sha256;}
