import { test } from 'node:test';
import assert from 'node:assert/strict';
import { decodeContext, SessionClient, SessionFailure } from '../../src/transport/session/client.js';

const context = { actor_id:'operator', scope:{tenant_id:'demo',project_id:'demo'}, run_id:null, synthetic:true };
test('session context rejects extra authority and malformed identifiers', () => {
  assert.deepEqual(decodeContext(context), context);
  assert.throws(() => decodeContext({...context, token:'secret'}), SessionFailure);
  assert.throws(() => decodeContext({...context, run_id:'../../secret'}), SessionFailure);
  assert.throws(() => decodeContext({...context, scope:{tenant_id:'demo'}}), SessionFailure);
});
test('session transport only exchanges a ticket through bounded same-origin JSON', async () => {
  const calls: RequestInit[] = [];
  const client = new SessionClient((async (path, options) => {
    assert.equal(path,'/session'); calls.push(options!);
    return new Response(JSON.stringify(context),{headers:{'content-type':'application/json'}});
  }) as typeof fetch);
  await client.open('ticket'); await client.open();
  assert.equal(calls[0]!.method,'POST'); assert.equal(calls[0]!.credentials,'same-origin');
  assert.equal(calls[0]!.body,JSON.stringify({ticket:'ticket'}));
  assert.equal(calls[1]!.method,'GET');
  const denied = new SessionClient((async () => new Response('private diagnostics',{status:403})) as typeof fetch);
  await assert.rejects(denied.open(), (error: unknown) => error instanceof SessionFailure && error.kind === 'denied');
});
