import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import type { CurationRequest } from '../../../src/contracts/campaign_curation.js';
import { CurationRequestModel } from '../../../src/page_models/campaign_curation/request.js';
import { CurationJournal } from '../../../src/page_models/campaign_curation/journal.js';
import { CurationSubmission } from '../../../src/transport/campaign_curation/submission.js';
import { CurationCommandFailure } from '../../../src/transport/campaign_curation/commands.js';
const request=JSON.parse(readFileSync('tests/fixtures/campaign_curation/commands.json','utf8'))[0].request as CurationRequest;
const context={actor_id:request.identity.actor_id,scope:request.identity.scope,run_id:request.payload.context.predecessor.run_id};
function receipt(command:CurationSubmission){return {wire_version:'1' as const,identity:command.request.identity,request_sha256:command.sha256,
  reference:command.selection.reference,revision:0,phase:'queued' as const,reason_code:null,created_at:'2026-10-12T00:00:00Z',updated_at:'2026-10-12T00:00:00Z'};}
function setup(){
  const values=new Map<string,string>(),calls:string[]=[];
  const storage={getItem:(key:string)=>values.get(key)??null,setItem:(key:string,value:string)=>{values.set(key,value);}};
  const journal=new CurationJournal(context,storage);
  const source={submit:async(command:CurationSubmission)=>{assert.equal((await journal.load())?.command.body,command.body);calls.push(command.body);return receipt(command);},
    receipt:async(command:CurationSubmission)=>{calls.push('query');return receipt(command);}};
  return {values,storage,journal,calls,source,model:new CurationRequestModel(source,journal)};
}
test('durable original precedes POST and accepted receipt is not model progress',async()=>{
  const f=setup();await f.model.initialize();assert.equal(f.model.canSubmit,true);
  await f.model.submit(request);assert.equal(f.model.snapshot.phase,'accepted');assert.equal(f.calls.length,1);
  assert.equal(f.model.snapshot.receipt?.phase,'queued');assert.equal(f.model.canSubmit,false);
  assert.equal(f.model.submission?.selection.predecessor,context.run_id);
});
test('reload hides cached acceptance until original receipt query verifies it',async()=>{
  const f=setup();await f.model.initialize();await f.model.submit(request);
  const replacement=new CurationRequestModel(f.source,f.journal);await replacement.initialize();
  assert.equal(replacement.snapshot.phase,'unresolved');assert.equal(replacement.snapshot.receipt,null);assert.equal(replacement.submission,undefined);
  await replacement.reconcile();assert.equal(replacement.snapshot.phase,'accepted');assert.equal(f.calls.length,2);assert.equal(f.calls[1],'query');
});
test('lost reply and missing receipt preserve exact original retry bytes',async()=>{
  const f=setup();let accepted=false;
  const model=new CurationRequestModel({submit:async command=>{f.calls.push(command.body);if(!accepted)throw new CurationCommandFailure('unavailable');return receipt(command);},
    receipt:async()=>{throw new CurationCommandFailure('missing');}},f.journal);
  await model.initialize();await model.submit(request);assert.equal(model.snapshot.phase,'unresolved');
  await model.reconcile();assert.equal(model.snapshot.reason,'missing');assert.equal(f.calls.length,1);
  accepted=true;await model.retryOriginal();assert.equal(model.snapshot.phase,'accepted');assert.equal(f.calls[0],f.calls[1]);
});
test('storage failure prevents provider-triggering intake',async()=>{
  const f=setup();const journal=new CurationJournal(context,{getItem:()=>null,setItem:()=>{throw Error('full');}});
  const model=new CurationRequestModel(f.source,journal);await model.initialize();await model.submit(request);
  assert.equal(model.snapshot.phase,'storage_failed');assert.deepEqual(f.calls,[]);
});
test('a different pending original and foreign restored scope cannot be overwritten',async()=>{
  const f=setup();const first=await CurationSubmission.create(request);await f.journal.save(first);
  const changed=structuredClone(request);changed.identity.command_id='other';
  await assert.rejects(()=>CurationSubmission.create(changed).then(command=>f.journal.save(command)),/pending/);
  const foreign=new CurationJournal({...context,actor_id:'foreign'},{getItem:()=>[...f.values.values()][0]!,setItem:()=>{}});
  await assert.rejects(()=>foreign.load(),/scope/);
});
test('conflict is not an invitation to automatically submit again',async()=>{
  const f=setup();const model=new CurationRequestModel({...f.source,submit:async()=>{throw new CurationCommandFailure('conflict');}},f.journal);
  await model.initialize();await model.submit(request);assert.equal(model.snapshot.phase,'conflict');assert.equal(model.canReconcile,false);assert.equal(model.canSubmit,false);
});
test('double click during command preparation cannot mint another identity',async()=>{
  const f=setup();await f.model.initialize();const pending=f.model.submit(request);
  await assert.rejects(()=>f.model.submit(request),/not_available/);await pending;assert.equal(f.calls.length,1);
});
test('reentrant denial before transmission prevents a POST',async()=>{
  const f=setup();await f.model.initialize();f.model.subscribe(()=>{if(f.model.snapshot.phase==='submitting')f.model.deny();});
  await f.model.submit(request);assert.equal(f.model.snapshot.phase,'denied');assert.deepEqual(f.calls,[]);
});
test('late acknowledgement cannot restore denied or disposed content',async()=>{
  for(const action of ['deny','dispose'] as const){
    const f=setup();let release:(()=>void)|undefined;
    const model=new CurationRequestModel({...f.source,submit:async command=>{await new Promise<void>(resolve=>{release=resolve;});return receipt(command);}},f.journal);
    await model.initialize();const pending=model.submit(request);
    while(!release)await new Promise(resolve=>setTimeout(resolve,1));
    model[action]();release();await pending;
    assert.equal(model.snapshot.receipt,null);assert.equal(model.submission,undefined);assert.equal(model.canReconcile,false);
  }
});
