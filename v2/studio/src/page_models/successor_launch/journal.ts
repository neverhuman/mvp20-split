import type {SuccessorLaunchReceipt} from '../../contracts/successor_launch.js';
import {SuccessorSubmission} from '../../transport/successor_launch/submission.js';
import type {CurationActor,CurationStorage} from '../campaign_curation/journal.js';
import {sameScope} from '../../transport/campaign_curation/identity.js';

export interface SuccessorContext extends CurationActor{curation_id:string}
/** One original per retained curation. Cached receipts are recovery hints, never live authority. */
export class SuccessorJournal{
  private readonly key:string;
  constructor(readonly context:SuccessorContext,private readonly storage:CurationStorage){
    this.key='amphora.successor.v1:'+JSON.stringify([context.scope.tenant_id,context.scope.project_id,context.actor_id,context.run_id,context.curation_id]);
  }
  private authorize(command:SuccessorSubmission){
    const value=command.request;
    if(value.identity.actor_id!==this.context.actor_id||!sameScope(value.identity.scope,this.context.scope)||
      value.payload.admission.payload.predecessor.run_id!==this.context.run_id)throw Error('successor_storage_scope');
  }
  load(){
    const raw=this.storage.getItem(this.key);if(raw===null)return null;if(raw.length>600000)throw Error('successor_storage_invalid');
    const value=JSON.parse(raw);
    if(!value||value.version!==1||typeof value.body!=='string'||Object.keys(value).some(key=>!['version','body','receipt'].includes(key)))throw Error('successor_storage_invalid');
    const command=SuccessorSubmission.restore(value.body);this.authorize(command);
    return {command,receipt:value.receipt?command.verify(value.receipt):undefined};
  }
  save(command:SuccessorSubmission,receipt?:SuccessorLaunchReceipt){
    this.authorize(command);const old=this.load();
    if(old&&old.command.body!==command.body)throw Error('successor_storage_pending');
    if(receipt)command.verify(receipt,old?.receipt);
    const raw=JSON.stringify({version:1,body:command.body,...(receipt?{receipt}:{})});
    this.storage.setItem(this.key,raw);if(this.storage.getItem(this.key)!==raw)throw Error('successor_storage_changed');
  }
}
