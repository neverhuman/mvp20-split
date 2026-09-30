import { test } from "node:test";
import assert from "node:assert/strict";
import { MonitorModel } from "../../src/page_models/monitor.js";
import { EventPosition } from "../../src/page_models/event_position.js";
import type { ObservationSource } from "../../src/transport/observations.js";
import type { GraphSnapshotPage, GraphNodeDetail } from "../../src/contracts/observations.js";
import { ReadFailure } from "../../src/transport/failure.js";
import { snapshot, detail, events, deferred, context, id } from "../fixtures/observations.js";

function source(overrides: Partial<ObservationSource> = {}): ObservationSource {
  return { snapshot: async () => snapshot(), detail: async (_run, activation) => detail(Number.parseInt(activation, 16)),
    values: async () => { throw new Error("not selected"); }, events: async () => events([], 1), ...overrides };
}

test("one loader extends a consistent bounded window and exposes omitted context", async () => {
  const calls: (string | undefined)[] = [];
  const model = new MonitorModel(source({ snapshot: async (_run, _query, cursor) => {
    calls.push(cursor); return cursor ? snapshot({ ids: [3, 4], total: 4 }) : snapshot({ total: 4, next: "page-2" });
  } }));
  await model.open(context);
  assert.equal(model.snapshot.window?.omitted, 2);
  await model.loadMore();
  assert.deepEqual(model.snapshot.window?.nodes.map((node) => node.activation_id), [1, 2, 3, 4].map(id));
  assert.equal(model.snapshot.window?.omitted, 0);
  await model.loadMore();
  assert.deepEqual(calls, [undefined, "page-2"]);
});

test("late uncancellable graph response cannot replace another run", async () => {
  const old = deferred<GraphSnapshotPage>();
  let oldSignal: AbortSignal | undefined;
  const model = new MonitorModel(source({ snapshot: async (run, _query, _cursor, signal) => {
    if (run === "old") { oldSignal = signal; return old.promise; }
    return snapshot({ run });
  } }));
  const first = model.open({ ...context, run: "old" });
  await model.open({ ...context, run: "new" });
  old.resolve(snapshot({ run: "old" }));
  await first;
  assert.ok(oldSignal?.aborted);
  assert.equal(model.snapshot.window?.snapshot.cut.run_id, "new");
});

test("late detail cannot overwrite newer selection even when peer ignores cancellation", async () => {
  const pending = deferred<GraphNodeDetail>();
  const model = new MonitorModel(source({ detail: async (_run, activation) => activation === id(1) ? pending.promise : detail(2) }));
  await model.open(context);
  const first = model.select(id(1));
  await model.select(id(2));
  pending.resolve(detail(1)); await first;
  assert.equal(model.snapshot.selection, id(2));
  assert.equal(model.snapshot.detail?.node.activation_id, id(2));
});

test("new snapshot preserves selection but rejects late old-revision detail", async () => {
  const pending = deferred<GraphNodeDetail>();
  let revision = 1;
  const model = new MonitorModel(source({ snapshot: async () => snapshot({ revision }),
    detail: async () => revision === 1 ? pending.promise : detail(1, revision) }));
  await model.open(context);
  const first = model.select(id(1));
  revision = 2; await model.refresh();
  pending.resolve(detail(1, 1)); await first;
  assert.equal(model.snapshot.selection, id(1));
  assert.equal(model.snapshot.detail?.cut.revision, 2);
});

test("mixed-revision page marks existing window stale without merging", async () => {
  const model = new MonitorModel(source({ snapshot: async (_run, _query, cursor) => cursor
    ? snapshot({ revision: 2, ids: [3, 4], total: 4 }) : snapshot({ total: 4, next: "page-2" }) }));
  await model.open(context); await model.loadMore();
  assert.equal(model.snapshot.phase, "stale");
  assert.equal(model.snapshot.window?.nodes.length, 2);
  assert.equal(model.snapshot.window?.snapshot.cut.revision, 1);
});

test("access denial fences an outstanding page before clearing protected view data", async () => {
  const pending = deferred<GraphSnapshotPage>();
  const model = new MonitorModel(source({ snapshot: async (_run, _query, cursor) => cursor
    ? pending.promise : snapshot({ total: 4, next: "page-2" }), events: async () => { throw new ReadFailure("denied"); } }));
  await model.open(context);
  const loading = model.loadMore(); await model.poll();
  pending.resolve(snapshot({ ids: [3, 4], total: 4 })); await loading;
  assert.equal(model.snapshot.phase, "denied"); assert.equal(model.snapshot.window, null);
});

test("a page cannot contradict status or budget while claiming the same snapshot", async () => {
  const later = snapshot({ ids: [3, 4], total: 4 }); later.snapshot.budget.spent = 2;
  const model = new MonitorModel(source({ snapshot: async (_run, _query, cursor) => cursor
    ? later : snapshot({ total: 4, next: "page-2" }) }));
  await model.open(context); await model.loadMore();
  assert.equal(model.snapshot.phase, "failed"); assert.equal(model.snapshot.window?.snapshot.budget.spent, 0);
});

test("duplicate page membership and false completeness cannot be presented as a full graph", async () => {
  const model = new MonitorModel(source({ snapshot: async (_run, _query, cursor) => cursor
    ? snapshot({ ids: [2, 3], total: 4 }) : snapshot({ total: 4, next: "page-2" }) }));
  await model.open(context); await model.loadMore();
  assert.equal(model.snapshot.phase, "failed");
  const incomplete = new MonitorModel(source({ snapshot: async () => snapshot({ total: 99 }) }));
  await incomplete.open(context);
  assert.equal(incomplete.snapshot.phase, "failed");
});

test("foreign scope/query and wrong activation details are not exposed", async () => {
  const foreign = snapshot(); foreign.snapshot.cut.scope = { ...context.scope, project_id: "foreign" };
  const model = new MonitorModel(source({ snapshot: async () => foreign }));
  await model.open(context);
  assert.equal(model.snapshot.window, null);
  assert.equal(model.snapshot.phase, "failed");
  const wrongQuery = new MonitorModel(source()); await wrongQuery.open(context, { frontier_only: true });
  assert.equal(wrongQuery.snapshot.phase, "failed");
  const wrongDetail = new MonitorModel(source({ detail: async () => detail(2) }));
  await wrongDetail.open(context); await wrongDetail.select(id(1));
  assert.equal(wrongDetail.snapshot.detail, null);
  assert.equal(wrongDetail.snapshot.detailPhase, "failed");
});

test("hidden invalidation marks stale without fetching; activation refreshes and preserves selection", async () => {
  let loads = 0, polls = 0;
  const model = new MonitorModel(source({ snapshot: async () => snapshot({ revision: ++loads }),
    detail: async () => detail(1, loads), events: async () => { polls++; return events([2]); } }));
  await model.open(context); await model.select(id(1)); await model.setVisible(false);
  await model.invalidate(); await model.poll();
  assert.equal(model.snapshot.phase, "stale"); assert.equal(loads, 1); assert.equal(polls, 0);
  await model.setVisible(true);
  assert.equal(loads, 2); assert.equal(model.snapshot.selection, id(1)); assert.equal(model.snapshot.detail?.cut.revision, 2);
});

test("events invalidate visible state; expired or gapped history triggers one fresh snapshot", async () => {
  for (const behavior of [async () => events([2]), async () => events([3]), async () => { throw new ReadFailure("resnapshot"); }]) {
    let loads = 0;
    const model = new MonitorModel(source({ snapshot: async () => snapshot({ revision: ++loads }), events: behavior }));
    await model.open(context); await model.poll();
    assert.equal(loads, 2); assert.equal(model.snapshot.phase, "ready");
  }
});

test("duplicate invalidations do not rewind or invent revisions", () => {
  let position = new EventPosition(1, "original").accept(events([2]));
  assert.equal(position.accept(events([2])).revision, 2);
  position = position.accept(events([3]));
  assert.equal(position.accept(events([2])), position);
  assert.throws(() => position.accept(events([5])), /Refresh/);
  assert.throws(() => position.accept(events([], 2)), /Refresh/);
  assert.throws(() => position.accept({ ...events([3]), entries: [{ event_id: "changed-id", revision: 3 }] }), /Refresh/);
});

test("empty, denied and disposal states remain explicit and dispose aborts in-flight ownership", async () => {
  const empty = new MonitorModel(source({ snapshot: async () => snapshot({ ids: [] }) }));
  await empty.open(context); assert.equal(empty.snapshot.phase, "empty");
  let denied = false;
  const model = new MonitorModel(source({ snapshot: async () => { if (denied) throw new ReadFailure("denied"); return snapshot(); } }));
  await model.open(context); denied = true; await model.refresh();
  assert.equal(model.snapshot.phase, "denied"); assert.equal(model.snapshot.window, null);
  const pending = deferred<GraphSnapshotPage>(); let active: AbortSignal | undefined, changes = 0;
  const disposed = new MonitorModel(source({ snapshot: async (_r, _q, _c, signal) => { active = signal; return pending.promise; } }));
  disposed.subscribe(() => changes++);
  const loading = disposed.open(context); disposed.dispose(); const last = changes;
  pending.resolve(snapshot()); await loading; await disposed.open(context);
  assert.ok(active?.aborted); assert.equal(changes, last); assert.equal(disposed.snapshot.window, null);
});
