import { test } from 'node:test';
import assert from 'node:assert/strict';
import { CurationClient } from '../../../src/transport/campaign_curation/client.js';
import { ScientificReadFailure } from '../../../src/transport/scientific/failure.js';
import { fixture, fulfilled } from './fixtures.js';

const signal = () => new AbortController().signal;
const json = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json' } });
const failure = (kind: string) => (error: unknown) => error instanceof ScientificReadFailure && error.kind === kind;

test('reads the original curation and selected gap without mutation or catalog fetch', async () => {
  const f = fixture(), paths: string[] = [];
  const client = new CurationClient(async (path, options) => {
    paths.push(String(path));
    assert.equal(options?.method, 'GET'); assert.equal(options?.body, undefined);
    assert.equal(options?.credentials, 'same-origin'); assert.equal(options?.redirect, 'error');
    return json(String(path).includes('capability-requests') ? f.capability : f.curation);
  });
  assert.deepEqual(await client.curation(f.selection, signal()), f.curation);
  assert.deepEqual(await client.capability(f.detail, signal()), f.capability);
  assert.equal(paths.length, 2);
  assert.notEqual(f.curation.provider!.output_sha256, f.capability.proposal_sha256);
});

test('named absence differs from outage, denial, malformed success and forged authority', async () => {
  const f = fixture();
  assert.equal(await new CurationClient(async () => json({ reason_code: 'curation_not_recorded' }, 404)).curation(f.selection, signal()), null);
  assert.equal(await new CurationClient(async () => json({ reason_code: 'capability_request_not_recorded' }, 404)).capability(f.detail, signal()), null);
  for (const [value, status, kind] of [[{}, 404, 'unavailable'], [{}, 403, 'denied'], [null, 200, 'invalid_response'],
    [{ ...f.curation, execute_now: true }, 200, 'invalid_response']] as const) {
    await assert.rejects(new CurationClient(async () => json(value, status)).curation(f.selection, signal()), failure(kind));
  }
});

test('foreign actor, predecessor, reference and provider linkage cannot be shown', async () => {
  const f = fixture();
  for (const field of ['actor', 'predecessor', 'curation', 'provider', 'gap']) {
    const value = structuredClone(f.curation);
    if (field === 'actor') value.receipt.identity.actor_id = 'other';
    if (field === 'predecessor') value.specification.context.predecessor.run_id = 'other';
    if (field === 'curation') value.receipt.reference.curation_id = 'curation-' + 'f'.repeat(64);
    if (field === 'provider') value.provider!.attempt.engagement.engagement_id = 'other';
    if (field === 'gap') value.capability_requests[0]!.request_id = 'capability-' + 'f'.repeat(64) + '-00';
    await assert.rejects(new CurationClient(async () => json(value)).curation(f.selection, signal()), failure('invalid_response'));
  }
});

test('unrelated gap and invented fulfilled flag reject independently of schema shape', async () => {
  const f = fixture();
  for (const field of ['gap', 'curation', 'fulfilled']) {
    const value = structuredClone(f.capability);
    if (field === 'gap') value.gap.purpose = 'Unrelated behavior';
    if (field === 'curation') value.curation.curation_id = 'curation-' + 'f'.repeat(64);
    if (field === 'fulfilled') value.status = 'fulfilled';
    await assert.rejects(new CurationClient(async () => json(value)).capability(f.detail, signal()), failure('invalid_response'));
  }
});

test('pre-aborted and invalid selections never make requests; late responses stay cancelled', async () => {
  const f = fixture(); let calls = 0;
  const client = new CurationClient(async () => { calls++; return json(f.curation); });
  const aborted = new AbortController(); aborted.abort();
  await assert.rejects(client.curation(f.selection, aborted.signal), failure('aborted'));
  await assert.rejects(client.curation({ ...f.selection, reference: { ...f.selection.reference, curation_id: '../other' } }, signal()), failure('invalid_request'));
  assert.equal(calls, 0);
  const controller = new AbortController();
  const late = new CurationClient(async () => { controller.abort(); return json(f.curation); });
  await assert.rejects(late.curation(f.selection, controller.signal), failure('aborted'));
});

test('oversized response and timed-out uncancellable peer cannot expose content', async () => {
  const f = fixture();
  const huge = new CurationClient(async () => new Response('x'.repeat(1048577), { headers: { 'Content-Type': 'application/json' } }));
  await assert.rejects(huge.curation(f.selection, signal()), failure('invalid_response'));
  const slow = new CurationClient(async () => { await new Promise(resolve => setTimeout(resolve, 15)); return json(f.curation); }, 1);
  await assert.rejects(slow.curation(f.selection, signal()), failure('timeout'));
});

test('fulfillment is bound to the original owner/request and scoped evidence', async () => {
  for (const status of ['pending', 'rejected', 'verified'] as const) {
    const f = fulfilled(status);
    assert.deepEqual(await new CurationClient(async () => json(f.capability)).capability(f.detail, signal()), f.capability);
  }
  const f = fulfilled();
  for (const fault of ['actor', 'request', 'evidence', 'reason']) {
    const value = structuredClone(f.capability);
    if (fault === 'actor') value.fulfillment!.identity.actor_id = 'foreign';
    if (fault === 'request') value.fulfillment!.specification.request.request_id = 'foreign';
    if (fault === 'evidence') value.fulfillment!.specification.acceptance_evidence[0]!.scope.project_id = 'foreign';
    if (fault === 'reason') value.fulfillment!.reason_code = 'capability_acceptance_unproven';
    await assert.rejects(new CurationClient(async () => json(value)).capability(f.detail, signal()), failure('invalid_response'));
  }
});
