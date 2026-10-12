import {decodeSuccessor,type SuccessorLaunchReceipt} from '../../contracts/successor_launch.js';
import {boundedJSON} from '../bounded_json.js';
import {LaunchFailure} from '../launch/client.js';
import type {SuccessorSubmission} from './submission.js';

/** Only Deployment launch/read routes. No direct Runtime admission or implicit retries. */
export class SuccessorClient{
  constructor(private readonly fetcher:typeof fetch=fetch,private readonly timeoutMs=15000){}
  private async request(path:string,signal:AbortSignal,body?:string){
    const controller=new AbortController(),abort=()=>controller.abort();signal.addEventListener('abort',abort,{once:true});
    if(signal.aborted)abort();const timer=setTimeout(abort,this.timeoutMs);
    try{
      if(controller.signal.aborted)throw new LaunchFailure('unavailable');
      const response=await this.fetcher.call(globalThis,'/api/deployment/v1/campaign-successor-launches'+path,{
        method:body===undefined?'GET':'POST',...(body===undefined?{}:{body}),credentials:'same-origin',redirect:'error',signal:controller.signal,
        headers:{Accept:'application/json',...(body===undefined?{}:{'Content-Type':'application/json'})}});
      if([401,403,404].includes(response.status)){await response.body?.cancel();throw new LaunchFailure(response.status===404?'missing':'denied');}
      if(!response.ok){
        const value=await boundedJSON(response,4096) as {reason_code?:unknown};
        if(response.status===409&&value.reason_code==='launch_request_conflict')throw new LaunchFailure('conflict');
        if(response.status===409&&value.reason_code==='launch_slot_busy')throw new LaunchFailure('busy');
        throw new LaunchFailure(response.status===422?'invalid_request':'unavailable');
      }
      const raw=await boundedJSON(response,262144);if(controller.signal.aborted)throw new LaunchFailure('unavailable');
      try{return decodeSuccessor('receipt',raw);}catch{throw new LaunchFailure('invalid_response');}
    }catch(error){throw error instanceof LaunchFailure?error:new LaunchFailure('unavailable');}
    finally{clearTimeout(timer);signal.removeEventListener('abort',abort);}
  }
  async submit(command:SuccessorSubmission,signal:AbortSignal){return command.verify(await this.request('',signal,command.body));}
  async receipt(command:SuccessorSubmission,signal:AbortSignal,previous?:SuccessorLaunchReceipt){
    // Without any reply, use the approved authenticated identity read. Never invent Python's canonical digest.
    const result=await this.request(previous?'/receipts/query':'/'+encodeURIComponent(command.request.identity.command_id),signal,
      previous?JSON.stringify(command.query(previous)):undefined);
    return command.verify(result,previous);
  }
}
