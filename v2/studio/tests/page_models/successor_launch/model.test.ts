import test from 'node:test';
import assert from 'node:assert/strict';
import {SuccessorLaunchModel} from '../../../src/page_models/successor_launch/model.js';
import {SuccessorJournal} from '../../../src/page_models/successor_launch/journal.js';
import {LaunchFailure} from '../../../src/transport/launch/client.js';
import {successorCommand,successorReceipt} from '../../fixtures/successor_launch.js';
function fixture(){
  const values=new Map<string,string>(),command=successorCommand(),receipt=successorReceipt(command);
  const storage={getItem:(key:string)=>values.get(key)??null,setItem:(key:string,value:string)=>{values.set(key,value);}};
  const journal=new SuccessorJournal({actor_id:'owner',scope:command.request.identity.scope,run_id:'parent',curation_id:'curation-original'},storage);
  return {values,command,receipt,storage,journal};
}

test('lost reply reload reads original identity and then preserves owner hash without another intake',async()=>{
  const f=fixture();let posts=0,reads=0;
  const source={submit:async(command:typeof f.command)=>{posts++;assert.equal(f.journal.load()?.command.body,command.body);throw new LaunchFailure('unavailable');},
    receipt:async(command:typeof f.command,_signal:AbortSignal,previous?:typeof f.receipt)=>{reads++;assert.equal(command.body,f.command.body);assert.equal(previous?.request_sha256,reads===1?undefined:f.receipt.request_sha256);return f.receipt;}};
  const first=new SuccessorLaunchModel(source,f.journal);first.initialize();await first.submit(f.command);assert.equal(first.snapshot.phase,'unresolved');first.dispose();
  const restored=new SuccessorLaunchModel(source,f.journal);restored.initialize();assert.equal(restored.snapshot.receipt,null);await restored.reconcile();await restored.reconcile();
  assert.equal(restored.snapshot.phase,'ready');assert.equal(posts,1);assert.equal(reads,2);assert.equal(restored.canSubmit,false);
});

test('double clicks and different stored originals cannot create another launch',async()=>{
  const f=fixture();let finish!:(value:typeof f.receipt)=>void;
  const model=new SuccessorLaunchModel({submit:async()=>new Promise(resolve=>{finish=resolve;}),receipt:async()=>f.receipt},f.journal);
  model.initialize();const pending=model.submit(f.command);
  assert.throws(()=>model.submit(successorCommand('another')),/not_available/);
  assert.throws(()=>f.journal.save(successorCommand('another')),/pending/);finish(f.receipt);await pending;
});

test('reentrant denial stops dispatch and late replies after suspension stay hidden',async()=>{
  const f=fixture();let calls=0;
  const denied=new SuccessorLaunchModel({submit:async()=>{calls++;return f.receipt;},receipt:async()=>f.receipt},f.journal);
  denied.initialize();denied.subscribe(()=>{if(denied.snapshot.phase==='submitting')denied.deny();});await denied.submit(f.command);assert.equal(calls,0);
  let resolve!:(value:typeof f.receipt)=>void;
  const model=new SuccessorLaunchModel({submit:async()=>f.receipt,receipt:async()=>new Promise(done=>{resolve=done;})},f.journal);
  model.initialize();const pending=model.reconcile();model.suspend();resolve(f.receipt);await pending;assert.equal(model.snapshot.phase,'restoring');assert.equal(model.snapshot.receipt,null);
});

test('storage failure prevents posting and live denial clears protected launch state',async()=>{
  const f=fixture();let posts=0;
  f.storage.setItem=()=>{throw Error('quota');};
  const blocked=new SuccessorLaunchModel({submit:async()=>{posts++;return f.receipt;},receipt:async()=>f.receipt},f.journal);
  blocked.initialize();await blocked.submit(f.command);assert.equal(blocked.snapshot.phase,'storage_failed');assert.equal(posts,0);
  const other=fixture();other.journal.save(other.command,other.receipt);
  const denied=new SuccessorLaunchModel({submit:async()=>other.receipt,receipt:async()=>{throw new LaunchFailure('denied');}},other.journal);
  denied.initialize();await denied.reconcile();assert.equal(denied.snapshot.phase,'denied');assert.equal(denied.submission,undefined);assert.equal(denied.snapshot.receipt,null);
});
