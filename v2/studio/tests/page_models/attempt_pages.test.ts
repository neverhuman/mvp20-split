import { test } from "node:test";
import assert from "node:assert/strict";
import { MonitorModel } from "../../src/page_models/monitor.js";
import type { ObservationSource } from "../../src/transport/observations.js";
import { evidenceDetail, values } from "../fixtures/evidence.js";
import { snapshot, context, id, events, detail, deferred } from "../fixtures/observations.js";

const first = () => ({ ...evidenceDetail(), next_cursor: "next" });
const next = () => ({ ...evidenceDetail(), attempts: [{ ...evidenceDetail().attempts[0]!, attempt_id: "attempt-2", fence: 2 }] });
const source = (): ObservationSource => ({ snapshot: async () => snapshot(), detail: async (_run, _activation, _pin, cursor) => cursor ? next() : first(),
  values: async () => values(), events: async () => events([]) });
test("one detail loader replaces bounded attempt pages without duplicate membership", async () => {
  const peer = source(), model = new MonitorModel(peer); await model.open(context); await model.select(id(1)); await model.nextAttempts();
  assert.equal(model.snapshot.detail?.attempts[0]?.attempt_id, "attempt-2");
  assert.equal(model.snapshot.detail?.attempts.length, 1);
  await model.select(id(1)); peer.detail = async () => evidenceDetail(); await model.nextAttempts();
  assert.equal(model.snapshot.detailError?.kind, "invalid_response");
});
test("late attempt continuation cannot replace a newer selected activation", async () => {
  const peer = source(), model = new MonitorModel(peer); await model.open(context); await model.select(id(1));
  const held = deferred<ReturnType<typeof next>>(); peer.detail = async (_run, activation, _pin, cursor) => cursor ? held.promise : detail(2);
  const pending = model.nextAttempts(); await model.select(id(2)); held.resolve(next()); await pending;
  assert.equal(model.snapshot.detail?.node.activation_id, id(2));
});
