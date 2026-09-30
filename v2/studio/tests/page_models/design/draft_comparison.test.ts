import { test } from "node:test";
import assert from "node:assert/strict";
import { DraftComparison } from "../../../src/page_models/design/draft_comparison.js";
import { local } from "../../fixtures/authoring.js";

test("comparison separates context, bindings, edges and node changes without scientific authority", () => {
  const before = local(), after = local();
  after.title = "Revised";
  after.definition.context = [{ kind: "source", identity: "assay", revision: "2", sha256: "a".repeat(64) }];
  after.definition.body.nodes.push({ kind: "finish", node_id: "other", outputs: [] });
  after.definition.body.edges = [{ source: "done", target: "other", route: "next" }];
  const done = after.definition.body.nodes[0]!;
  if (done.kind === "finish") done.outputs = [{ port: "score", source: { kind: "number", value: 1.25 } }];
  const result = new DraftComparison(before, after).snapshot;
  assert.deepEqual(new Set(result.changes.map(row => row.category)), new Set(["definition", "context", "node", "edge", "binding"]));
  assert.equal(result.scientificCompatibility, "not_assessed");
  assert.equal(result.validationRequired, true);
  assert.equal(result.omitted, 0);
  assert.ok(result.changes.some(row => row.path === "/definition/body/nodes/node:done/outputs/0"));
});

test("node identity survives insertion and reorder without inventing node modifications", () => {
  const before = local();
  before.definition.body.nodes.push({ kind: "finish", node_id: "other", outputs: [] });
  const after = structuredClone(before);
  after.definition.body.nodes.reverse();
  after.definition.body.nodes.unshift({ kind: "finish", node_id: "first", outputs: [] });
  const changes = new DraftComparison(before, after).snapshot.changes;
  assert.deepEqual(changes.map(row => row.kind), ["added", "reordered"]);
  assert.equal(changes[0]?.path, "/definition/body/nodes/node:first");
  assert.equal(new DraftComparison(before, structuredClone(before)).snapshot.total, 0);
});

test("comparison is bounded and copy isolated; truncated differences remain explicit", () => {
  const before = local(), after = local();
  after.title = "Changed"; after.definition.revision = 2;
  const comparison = new DraftComparison(before, after, 1);
  assert.equal(comparison.snapshot.total, 2);
  assert.equal(comparison.snapshot.omitted, 1);
  comparison.snapshot.changes[0]!.path = "tampered";
  after.title = "outside";
  assert.notEqual(comparison.snapshot.changes[0]?.path, "tampered");
  assert.throws(() => new DraftComparison(before, after, 201), /limit/);
  assert.throws(() => new DraftComparison(before, { ...after, definition: { ...after.definition, campaign_id: "foreign" } }), /context_mismatch/);
});

test("duplicate node identities remain visible instead of being silently collapsed", () => {
  const before = local(), after = local();
  after.definition.body.nodes.push({ kind: "finish", node_id: "done", outputs: [] });
  const result = new DraftComparison(before, after).snapshot;
  assert.equal(result.total, 1);
  assert.equal(result.changes[0]?.path, "/definition/body/nodes/1");
  assert.match(result.warnings[1]!, /Duplicate/);
});
