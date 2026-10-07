import { test } from 'node:test';
import assert from 'node:assert/strict';
import { WorkspaceSession } from '../../src/page_models/session/model.js';
import type { WorkspaceContext } from '../../src/transport/session/client.js';
import { SessionFailure } from '../../src/transport/session/client.js';

test('late session response cannot restore authority after denial', async () => {
  let release!: (value: WorkspaceContext) => void;
  const pending = new Promise<WorkspaceContext>(resolve => {release=resolve;});
  let calls=0;
  const model = new WorkspaceSession({open:async () => { if (++calls===1) return pending; throw new SessionFailure('denied'); }});
  const first=model.open(); await model.open();
  release({actor_id:'operator',scope:{tenant_id:'demo',project_id:'demo'},run_id:null,synthetic:true});
  await first;
  assert.equal(model.snapshot.phase,'denied'); assert.equal(model.snapshot.context,null);
});
test('gateway failure leaves no stale workspace context', async () => {
  const model = new WorkspaceSession({open:async () => {throw new Error('private diagnostic');}});
  await model.open(); assert.equal(model.snapshot.phase,'failed'); assert.equal(model.snapshot.context,null);
});
