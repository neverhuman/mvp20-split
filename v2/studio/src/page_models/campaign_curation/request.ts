import type { CurationReceipt,CurationRequest } from '../../contracts/campaign_curation.js';
import { CurationCommands,CurationCommandFailure } from '../../transport/campaign_curation/commands.js';
import { CurationSubmission } from '../../transport/campaign_curation/submission.js';
import { RequestLane } from '../request_lane.js';
import { immutable } from '../explore/context.js';
import { CurationJournal } from './journal.js';

interface RequestView {
  phase:'idle'|'restoring'|'preparing'|'submitting'|'unresolved'|'reconciling'|'accepted'|'conflict'|'denied'|'storage_failed';
  receipt:CurationReceipt|null; reason:string|null;
}
/** One original request. Progress and eventual graph adoption belong to separate owners. */
export class CurationRequestModel {
  private readonly lane=new RequestLane();
  private readonly listeners=new Set<()=>void>();
  private command:CurationSubmission|undefined;
  private previous:CurationReceipt|undefined;
  private disposed=false;
  private initialized=false;
  private view:Readonly<RequestView>=Object.freeze({phase:'restoring',receipt:null,reason:null});
  constructor(private readonly source:Pick<CurationCommands,'submit'|'receipt'>,private readonly journal:CurationJournal) {}
  get snapshot(){return this.view;}
  get submission(){return this.view.phase==='accepted'?this.command:undefined;}
  get canSubmit(){return !this.disposed&&this.view.phase==='idle';}
  get canReconcile(){return !this.disposed&&!!this.command&&['accepted','unresolved'].includes(this.view.phase);}
  subscribe(listener:()=>void){this.listeners.add(listener);return()=>{this.listeners.delete(listener);};}
  private patch(fields:Partial<RequestView>){if(this.disposed)return;this.view=immutable({...this.view,...fields});for(const listener of this.listeners)listener();}
  async initialize(){
    if(this.initialized||this.disposed)return;this.initialized=true;
    const lane=this.lane.begin();
    try{
      const saved=await this.journal.load();if(!lane.current())return;
      this.command=saved?.command;this.previous=saved?.receipt;
      this.patch({phase:saved?'unresolved':'idle',receipt:null,reason:null});
    }catch{if(lane.current())this.patch({phase:'storage_failed',receipt:null,reason:'recovery_record_unavailable'});}
  }
  async submit(request:CurationRequest){
    if(!this.canSubmit)throw Error('curation_not_available');
    const lane=this.lane.begin();this.patch({phase:'preparing',receipt:null,reason:null});
    try{
      const command=await CurationSubmission.create(request);if(!lane.current())return;
      try{await this.journal.save(command);}catch{if(lane.current())this.patch({phase:'storage_failed',reason:'recovery_record_unavailable'});return;}
      if(!lane.current())return;
      this.command=command;this.previous=undefined;
      await this.perform(true);
    }catch{if(lane.current())this.patch({phase:'idle',reason:'invalid_request'});}
  }
  reconcile(){if(!this.canReconcile)throw Error('curation_not_reconcilable');return this.perform(false);}
  retryOriginal(){if(!this.canReconcile||this.view.phase!=='unresolved')throw Error('curation_not_retryable');return this.perform(true);}
  deny(){this.lane.cancel();this.command=undefined;this.previous=undefined;this.patch({phase:'denied',receipt:null,reason:'denied'});}
  suspend(){
    this.lane.cancel();this.command=undefined;this.previous=undefined;this.initialized=false;
    this.patch({phase:'restoring',receipt:null,reason:null});
  }
  dispose(){this.disposed=true;this.lane.cancel();this.command=undefined;this.previous=undefined;this.view=Object.freeze({phase:'denied',receipt:null,reason:null});this.listeners.clear();}
  private async perform(post:boolean){
    const command=this.command!,lane=this.lane.begin();
    this.patch({phase:post?'submitting':'reconciling',receipt:null,reason:null});
    // Subscribers may synchronously revoke or dispose the region.
    if(!lane.current())return;
    try{
      const raw=await(post?this.source.submit(command,lane.signal):this.source.receipt(command,lane.signal));
      if(!lane.current())return;
      const receipt=command.verify(raw,this.previous);
      try{await this.journal.save(command,receipt);}catch{if(lane.current())this.patch({phase:'storage_failed',receipt:null,reason:'recovery_record_unavailable'});return;}
      if(!lane.current())return;this.previous=receipt;
      this.patch({phase:'accepted',receipt,reason:null});
    }catch(error){
      if(!lane.current())return;
      if(error instanceof CurationCommandFailure&&error.kind==='denied'){this.deny();return;}
      this.patch({phase:error instanceof CurationCommandFailure&&error.kind==='conflict'?'conflict':'unresolved',receipt:null,
        reason:error instanceof CurationCommandFailure?error.kind:'invalid_response'});
    }
  }
}
