import { test } from 'node:test';
import assert from 'node:assert/strict';
import type { CapabilityRequestView, CurationView } from '../../../src/contracts/campaign_curation.js';
import { CurationModel } from '../../../src/page_models/campaign_curation/model.js';
import { ScientificReadFailure } from '../../../src/transport/scientific/failure.js';
import { fixture, fulfilled } from '../../transport/campaign_curation/fixtures.js';

function deferred<T>() { let resolve!: (value: T) => void; const promise = new Promise<T>(done => { resolve = done; }); return { promise, resolve }; }
function setup() {
  const f = fixture(), calls = { roots: 0, details: 0 };
  const source = { async curation() { calls.roots++; return f.curation; }, async capability() { calls.details++; return f.capability; } };
  const model = new CurationModel(source);
  return { f, calls, source, model };
}

test('one original curation loads and capability detail is lazy and immutable', async () => {
  const { f, calls, model } = setup();
  await model.select(f.selection);
  assert.equal(model.snapshot.phase, 'ready'); assert.equal(calls.details, 0);
  assert.equal(model.snapshot.record!.status, 'Additional tools needed');
  assert.equal(model.snapshot.record!.requests[0]!.purpose, f.capability.gap.purpose);
  await model.inspect(0);
  assert.equal(calls.details, 1); assert.equal(model.snapshot.detail.record!.fulfillmentStatus, 'Not yet supplied');
  assert.throws(() => { model.snapshot.record!.data.specification.direction = 'changed'; }, TypeError);
  f.curation.specification.direction = 'caller changed';
  assert.notEqual(model.snapshot.record!.data.specification.direction, f.curation.specification.direction);
  await model.inspect(999); assert.equal(calls.details, 1);
});

test('visible refresh preserves selected detail and reads only the scoped region', async () => {
  const { f, model, calls } = setup();
  await model.select(f.selection); await model.inspect(0); await model.refresh();
  assert.deepEqual(calls, { roots: 2, details: 2 });
  assert.equal(model.snapshot.detail.index, 0); assert.equal(model.snapshot.detail.phase, 'ready');
});

test('root context replacement fences an uncancellable original response', async () => {
  const f = fixture(), pending = deferred<CurationView | null>();
  const model = new CurationModel({ curation: () => pending.promise, capability: async () => f.capability });
  const request = model.select(f.selection);
  await model.select(null); pending.resolve(f.curation); await request;
  assert.equal(model.snapshot.phase, 'idle'); assert.equal(model.snapshot.record, null);
});

test('hiding cancels both lanes; returning re-reads the selected reference', async () => {
  const { f, model, source, calls } = setup();
  await model.select(f.selection);
  const pending = deferred<CapabilityRequestView>();
  source.capability = () => pending.promise;
  const detail = model.inspect(0); await model.setVisible(false);
  pending.resolve(f.capability); await detail;
  assert.equal(model.snapshot.phase, 'hidden'); assert.equal(model.snapshot.record, null); assert.equal(model.snapshot.detail.record, null);
  source.capability = async () => f.capability;
  await model.setVisible(true);
  assert.equal(calls.roots, 2); assert.equal(model.snapshot.detail.phase, 'ready');
});

test('reentrant hiding or disposal prevents starting obsolete reads', async () => {
  const { f, model, calls } = setup();
  model.subscribe(() => { if (model.snapshot.phase === 'loading') void model.setVisible(false); });
  await model.select(f.selection); assert.equal(calls.roots, 0);
  const other = setup(); await other.model.select(other.f.selection);
  other.model.subscribe(() => { if (other.model.snapshot.detail.phase === 'loading') other.model.dispose(); });
  await other.model.inspect(0); assert.equal(other.calls.details, 0); assert.equal(other.model.snapshot.record, null);
});

test('denial clears root/detail state while ordinary detail failures preserve the original', async () => {
  const { f, model, source } = setup();
  await model.select(f.selection); await model.inspect(0);
  source.capability = async () => { throw new ScientificReadFailure('unavailable'); };
  await model.inspect(0);
  assert.equal(model.snapshot.phase, 'ready'); assert.equal(model.snapshot.detail.phase, 'failed'); assert.equal(model.snapshot.detail.record, null);
  source.capability = async () => { throw new ScientificReadFailure('denied'); };
  await model.inspect(0);
  assert.equal(model.snapshot.phase, 'denied'); assert.equal(model.snapshot.record, null); assert.equal(model.snapshot.detail.record, null);
});

test('root denial and caller invalidation cannot leave stale protected records', async () => {
  const { f, model, source } = setup(); await model.select(f.selection); await model.inspect(0);
  model.invalidate(); assert.equal(model.snapshot.phase, 'stale'); assert.equal(model.snapshot.record, null);
  source.curation = async () => { throw new ScientificReadFailure('denied'); };
  await model.refresh(); assert.equal(model.snapshot.phase, 'denied'); assert.equal(model.snapshot.detail.record, null);
});

test('changed original input or proposal and regressed revision reject on refresh', async () => {
  for (const fault of ['direction', 'proposal', 'revision', 'provider']) {
    const { f, model } = setup(); await model.select(f.selection);
    if (fault === 'direction') f.curation.specification.direction = 'changed';
    if (fault === 'proposal') f.curation.proposal!.rationale = 'rewritten';
    if (fault === 'revision') f.curation.receipt.revision--;
    if (fault === 'provider') f.curation.provider!.output_sha256 = 'f'.repeat(64);
    await model.refresh(); assert.equal(model.snapshot.phase, 'failed'); assert.equal(model.snapshot.reason, 'invalid_response');
    assert.equal(model.snapshot.record, null);
  }
});

test('known missing records differ from read failure and from empty selection', async () => {
  const f = fixture();
  const model = new CurationModel({ curation: async () => null, capability: async () => null });
  await model.select(f.selection); assert.equal(model.snapshot.phase, 'missing');
  await model.select(null); assert.equal(model.snapshot.phase, 'idle');
  const detail = new CurationModel({ curation: async () => f.curation, capability: async () => null });
  await detail.select(f.selection); await detail.inspect(0);
  assert.equal(detail.snapshot.phase, 'ready'); assert.equal(detail.snapshot.detail.phase, 'missing');
});

test('historical verified winner and proposal identity cannot be replaced on detail refresh', async () => {
  for (const fault of ['proposal', 'winner']) {
    const f = fulfilled();
    const model = new CurationModel({ curation: async () => f.curation, capability: async () => f.capability });
    await model.select(f.selection); await model.inspect(0);
    assert.equal(model.snapshot.detail.record!.fulfillmentStatus, 'Fulfillment evidence verified');
    if (fault === 'proposal') f.capability.proposal_sha256 = 'f'.repeat(64);
    else f.capability.fulfillment!.identity.command_id = 'new-winner';
    await model.inspect(0);
    assert.equal(model.snapshot.detail.phase, 'failed'); assert.equal(model.snapshot.detail.record, null);
  }
});

test('an original pending receipt can progress to verification without implying campaign admission', async () => {
  const f = fulfilled('pending'); let capability = f.capability;
  const model = new CurationModel({ curation: async () => f.curation, capability: async () => capability });
  await model.select(f.selection); await model.inspect(0);
  assert.equal(model.snapshot.detail.record!.fulfillmentStatus, 'Evidence review pending');
  capability = fulfilled('verified').capability;
  await model.inspect(0);
  assert.equal(model.snapshot.detail.phase, 'ready');
  assert.equal(model.snapshot.record!.data.validated_draft, null);
});

test('disposal clears content and blocks all later operations', async () => {
  const { f, calls, model } = setup(); await model.select(f.selection);
  model.dispose(); await model.refresh(); await model.inspect(0); await model.select(f.selection);
  assert.equal(model.snapshot.phase, 'idle'); assert.equal(model.snapshot.record, null); assert.equal(calls.roots, 1);
});

test('reentrant detail selection during refresh does not start a duplicate read', async () => {
  const { f, model, calls } = setup(); await model.select(f.selection); await model.inspect(0);
  model.subscribe(() => { if (model.snapshot.phase === 'ready' && model.snapshot.detail.phase === 'idle') void model.inspect(0); });
  await model.refresh(); await Promise.resolve();
  assert.deepEqual(calls, { roots: 2, details: 2 });
});

test('nonterminal progress can advance but a terminal original cannot restart itself', async () => {
  const { f, model } = setup();
  const original = structuredClone(f.curation);
  f.curation.receipt.phase = 'queued'; f.curation.receipt.revision = 0;
  f.curation.provider = null; f.curation.proposal = null; f.curation.capability_requests = [];
  await model.select(f.selection);
  f.curation.receipt.phase = 'assembling'; f.curation.receipt.revision = 1;
  await model.refresh(); assert.equal(model.snapshot.phase, 'ready');
  Object.assign(f.curation, original);
  await model.refresh(); assert.equal(model.snapshot.record!.status, 'Additional tools needed');
  f.curation.receipt.revision++; f.curation.receipt.phase = 'compiling';
  await model.refresh(); assert.equal(model.snapshot.phase, 'failed');
});
