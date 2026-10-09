import { test } from "node:test";
import assert from "node:assert/strict";
import { CampaignLaunch } from "../../../src/page_models/launch/model.js";
import { LaunchJournal } from "../../../src/page_models/launch/journal.js";
import { LaunchFailure } from "../../../src/transport/launch/client.js";
import { admission, command, context, profile, receipt, storage } from "../../fixtures/launch.js";

test("persist before POST; refresh reads the original receipt without duplicate launch", async () => {
  const store = storage(), journal = new LaunchJournal(context, store); let posts = 0, reads = 0;
  const source = { submit: async () => { posts++; assert.equal(journal.load()?.command.body, command().body); throw new LaunchFailure("unavailable"); },
    receipt: async (cmd: ReturnType<typeof command>) => { reads++; return receipt(cmd, true); } };
  const first = new CampaignLaunch(source, journal);
  await first.requestLaunch(admission(), profile);
  assert.equal(first.snapshot.phase, "unresolved"); assert.equal(first.canRequest, false); first.dispose();
  const restored = new CampaignLaunch(source, journal);
  assert.equal(Boolean(restored.snapshot.receipt), false); await restored.reconcile();
  assert.equal(restored.snapshot.receipt?.run_id, "actual-run"); assert.equal(restored.snapshot.receipt?.phase, "admitted_not_engaged");
  assert.equal(posts, 1); assert.equal(reads, 1);
});

test("missing receipt permits only deliberate original-byte retry", async () => {
  const journal = new LaunchJournal(context, storage()); journal.save(command());
  const bodies: string[] = [];
  const model = new CampaignLaunch({ submit: async cmd => { bodies.push(cmd.body); return receipt(cmd); },
    receipt: async () => { throw new LaunchFailure("missing"); } }, journal);
  await model.reconcile(); assert.equal(model.snapshot.reason, "missing");
  assert.throws(() => model.requestLaunch(admission("replacement"), profile));
  await model.retryOriginal(); assert.deepEqual(bodies, [command().body]);
  assert.equal(model.canRequest, false);
});

test("durable state failure or pending cross-tab identity prevents any POST", async () => {
  let posts = 0;
  const source = { submit: async () => { posts++; return receipt(); }, receipt: async () => receipt() };
  const store = storage(), journal = new LaunchJournal(context, store), model = new CampaignLaunch(source, journal);
  journal.save(command());
  await model.requestLaunch(admission("competing"), profile);
  assert.equal(model.snapshot.phase, "storage_failed"); assert.equal(posts, 0);
  const broken = new CampaignLaunch(source, new LaunchJournal(context, { getItem: () => null, setItem: () => { throw new Error("quota"); } }));
  await broken.requestLaunch(admission(), profile); assert.equal(broken.snapshot.phase, "storage_failed"); assert.equal(posts, 0);
});

test("denial and disposal fence late receipt responses", async () => {
  let resolve!: (value: ReturnType<typeof receipt>) => void;
  const model = new CampaignLaunch({ submit: async () => new Promise(done => { resolve = done; }), receipt: async () => receipt() },
    new LaunchJournal(context, storage()));
  const pending = model.requestLaunch(admission(), profile); model.deny(); resolve(receipt(command(), true)); await pending;
  assert.equal(model.snapshot.phase, "denied"); assert.equal(model.snapshot.receipt, null); assert.equal(model.canReconcile, false);
});

test("identity conflict cannot adopt a receipt or issue another request", async () => {
  const model = new CampaignLaunch({ submit: async () => { throw new LaunchFailure("conflict"); }, receipt: async () => receipt() },
    new LaunchJournal(context, storage()));
  await model.requestLaunch(admission(), profile);
  assert.equal(model.snapshot.phase, "conflict"); assert.throws(() => model.reconcile()); assert.throws(() => model.retryOriginal());
});

test("restored cached run is hidden until live validation; changed admission remains unresolved", async () => {
  const journal = new LaunchJournal(context, storage()); journal.save(command(), receipt(command(), true));
  const changed = receipt(command(), true); changed.admission!.outcome.binding.operation_id = "different-op";
  const model = new CampaignLaunch({ submit: async () => changed, receipt: async () => changed }, journal);
  assert.equal(model.snapshot.receipt, null); await model.reconcile();
  assert.equal(model.snapshot.phase, "unresolved"); assert.equal(model.snapshot.receipt, null);
});

test("only a live released receipt permits a deliberately new campaign", async () => {
  const journal = new LaunchJournal(context, storage());
  const released = receipt(command(), true); released.phase = "released";
  journal.save(command(), released);
  const model = new CampaignLaunch({ submit: async cmd => receipt(cmd), receipt: async () => released }, journal);
  assert.equal(model.canRequest, false); await model.reconcile(); assert.equal(model.canRequest, true);
  await model.requestLaunch(admission("next-campaign"), profile);
  assert.equal(journal.load()?.command.request.identity.command_id, "next-campaign");
});

test("recovery replays the same admitted request and never creates a new campaign identity", async () => {
  const journal = new LaunchJournal(context, storage()); let calls = 0;
  const held = receipt(command(), true); held.phase = "recovery_required";
  journal.save(command(), held);
  const model = new CampaignLaunch({ receipt: async () => held, submit: async cmd => {
    calls++; assert.equal(cmd.body, command().body); return { ...receipt(cmd, true), revision: 4 };
  } }, journal);
  await model.reconcile(); assert.equal(model.canRequest, false);
  await model.retryOriginal(); assert.equal(calls, 1); assert.equal(model.snapshot.receipt?.run_id, "actual-run");
});

test("corrupt or foreign recovery state blocks instead of silently starting over", () => {
  const store = storage(), journal = new LaunchJournal(context, store); journal.save(command());
  const key = [...store.records.keys()][0]!;
  store.records.set(key, "{");
  const model = new CampaignLaunch({ submit: async () => receipt(), receipt: async () => receipt() }, journal);
  assert.equal(model.snapshot.phase, "storage_failed"); assert.equal(model.canRequest, false);
  assert.throws(() => new LaunchJournal({ ...context, actor_id: "other" }, storage()).save(command()));
});
