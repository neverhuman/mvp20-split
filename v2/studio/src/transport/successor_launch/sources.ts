import {decodeSuccessor} from '../../contracts/successor_launch.js';
import {boundedJSON} from '../bounded_json.js';
import {LaunchFailure} from '../launch/client.js';

/** Bounded committed run-export discovery; no value payloads or guessed node activations. */
export class SuccessorSources{
  constructor(private readonly fetcher:typeof fetch=fetch,private readonly timeoutMs=15000){}
  async read(run:string,signal:AbortSignal){
    if(!/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(run))throw Error('invalid_successor_run');
    const controller=new AbortController(),abort=()=>controller.abort();signal.addEventListener('abort',abort,{once:true});
    if(signal.aborted)abort();const timer=setTimeout(abort,this.timeoutMs);
    try{
      if(controller.signal.aborted)throw new LaunchFailure('unavailable');
      const response=await this.fetcher.call(globalThis,'/api/runtime/v1/graph-runs/'+encodeURIComponent(run)+'/carry-sources',
        {method:'GET',signal:controller.signal,credentials:'same-origin',redirect:'error',headers:{Accept:'application/json'}});
      if(!response.ok){await response.body?.cancel();throw new LaunchFailure([401,403].includes(response.status)?'denied':response.status===404?'missing':'unavailable');}
      const raw=await boundedJSON(response,262144);if(controller.signal.aborted)throw new LaunchFailure('unavailable');
      const value=decodeSuccessor('sources',raw);
      if(value.predecessor.run_id!==run)throw new LaunchFailure('invalid_response');return value;
    }catch(error){throw error instanceof LaunchFailure?error:new LaunchFailure('invalid_response');}
    finally{clearTimeout(timer);signal.removeEventListener('abort',abort);}
  }
}
