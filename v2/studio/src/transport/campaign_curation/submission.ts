import { decodeCurationRequest, decodeCurationReceipt, type CurationRequest, type CurationReceipt } from '../../contracts/campaign_curation.js';
import { canonical, same } from '../scientific/identity.js';
import { sameScope, type CurationSelection } from './identity.js';

/** This command contains only bounded integers and references, never graph numeric constants. */
function encoded(value: unknown) {
  const pending:unknown[]=[value];
  while(pending.length) {
    const item=pending.pop();
    if(typeof item==='string'&&/[\uD800-\uDFFF]/u.test(item))throw Error('invalid_curation_unicode');
    if(item&&typeof item==='object')pending.push(...Object.values(item));
  }
  const raw = canonical(value);
  // Python command profile uses ensure_ascii=True, including UTF-16 surrogate pairs.
  return raw.replace(/[\u007f-\uffff]/g, character => '\\u' + character.charCodeAt(0).toString(16).padStart(4,'0'));
}
async function digest(raw: string) {
  return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(raw))),
    value=>value.toString(16).padStart(2,'0')).join('');
}
function normalized(raw: unknown) {
  const value = structuredClone(decodeCurationRequest(raw));
  value.identity.schema_version ??= '1';
  const scope=value.identity.scope, context=value.payload.context;
  if (value.identity.command_family !== 'planning.curate_campaign' || !value.payload.direction.trim()) throw Error('invalid_curation_request');
  const scopes=[context.draft.scope,...context.knowledge.flatMap(head=>[head.snapshot.graph.scope,head.change.graph.scope]),
    ...[...context.questions,...context.needs,...context.artifacts].map(ref=>ref.scope)];
  if (scopes.some(item=>!sameScope(item,scope)) || context.knowledge.some(head=>!same(head.snapshot.graph,head.change.graph)))
    throw Error('curation_scope_mismatch');
  for(const keys of [context.knowledge.map(head=>head.snapshot.graph.graph_id),context.questions.map(ref=>ref.question_id),
    context.needs.map(ref=>ref.need_id),context.artifacts.map(ref=>ref.artifact_id)])
    if(new Set(keys).size!==keys.length) throw Error('duplicate_curation_context');
  if (/[\uD800-\uDFFF]/u.test(value.payload.direction)) throw Error('invalid_curation_unicode');
  return value;
}

/** Frozen original wire bytes and public-contract fingerprints; no retries or network. */
export class CurationSubmission {
  private constructor(readonly body: string, readonly sha256: string, readonly curationId: string) { Object.freeze(this); }
  static async create(request: CurationRequest) {
    const value=normalized(request), body=encoded(value);
    if(new TextEncoder().encode(body).byteLength>262144) throw Error('curation_request_too_large');
    return new CurationSubmission(body,await digest(body),'curation-'+await digest(encoded(value.identity)));
  }
  static async restore(body: string) {
    if(body.length>262144) throw Error('curation_storage_invalid');
    const command=await CurationSubmission.create(JSON.parse(body));
    if(command.body!==body) throw Error('curation_storage_invalid');
    return command;
  }
  get request(): CurationRequest { return JSON.parse(this.body); }
  get query() { return {identity:this.request.identity,request_sha256:this.sha256}; }
  get selection(): CurationSelection { const value=this.request; return {reference:{scope:value.identity.scope,curation_id:this.curationId},
    actor:value.identity.actor_id,predecessor:value.payload.context.predecessor.run_id}; }
  verify(raw: unknown, previous?: CurationReceipt) {
    const receipt=decodeCurationReceipt(raw), request=this.request;
    // Intake and exact receipt-query return the immutable ORIGINAL queued receipt.
    if(!same(receipt.identity,request.identity) || receipt.request_sha256!==this.sha256 ||
      receipt.reference.curation_id!==this.curationId || !sameScope(receipt.reference.scope,request.identity.scope) ||
      receipt.phase!=='queued' || receipt.revision!==0 || receipt.reason_code!==null ||
      receipt.created_at!==receipt.updated_at || previous && !same(receipt,previous)) throw Error('curation_receipt_mismatch');
    return structuredClone(receipt);
  }
}
