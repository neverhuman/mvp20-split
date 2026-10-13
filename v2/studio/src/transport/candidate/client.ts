import {decodeCandidate,type CandidateReference} from '../../contracts/candidate.js';
import {ScientificHTTP} from '../scientific/http.js';
import {requireReply,same} from '../scientific/identity.js';

/** Existing owner reads only. Data content access is checked independently. */
export class CandidateClient {
 private readonly http:ScientificHTTP;
 constructor(fetcher:typeof fetch=fetch,timeoutMs=15_000){this.http=new ScientificHTTP(fetcher,timeoutMs);}
 async candidate(reference:CandidateReference,signal:AbortSignal){
  const expected=structuredClone(reference);
  const result=await this.http.post('/api/research/v1/candidates/read',expected,value=>decodeCandidate('candidate',value),signal);
  requireReply(same(result.reference,expected));
  return result;
 }
 async producer(run:string,completion:string,signal:AbortSignal){
  const result=await this.http.get(`/api/runtime/v1/runs/${encodeURIComponent(run)}/completions/${encodeURIComponent(completion)}/producer`,value=>decodeCandidate('producer',value),signal);
  requireReply(result.completion.run_id===run&&result.completion.completion_id===completion);
  return result;
 }
}
