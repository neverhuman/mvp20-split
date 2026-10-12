import { boundedJSON } from '../bounded_json.js';
import type { CurationSubmission } from './submission.js';

export class CurationCommandFailure extends Error {
  constructor(readonly kind:'denied'|'missing'|'conflict'|'invalid_request'|'invalid_response'|'unavailable') { super(kind); }
}
/** Explicit original submit or read-only receipt query; no automatic retries. */
export class CurationCommands {
  constructor(private readonly fetcher:typeof fetch=fetch,private readonly timeoutMs=15000) {
    if(!Number.isSafeInteger(timeoutMs)||timeoutMs<1) throw Error('invalid_transport_configuration');
  }
  submit(command:CurationSubmission,signal:AbortSignal) { return this.send(command,false,signal); }
  receipt(command:CurationSubmission,signal:AbortSignal) { return this.send(command,true,signal); }
  private async send(command:CurationSubmission,query:boolean,signal:AbortSignal) {
    const controller=new AbortController(),abort=()=>controller.abort();
    signal.addEventListener('abort',abort,{once:true});if(signal.aborted)abort();
    const timer=setTimeout(abort,this.timeoutMs);
    try {
      if(controller.signal.aborted) throw new CurationCommandFailure('unavailable');
      const response=await this.fetcher.call(globalThis,'/api/planning/v1/campaign-curations'+(query?'/receipts/query':''),{
        method:'POST',body:query?JSON.stringify(command.query):command.body,credentials:'same-origin',redirect:'error',signal:controller.signal,
        headers:{Accept:'application/json','Content-Type':'application/json'}});
      if(response.status===401||response.status===403) {await response.body?.cancel();throw new CurationCommandFailure('denied');}
      if(!response.ok) {
        const value=await boundedJSON(response,4096) as {reason_code?:unknown};
        if(query&&response.status===404&&value?.reason_code==='curation_receipt_not_recorded') throw new CurationCommandFailure('missing');
        if(response.status===409&&['curation_command_conflict','curation_receipt_conflict'].includes(String(value?.reason_code))) throw new CurationCommandFailure('conflict');
        if(response.status===422&&value?.reason_code==='invalid_curation_request') throw new CurationCommandFailure('invalid_request');
        throw new CurationCommandFailure('unavailable');
      }
      const raw=await boundedJSON(response,65536);
      if(controller.signal.aborted) throw new CurationCommandFailure('unavailable');
      try { return command.verify(raw); } catch { throw new CurationCommandFailure('invalid_response'); }
    } catch(error) { throw error instanceof CurationCommandFailure?error:new CurationCommandFailure('unavailable'); }
    finally {clearTimeout(timer);signal.removeEventListener('abort',abort);}
  }
}
