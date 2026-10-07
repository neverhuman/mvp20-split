import { test } from 'node:test';
import assert from 'node:assert/strict';
import { DraftLibrary } from '../../../src/page_models/design/library.js';
import { AuthoringFailure } from '../../../src/transport/authoring.js';
import type { AuthoringClient } from '../../../src/transport/authoring.js';
import type { DraftPage, DraftRevision } from '../../../src/contracts/authoring.js';
import { scope, revision } from '../../fixtures/authoring.js';

const second=(): DraftRevision => ({...revision(),head:{...revision().head,draft_id:'other',title:'Other draft'}});
const page=(): DraftPage => ({scope,drafts:[revision().head,second().head],next_after:null});
function fixture(overrides: Partial<AuthoringClient> = {}) {
  const unexpected=async (): Promise<never>=>{throw new Error('unexpected mutation or catalog call');};
  const source={drafts:async()=>page(),draft:async(id: string)=>id === 'draft' ? revision() : second(),
    submit:unexpected,receipt:unexpected,validation:unexpected,universe:unexpected,releases:unexpected,schema:unexpected,...overrides};
  return new DraftLibrary({actor_id:'researcher',scope},source);
}
function deferred<T>() { let resolve!: (value:T)=>void; const promise=new Promise<T>(yes=>{resolve=yes;}); return {promise,resolve}; }

test('library opens exact advertised revision and never writes while browsing',async()=>{
  const model=fixture(); await model.refresh(); await model.open('draft');
  assert.equal(model.snapshot.phase,'ready');
  assert.equal(model.editing?.commands.session.snapshot.base?.head.revision,1);
  await assert.rejects(model.open('not-loaded'),/not_in_loaded/);
  await model.open('other'); assert.equal(model.snapshot.selected,'other'); model.dispose();
});

test('dirty work is retained before switching and if edited during a pending read',async()=>{
  const pending=deferred<DraftRevision>();
  const model=fixture({draft:async id=>id === 'draft' ? revision() : pending.promise});
  await model.refresh(); await model.open('draft');
  const original=model.editing!;
  const next=model.open('other');
  original.commands.session.edit({...original.commands.session.snapshot.local,title:'Unsaved work'});
  pending.resolve(second()); await next;
  assert.equal(model.snapshot.phase,'retained'); assert.equal(model.editing,original);
  await model.open('other'); assert.equal(model.snapshot.selected,'draft');
  assert.equal(model.editing?.commands.session.snapshot.local.title,'Unsaved work'); model.dispose();
});

test('foreign pages and substituted draft heads cannot create editing authority',async()=>{
  const foreign=fixture({drafts:async()=>({...page(),scope:{...scope,project_id:'foreign'}})});
  await foreign.refresh(); assert.equal(foreign.snapshot.phase,'failed'); assert.equal(foreign.snapshot.page,null);
  foreign.dispose();
  const substituted=fixture({draft:async()=>({...revision(),head:{...revision().head,content_sha256:'f'.repeat(64)}})});
  await substituted.refresh(); await substituted.open('draft');
  assert.equal(substituted.snapshot.phase,'failed'); assert.equal(substituted.editing,null); substituted.dispose();
});

test('denial clears loaded heads and prevents late reads restoring an editor',async()=>{
  const pending=deferred<DraftRevision>(); let calls=0;
  const model=fixture({drafts:async()=>{if(calls++)throw new AuthoringFailure('denied',false);return page();},draft:async()=>pending.promise});
  await model.refresh(); const opening=model.open('draft'); await model.refresh();
  pending.resolve(revision()); await opening;
  assert.equal(model.snapshot.phase,'denied'); assert.equal(model.snapshot.page,null); assert.equal(model.editing,null);
  await model.refresh(); assert.equal(calls,2); model.dispose();
});

test('denial retains local work but disables existing command and catalog owners',async()=>{
  let calls=0; const model=fixture({drafts:async()=>{if(calls++)throw new AuthoringFailure('denied',false);return page();}});
  await model.refresh(); await model.open('draft'); const editor=model.editing!;
  editor.commands.session.edit({...editor.commands.session.snapshot.local,title:'Retained'});
  await model.refresh(); assert.equal(model.snapshot.page,null);
  assert.equal(editor.commands.session.snapshot.denied,true); assert.equal(editor.catalog.snapshot.phase,'denied');
  assert.equal(editor.commands.session.snapshot.local.title,'Retained'); model.dispose();
});

test('disposal and reentrant refresh cannot dispatch or restore stale work',async()=>{
  let reads=0; const model=fixture({drafts:async()=>{reads++;return page();}});
  model.subscribe(()=>{if(model.snapshot.phase === 'loading')model.dispose();});
  await model.refresh(); assert.equal(reads,0);
  const pending=deferred<DraftRevision>();const other=fixture({draft:async()=>pending.promise});
  await other.refresh();const opening=other.open('draft');other.dispose();pending.resolve(revision());await opening;
  assert.equal(other.editing,null);
});

test('empty and unavailable remain distinct from denied',async()=>{
  const empty=fixture({drafts:async()=>({...page(),drafts:[]})});await empty.refresh();assert.equal(empty.snapshot.phase,'empty');empty.dispose();
  const unavailable=fixture({drafts:async()=>{throw new AuthoringFailure('unavailable',false);}});await unavailable.refresh();assert.equal(unavailable.snapshot.phase,'unavailable');unavailable.dispose();
});

test('an unresolved original save prevents replacement even without local edits',async()=>{
  const model=fixture();await model.refresh();await model.open('draft');
  const editor=model.editing!;
  editor.commands.session.beginSave('original-save');
  await model.open('other');
  assert.equal(model.snapshot.phase,'retained');assert.equal(model.editing,editor);
  assert.equal(editor.commands.session.snapshot.pending?.identity.command_id,'original-save');
  model.dispose();
});
