import type {SuccessorLaunchReceipt} from '../../contracts/successor_launch.js';
import type {SuccessorSubmission} from '../../transport/successor_launch/submission.js';
import type {SuccessorClient} from '../../transport/successor_launch/client.js';
import {LaunchFailure} from '../../transport/launch/client.js';
import {RequestLane} from '../request_lane.js';
import {immutable} from '../explore/context.js';
import type {SuccessorJournal} from './journal.js';

interface SuccessorView{
  phase:'restoring'|'idle'|'submitting'|'unresolved'|'reconciling'|'ready'|'conflict'|'denied'|'storage_failed';
  receipt:SuccessorLaunchReceipt|null;reason:string|null;
}
/** Durable original launch intent; Deployment progress never substitutes for Runtime execution. */
export class SuccessorLaunchModel{
  private readonly lane=new RequestLane();private readonly listeners=new Set<()=>void>();
  private command:SuccessorSubmission|undefined;private previous:SuccessorLaunchReceipt|undefined;
  private initialized=false;private disposed=false;
  private view:Readonly<SuccessorView>=Object.freeze({phase:'restoring',receipt:null,reason:null});
  constructor(private readonly source:Pick<SuccessorClient,'submit'|'receipt'>,private readonly journal:SuccessorJournal){}
  get snapshot(){return this.view;}
  get submission(){return this.view.phase==='ready'?this.command:undefined;}
  get canSubmit(){return !this.disposed&&this.view.phase==='idle';}
  get canReconcile(){return !this.disposed&&!!this.command&&['ready','unresolved'].includes(this.view.phase);}
  get canRetry(){return this.canReconcile&&(this.view.phase==='unresolved'||this.view.receipt?.phase==='recovery_required');}
  subscribe(listener:()=>void){this.listeners.add(listener);return()=>{this.listeners.delete(listener);};}
  private patch(fields:Partial<SuccessorView>){if(this.disposed)return;this.view=immutable({...this.view,...fields});for(const listener of this.listeners)listener();}
  initialize(){
    if(this.disposed||this.initialized)return;this.initialized=true;
    try{const saved=this.journal.load();this.command=saved?.command;this.previous=saved?.receipt;
      this.patch({phase:saved?'unresolved':'idle',receipt:null,reason:null});}
    catch{this.patch({phase:'storage_failed',receipt:null,reason:'recovery_record_unavailable'});}
  }
  submit(command:SuccessorSubmission){
    if(!this.canSubmit)throw Error('successor_not_available');
    try{this.journal.save(command);}catch{this.patch({phase:'storage_failed',receipt:null,reason:'recovery_record_unavailable'});return Promise.resolve();}
    this.command=command;this.previous=undefined;return this.perform(true);
  }
  reconcile(){if(!this.canReconcile)throw Error('successor_not_reconcilable');return this.perform(false);}
  retryOriginal(){if(!this.canRetry)throw Error('successor_not_retryable');return this.perform(true);}
  deny(){this.lane.cancel();this.command=undefined;this.previous=undefined;this.patch({phase:'denied',receipt:null,reason:'denied'});}
  suspend(){this.lane.cancel();this.command=undefined;this.previous=undefined;this.initialized=false;this.patch({phase:'restoring',receipt:null,reason:null});}
  dispose(){this.disposed=true;this.lane.cancel();this.command=undefined;this.previous=undefined;this.view=Object.freeze({phase:'denied',receipt:null,reason:null});this.listeners.clear();}
  private async perform(post:boolean){
    const command=this.command!,lane=this.lane.begin();this.patch({phase:post?'submitting':'reconciling',receipt:null,reason:null});
    if(!lane.current())return;
    try{
      const raw=await(post?this.source.submit(command,lane.signal):this.source.receipt(command,lane.signal,this.previous));
      if(!lane.current())return;const receipt=command.verify(raw,this.previous);
      try{this.journal.save(command,receipt);}catch{this.patch({phase:'storage_failed',receipt:null,reason:'recovery_record_unavailable'});return;}
      this.previous=receipt;this.patch({phase:'ready',receipt,reason:receipt.reason_code});
    }catch(error){
      if(!lane.current())return;
      if(error instanceof LaunchFailure&&error.kind==='denied'){this.deny();return;}
      this.patch({phase:error instanceof LaunchFailure&&error.kind==='conflict'?'conflict':'unresolved',receipt:null,
        reason:error instanceof LaunchFailure?error.kind:'invalid_response'});
    }
  }
}
