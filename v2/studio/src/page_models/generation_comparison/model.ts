import type {ObservationSource} from '../../transport/observations.js';
import type {DataProvenanceClient} from '../../transport/provenance/data.js';
import type {RunContext} from '../graph_window.js';
import {RequestLane} from '../request_lane.js';
import {discover,type Discovery} from './discovery.js';
import {RetainedGeneration,GenerationComparison} from './checkpoint.js';
type Phase='idle'|'loading'|'ready'|'denied'|'failed'|'stale';
type Slot=Readonly<{phase:Phase;key:string|null;value:RetainedGeneration|null}>;
export type GenerationView=Readonly<{phase:Phase;discovery:Discovery|null;left:Slot;right:Slot;message:string|null}>;
const empty=():Slot=>({phase:'idle',key:null,value:null});
export class GenerationModel {
 private readonly lane=new RequestLane();private readonly lanes={left:new RequestLane(),right:new RequestLane()};
 private listeners=new Set<()=>void>();private disposed=false;
 private view:GenerationView={phase:'idle',discovery:null,left:empty(),right:empty(),message:null};
 constructor(private readonly run:RunContext,private readonly runtime:Pick<ObservationSource,'snapshot'|'detail'>,private readonly data:Pick<DataProvenanceClient,'jsonArtifact'>){}
 get snapshot(){return this.view;}
 get comparison(){return this.view.left.value&&this.view.right.value?new GenerationComparison(this.view.left.value,this.view.right.value):null;}
 subscribe(listener:()=>void){this.listeners.add(listener);return()=>{this.listeners.delete(listener);};}
 private patch(fields:Partial<GenerationView>){if(this.disposed)return;this.view=Object.freeze({...this.view,...fields});for(const listener of this.listeners)listener();}
 async refresh(){
  if(this.disposed)return;const ticket=this.lane.begin();this.lanes.left.cancel();this.lanes.right.cancel();
  this.patch({phase:'loading',discovery:null,left:empty(),right:empty(),message:null});
  try{const discovery=await discover(this.run,this.runtime,ticket.signal);if(ticket.current())this.patch({phase:'ready',discovery});}
  catch(error){if(ticket.current())this.fail(error);}
 }
 async select(side:'left'|'right',key:string){
  if(this.disposed||this.view.phase!=='ready')return;
  const ticket=this.lanes[side].begin(),choice=this.view.discovery?.choices.find(c=>c.key===key);
  this.patch({[side]:{phase:choice?'loading':'idle',key:choice?key:null,value:null},message:null});
  if(!choice)return;
  try{
   const raw=await this.data.jsonArtifact(choice.reference,ticket.signal);
   if(!ticket.current())return;
   const value=new RetainedGeneration(choice.reference,raw);
   this.patch({[side]:{phase:'ready',key,value}});
  }catch(error){if(ticket.current())this.fail(error,side,key);}
 }
 private fail(error:unknown,side?:'left'|'right',key?:string){
  const kind=(error as {kind?:string})?.kind;
  if(kind==='aborted')return;
  if(kind==='denied'||kind==='resnapshot'||!side){
   this.lane.cancel();this.lanes.left.cancel();this.lanes.right.cancel();
   this.patch({phase:kind==='denied'?'denied':kind==='resnapshot'?'stale':'failed',discovery:null,left:empty(),right:empty(),message:kind==='denied'?'Search evidence is unavailable to this session.':kind==='resnapshot'?'The campaign changed during discovery. Refresh for a coherent read.':'Search outputs could not be verified.'});
  }else this.patch({[side]:{phase:'failed',key:key??null,value:null},message:kind==='limit'?'This checkpoint exceeds the 256 KiB inspection limit.':'The selected checkpoint could not be verified.'});
 }
 dispose(){this.disposed=true;this.lane.cancel();this.lanes.left.cancel();this.lanes.right.cancel();this.listeners.clear();}
}
