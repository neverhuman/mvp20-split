import {RequestLane} from '../request_lane.js';
import type {RecordedCuration} from './records.js';
import type {CurationGraphReader,CurationGraphReview} from './graph_review.js';
interface GraphReviewView{phase:'idle'|'loading'|'ready'|'denied'|'failed';review:CurationGraphReview|null}
export class CurationGraphModel{
  private readonly lane=new RequestLane();private readonly listeners=new Set<()=>void>();private disposed=false;
  private view:Readonly<GraphReviewView>=Object.freeze({phase:'idle',review:null});
  constructor(private readonly source:Pick<CurationGraphReader,'read'>){}
  get snapshot(){return this.view;}
  subscribe(listener:()=>void){this.listeners.add(listener);return()=>{this.listeners.delete(listener);};}
  private patch(view:GraphReviewView){if(this.disposed)return;this.view=Object.freeze(view);for(const listener of this.listeners)listener();}
  async load(record:RecordedCuration){
    if(this.disposed)return;const lane=this.lane.begin();this.patch({phase:'loading',review:null});if(!lane.current())return;
    try{const review=await this.source.read(record,lane.signal);if(lane.current())this.patch({phase:review?'ready':'idle',review});}
    catch(error){if(!lane.current())return;const denied=error!==null&&typeof error==='object'&&'kind'in error&&error.kind==='denied';this.patch({phase:denied?'denied':'failed',review:null});}
  }
  clear(){this.lane.cancel();this.patch({phase:'idle',review:null});}
  dispose(){this.disposed=true;this.lane.cancel();this.view=Object.freeze({phase:'idle',review:null});this.listeners.clear();}
}
