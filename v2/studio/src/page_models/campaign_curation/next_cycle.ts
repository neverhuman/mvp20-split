import type {CurationClient} from '../../transport/campaign_curation/client.js';
import type {CurationJournal} from './journal.js';
import {RecordedCuration} from './records.js';
import {RequestLane} from '../request_lane.js';

/** Explicit next request after a fresh verified terminal read; no command/provider call. */
export class CurationNextCycle{
  private lane=new RequestLane();private disposed=false;
  constructor(private readonly source:Pick<CurationClient,'curation'>,private readonly journal:CurationJournal){}
  async prepare(original:RecordedCuration){
    if(this.disposed||!original.terminal)throw Error('curation_terminal_required');
    const lane=this.lane.begin(),raw=await this.source.curation(original.selection,lane.signal);
    if(!lane.current()||!raw)throw Error('curation_terminal_unavailable');
    const current=new RecordedCuration(raw,original.selection);original.reconcile(current);
    await this.journal.beginNext(current,lane.signal);
    if(!lane.current())throw Error('curation_terminal_unavailable');
  }
  dispose(){this.disposed=true;this.lane.cancel();}
}
