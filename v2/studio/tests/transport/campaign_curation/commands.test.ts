import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { CurationSubmission } from '../../../src/transport/campaign_curation/submission.js';
import { CurationCommands } from '../../../src/transport/campaign_curation/commands.js';
import type { CurationRequest } from '../../../src/contracts/campaign_curation.js';
const vectors=JSON.parse(readFileSync('tests/fixtures/campaign_curation/commands.json','utf8')) as {
  request:CurationRequest;canonical:string;sha256:string;curation_id:string}[];
function receipt(command:CurationSubmission) {return {wire_version:'1',identity:command.request.identity,
  request_sha256:command.sha256,reference:command.selection.reference,revision:0,phase:'queued',reason_code:null,
  created_at:'2026-10-12T00:00:00Z',updated_at:'2026-10-12T00:00:00Z'};}
test('original command and identity fingerprints match Python-owned canonical vectors including Unicode',async()=>{
  for(const vector of vectors) {
    const command=await CurationSubmission.create(vector.request);
    assert.equal(command.body,vector.canonical);assert.equal(command.sha256,vector.sha256);assert.equal(command.curationId,vector.curation_id);
    assert.deepEqual(await CurationSubmission.restore(command.body),command);
    assert.deepEqual(command.verify(receipt(command)),receipt(command));
  }
});
test('malformed originals cannot change scope, duplicate pins or restored bytes',async()=>{
  for(const mutate of [(r:CurationRequest)=>{r.payload.context.draft.scope.project_id='other';},
    (r:CurationRequest)=>{r.payload.direction='   ';},(r:CurationRequest)=>{r.payload.direction='\ud800';},
    (r:CurationRequest)=>{r.identity.command_family='other';}]) {
    const request=structuredClone(vectors[0]!.request);mutate(request);
    await assert.rejects(()=>CurationSubmission.create(request));
  }
  await assert.rejects(()=>CurationSubmission.restore(' '+vectors[0]!.canonical));
  const command=await CurationSubmission.create(vectors[0]!.request);
  for(const changed of [{request_sha256:'0'.repeat(64)},{phase:'ready',revision:1},{reference:{...command.selection.reference,curation_id:'curation-'+'f'.repeat(64)}}])
    assert.throws(()=>command.verify({...receipt(command),...changed}));
});
test('submission and read-only recovery query use same identity without retry',async()=>{
  const command=await CurationSubmission.create(vectors[0]!.request),calls:{path:string;options:RequestInit}[]=[];
  const source=new CurationCommands((async(path,options)=>{calls.push({path:String(path),options:options!});return Response.json(receipt(command));}) as typeof fetch);
  await source.submit(command,new AbortController().signal);await source.receipt(command,new AbortController().signal);
  assert.equal(calls.length,2);assert.equal(calls[0]!.options.body,command.body);
  assert.equal(calls[1]!.path,'/api/planning/v1/campaign-curations/receipts/query');
  assert.deepEqual(JSON.parse(calls[1]!.options.body as string),command.query);
  assert.equal(calls[0]!.options.credentials,'same-origin');assert.equal(calls[0]!.options.redirect,'error');
});
test('named absence is distinct from outage, conflicts and foreign receipts',async()=>{
  const command=await CurationSubmission.create(vectors[0]!.request);
  for(const [status,value,kind] of [[404,{reason_code:'curation_receipt_not_recorded'},'missing'],
    [404,{},'unavailable'],[409,{reason_code:'curation_receipt_conflict'},'conflict'],[403,{},'denied'],
    [200,{...receipt(command),request_sha256:'f'.repeat(64)},'invalid_response']] as const) {
    let calls=0;const source=new CurationCommands((async()=>{calls++;return Response.json(value,{status});}) as typeof fetch);
    await assert.rejects(()=>source.receipt(command,new AbortController().signal),{kind});assert.equal(calls,1);
  }
});
test('uncancellable late command reply cannot escape cancellation',async()=>{
  const command=await CurationSubmission.create(vectors[0]!.request);const controller=new AbortController();
  const source=new CurationCommands((async()=>{controller.abort();return Response.json(receipt(command));}) as typeof fetch);
  await assert.rejects(()=>source.submit(command,controller.signal),{kind:'unavailable'});
});
