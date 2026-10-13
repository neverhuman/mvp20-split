import {test} from 'node:test';
import assert from 'node:assert/strict';
import {CandidateClient} from '../../../src/transport/candidate/client.js';
import {allowedRoute} from '../../../src/transport/scientific/routes.js';
import {fixture} from '../../page_models/candidate_inspector/fixture.js';
const reply=(value:unknown)=>new Response(JSON.stringify(value),{headers:{'content-type':'application/json'}});
test('candidate client uses exact same-origin read routes and current session',async()=>{
 const f=fixture(),seen:string[]=[];
 const client=new CandidateClient(async(path,options)=>{seen.push(String(path));assert.equal(options?.credentials,'same-origin');assert.equal(options?.redirect,'error');return reply(String(path).endsWith('/read')?f.candidate:f.proof);});
 const signal=new AbortController().signal;
 assert.deepEqual(await client.candidate(f.result.candidate,signal),f.candidate);
 assert.deepEqual(await client.producer('run-1','completion-1',signal),f.proof);
 assert.deepEqual(seen,['/api/research/v1/candidates/read','/api/runtime/v1/runs/run-1/completions/completion-1/producer']);
});
test('candidate routes do not admit writes, foreign origins, ambiguous escaping or adjacent paths',()=>{
 for(const path of ['/api/research/v1/candidates','https://evil.test/api/research/v1/candidates/read','/api/research/v1/candidates/read?scope=other'])assert.equal(allowedRoute('POST',path),false);
 for(const path of ['/api/runtime/v1/runs/r/completions/c/producer/extra','/api/runtime/v1/runs/%2E%2E/completions/c/producer','/api/runtime/v1/runs/r/completions/c/producer?other=1'])assert.equal(allowedRoute('GET',path),false);
});
test('wrong candidate and producer identities fail before consumers receive data',async()=>{
 const f=fixture(),signal=new AbortController().signal;
 f.candidate.reference={...f.candidate.reference,candidate_id:'other'};
 const client=new CandidateClient(async path=>reply(String(path).endsWith('/read')?f.candidate:f.proof));
 await assert.rejects(()=>client.candidate(f.result.candidate,signal));
 await assert.rejects(()=>client.producer('wrong-run','completion-1',signal));
});
