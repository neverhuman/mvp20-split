import { test } from "node:test";
import assert from "node:assert/strict";
import { MonitorModel } from "../../src/page_models/monitor.js";
import type { ObservationSource } from "../../src/transport/observations.js";
import { values } from "../fixtures/evidence.js";
import { snapshot, context, id, detail, events } from "../fixtures/observations.js";

test("hidden observations become stale without fetching and reactivation preserves selection at a fresh cut", async () => {
  let reads = 0, clock = "2026-09-30T02:00:00.000Z";
  const source: ObservationSource = { snapshot: async () => snapshot({ revision: ++reads }),
    detail: async () => detail(1, reads), values: async () => values(), events: async () => events([]) };
  const model = new MonitorModel(source, () => clock);
  await model.open(context); await model.select(id(1));
  assert.equal(model.snapshot.fetchedAt, clock);
  await model.setVisible(false); assert.equal(model.snapshot.phase, "stale"); assert.equal(reads, 1);
  clock = "2026-09-30T02:01:00.000Z";
  await model.setVisible(true);
  assert.equal(model.snapshot.selection, id(1)); assert.equal(model.snapshot.detail?.cut.revision, 2);
  assert.equal(model.snapshot.fetchedAt, clock); assert.equal(reads, 2);
});
