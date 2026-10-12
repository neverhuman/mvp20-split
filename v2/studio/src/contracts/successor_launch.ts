import type {ValidateFunction} from 'ajv';
import compiled from './generated/successor_launch/validators.js';
import type {SuccessorLaunchRequest} from './generated/successor_launch/request.js';
import type {SuccessorLaunchReceipt} from './generated/successor_launch/receipt.js';
import type {SuccessorLaunchReceiptQuery} from './generated/successor_launch/query.js';
import type {AdmitDraftSuccessor} from './generated/successor_launch/admission.js';
export type {SuccessorLaunchRequest,SuccessorLaunchReceipt,SuccessorLaunchReceiptQuery,AdmitDraftSuccessor};
interface Wire {request:SuccessorLaunchRequest;receipt:SuccessorLaunchReceipt;query:SuccessorLaunchReceiptQuery;admission:AdmitDraftSuccessor}
const validators=compiled as Record<string,ValidateFunction>;
export function decodeSuccessor<K extends keyof Wire>(kind:K,value:unknown):Wire[K]{
  const validate=validators[kind] as ValidateFunction<Wire[K]>;
  if(!validate(value))throw Error('invalid_successor_response');return value;
}
