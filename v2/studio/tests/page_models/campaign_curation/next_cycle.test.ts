import test from 'node:test';
import assert from 'node:assert/strict';
import {CurationSubmission} from '../../../src/transport/campaign_curation/submission.js';
import {CurationJournal} from '../../../src/page_models/campaign_curation/journal.js';
import {CurationNextCycle} from '../../../src/page_models/campaign_curation/next_cycle.js';
import {RecordedCuration} from '../../../src/page_models/campaign_curation/records.js';
import {fixture} from '../../transport/campaign_curation/fixtures.js';

async function setup(){
  const f=fixture(),command=await CurationSubmission.create({encoding:'amphora-command-v2',identity:f.curation.receipt.identity,payload:f.curation.specification});
  f.curation.receipt={...f.curation.receipt,reference:command.selection.reference,request_sha256:command.sha256,phase:'failed',reason_code:'synthetic_failure'};
  f.curation.proposal=null;f.curation.provider=null;f.curation.capability_requests=[];f.curation.validated_draft=null;
  const record=new RecordedCuration(f.curation,command.selection),values=new Map<string,string>();
  const storage={getItem:(key:string)=>values.get(key)??null,setItem:(key:string,value:string)=>{values.set(key,value);}};
  const journal=new CurationJournal({actor_id:command.selection.actor,scope:f.scope,run_id:command.selection.predecessor},storage);
  await journal.save(command);return {...f,record,command,values,storage,journal};
}
test('explicit next-cycle preparation archives original intent and performs only a fresh read',async()=>{
  const f=await setup();let reads=0;
  const cycle=new CurationNextCycle({curation:async()=>{reads++;return f.curation;}},f.journal);
  await cycle.prepare(f.record);assert.equal(reads,1);assert.equal(await f.journal.load(),null);
  assert.equal([...f.values.keys()].filter(key=>key.includes(':original:')).length,1);
  assert.ok([...f.values.values()].some(value=>value.includes(JSON.stringify(f.command.body))));
  const next=await CurationSubmission.create({...f.command.request,identity:{...f.command.request.identity,command_id:'new-idea'}});
  await f.journal.save(next);assert.equal((await f.journal.load())?.command.curationId,next.curationId);
});
test('nonterminal, changed terminal, denial and archive failure preserve the original',async()=>{
  for(const variant of ['nonterminal','changed','denied','archive']){
    const f=await setup();
    if(variant==='nonterminal'){f.curation.receipt.phase='assembling';f.curation.receipt.reason_code=null;}
    const original=variant==='nonterminal'?new RecordedCuration(f.curation,f.command.selection):f.record;
    if(variant==='changed')f.curation.specification.direction='Changed original';
    if(variant==='archive')f.storage.setItem=()=>{throw Error('quota');};
    const cycle=new CurationNextCycle({curation:async()=>{if(variant==='denied')throw Error('denied');return f.curation;}},f.journal);
    await assert.rejects(cycle.prepare(original));assert.equal((await f.journal.load())?.command.body,f.command.body);
  }
});
test('disposing during live read cannot release the browser original',async()=>{
  const f=await setup();let resolve!:(value:typeof f.curation)=>void;
  const cycle=new CurationNextCycle({curation:async()=>new Promise(done=>{resolve=done;})},f.journal);
  const pending=cycle.prepare(f.record);cycle.dispose();resolve(f.curation);await assert.rejects(pending);
  assert.equal((await f.journal.load())?.command.body,f.command.body);
});
