import type { CurationReceipt } from '../../contracts/campaign_curation.js';
import { CurationSubmission } from '../../transport/campaign_curation/submission.js';
import { sameScope } from '../../transport/campaign_curation/identity.js';
import {RecordedCuration,sameValue} from './records.js';

export interface CurationStorage { getItem(key:string):string|null; setItem(key:string,value:string):void }
export interface CurationActor { actor_id:string; scope:{tenant_id:string;project_id:string}; run_id:string }

/** Scoped untrusted recovery hint; storage never establishes server acceptance. */
export class CurationJournal {
  private readonly key:string;
  constructor(readonly context:CurationActor,private readonly storage:CurationStorage) {
    this.key='amphora.curation.v1:'+JSON.stringify([context.scope.tenant_id,context.scope.project_id,context.actor_id,context.run_id]);
  }
  private authorize(command:CurationSubmission) {
    const value=command.request;
    if(value.identity.actor_id!==this.context.actor_id || !sameScope(value.identity.scope,this.context.scope) ||
      value.payload.context.predecessor.run_id!==this.context.run_id) throw Error('curation_storage_scope');
  }
  async load() {
    const raw=this.storage.getItem(this.key);if(raw===null)return null;
    if(raw.length>600000)throw Error('curation_storage_invalid');
    const value=JSON.parse(raw);
    if(value===null)return null;
    if(!value||value.version!==1||typeof value.body!=='string'||Object.keys(value).some(key=>!['version','body','receipt'].includes(key)))throw Error('curation_storage_invalid');
    const command=await CurationSubmission.restore(value.body);this.authorize(command);
    return {command,receipt:value.receipt?command.verify(value.receipt):undefined};
  }
  async save(command:CurationSubmission,receipt?:CurationReceipt) {
    this.authorize(command);
    const original=this.storage.getItem(this.key), prior=await this.load();
    if(prior&&prior.command.body!==command.body)throw Error('curation_storage_pending');
    if(receipt)command.verify(receipt,prior?.receipt);
    // Catch a changed tab during async hash validation. Server identity remains the lock.
    if(this.storage.getItem(this.key)!==original)throw Error('curation_storage_changed');
    const raw=JSON.stringify({version:1,body:command.body,...(receipt?{receipt}:{})});
    this.storage.setItem(this.key,raw);
    if(this.storage.getItem(this.key)!==raw)throw Error('curation_storage_changed');
  }
  /** Explicit preparation of a different request, never a retry/refund of this terminal outcome. */
  async beginNext(record:RecordedCuration,signal:AbortSignal){
    const original=this.storage.getItem(this.key),saved=await this.load(),value=record.data;
    if(!saved||!record.terminal||saved.command.curationId!==value.receipt.reference.curation_id||
      saved.command.sha256!==value.receipt.request_sha256||!sameValue(saved.command.request.payload,value.specification)||
      !sameValue(saved.command.request.identity,value.receipt.identity))throw Error('curation_terminal_original_required');
    if(signal.aborted)throw Error('curation_cycle_aborted');
    if(this.storage.getItem(this.key)!==original)throw Error('curation_storage_changed');
    const archive=this.key+':original:'+saved.command.request.identity.command_id;
    const prior=this.storage.getItem(archive);if(prior!==null&&prior!==original)throw Error('curation_archive_changed');
    this.storage.setItem(archive,original!);
    if(this.storage.getItem(archive)!==original||this.storage.getItem(this.key)!==original)throw Error('curation_storage_changed');
    this.storage.setItem(this.key,'null');if(this.storage.getItem(this.key)!=='null')throw Error('curation_storage_changed');
  }
}
