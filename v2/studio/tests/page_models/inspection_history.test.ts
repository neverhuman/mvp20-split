import { test } from "node:test";
import assert from "node:assert/strict";
import { InspectionHistory } from "../../src/page_models/inspection_history.js";
import { captureInspection } from "../../src/page_models/history_pin.js";
import { GraphWindow } from "../../src/page_models/graph_window.js";
import type { MonitorView } from "../../src/page_models/monitor.js";
import { context, snapshot, detail, id } from "../fixtures/observations.js";
import { artifact, completion, evidenceDetail, values } from "../fixtures/evidence.js";
import { EvidenceModel } from "../../src/page_models/evidence.js";
import { lineage } from "../fixtures/navigation.js";

function monitor(revision = 1, count = 2): MonitorView {
  return { phase: "ready", window: GraphWindow.open(context, {}, snapshot({ revision, ids: Array.from({ length: count }, (_, i) => i + 1) })),
    selection: id(1), detail: detail(1, revision), detailPhase: "ready", loadingMore: false, error: null, detailError: null, fetchedAt: null };
}
test("pins retain immutable observed records while live revisions advance", () => {
  const history = new InspectionHistory(2, () => "2026-09-30T03:00:00Z"), live = monitor();
  history.setScope(context.scope); history.capture({ monitor: live });
  const pin = history.snapshot.pins[0]!;
  live.detail!.node.path.node_id = "changed";
  history.capture({ monitor: monitor(2) });
  assert.equal(pin.cut.revision, 1); assert.equal(pin.detail!.node.path.node_id, "node-1");
  assert.equal(history.snapshot.pins[1]!.cut.revision, 2);
  assert.throws(() => { pin.cut.revision = 99; }, TypeError);
  history.capture({ monitor: monitor(3) });
  assert.equal(history.snapshot.pins.length, 2); assert.match(history.snapshot.error!, /Remove a pin/);
  history.select(pin.id); history.remove(pin.id); assert.equal(history.snapshot.selected, null);
});
test("scope changes and denial clear history; foreign and stale captures fail closed", () => {
  const history = new InspectionHistory(); history.setScope(context.scope);
  history.capture({ monitor: { ...monitor(), phase: "stale" } }); assert.equal(history.snapshot.pins.length, 0);
  history.capture({ monitor: monitor() }); assert.equal(history.snapshot.pins.length, 1);
  history.setScope({ ...context.scope }); assert.equal(history.snapshot.pins.length, 1);
  history.setScope({ tenant_id: "other", project_id: "other" }); assert.equal(history.snapshot.pins.length, 0);
  history.capture({ monitor: monitor() }); assert.equal(history.snapshot.pins.length, 0);
  history.setScope(context.scope); history.capture({ monitor: monitor() }); history.deny();
  assert.equal(history.compatible(context.scope), false); assert.equal(history.snapshot.pins.length, 0);
  assert.throws(() => history.select("unknown")); assert.throws(() => new InspectionHistory(9));
});
test("bounded captures retain omissions without inventing edges, evidence or unloaded detail", () => {
  const pin = captureInspection("bounded", "2026-09-30T03:00:00Z", { monitor: { ...monitor(1, 250), detailPhase: "loading" } });
  assert.equal(pin.nodes.length, 200); assert.equal(pin.totalNodes, 250);
  assert.deepEqual(pin.edges, []); assert.equal(pin.detail, null); assert.equal(pin.completion, null);
  assert.equal(pin.artifact, null); assert.equal(pin.lineage, null);
  assert.throws(() => captureInspection("invalid", "now", { monitor: { ...monitor(), detail: detail(1, 2) } }));
});
test("captured evidence preserves owner identities and rejects unrelated artifacts or lineage", async () => {
  const evidence = new EvidenceModel({ completion: async () => completion(), values: async () => values(), artifact: async () => artifact() });
  evidence.bind(snapshot().snapshot, evidenceDetail());
  await evidence.completion("attempt-1"); await evidence.values("result"); await evidence.artifact(artifact());
  const selection = { monitor: { ...monitor(), detail: evidenceDetail() }, evidence: evidence.snapshot,
    namedViews: { phase: "ready" as const, catalog: null, lineage: lineage(), lineagePhase: "ready" as const, error: null } };
  const pin = captureInspection("evidence", "2026-09-30T03:00:00Z", selection);
  assert.deepEqual(pin.completion, completion()); assert.deepEqual(pin.artifact, artifact());
  assert.deepEqual(pin.values, values()); assert.deepEqual(pin.lineage, lineage());
  assert.throws(() => captureInspection("bad", "now", { ...selection, evidence: { ...selection.evidence,
    artifact: { phase: "ready", error: null, value: { ...artifact(), sha256: id(999) } } } }));
  assert.throws(() => captureInspection("bad", "now", { ...selection, namedViews: { ...selection.namedViews,
    lineage: { ...lineage(), plan_sha256: id(999) } } }));
  assert.throws(() => captureInspection("bad", "now", { monitor: { ...monitor(), selection: id(2) } }));
  evidence.dispose();
});
