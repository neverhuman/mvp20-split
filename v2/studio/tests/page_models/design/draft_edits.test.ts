import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { DraftEdits } from "../../../src/page_models/design/draft_edits.js";
import { EditorCatalog } from "../../../src/page_models/design/editor_catalog.js";
import { session, scope } from "../../fixtures/authoring.js";
import { registryFixture } from "../../fixtures/registry.js";

async function fixture() {
  const { release, universe } = registryFixture();
  const bytes = Buffer.from(JSON.stringify({ type: "object", properties: { gain: { type: "number", minimum: 0, maximum: 2 } }, additionalProperties: false, required: ["gain"] }));
  const reference = { schema_id: "numeric-input", version: "1" as const, sha256: createHash("sha256").update(bytes).digest("hex") };
  release.lock.input_schemas[0]!.schema_ref = reference; release.descriptor.tool.inputs[0]!.schema_ref = reference;
  universe.reviewed_tools = [structuredClone(release.lock)]; universe.schemas = [reference];
  const catalog = new EditorCatalog(scope, { universe: async () => universe, releases: async () => ({ items: [release], next_after: null }),
    schema: async () => ({ reference, scope, universe_sha256: universe.universe_sha256, schema_bytes_base64: bytes.toString("base64") }) });
  await catalog.refresh(); const draft = session();
  return { catalog, draft, edits: new DraftEdits(draft, catalog), release, reference };
}

test("tool insertion and input edits use current exact discovery pins without execution authority", async () => {
  const { edits, draft, catalog, release } = await fixture();
  edits.insertTool([], "calculate", release.lock.descriptor_sha256);
  assert.deepEqual(edits.scope().nodes[1], { kind: "invoke", node_id: "calculate", tool: release.lock.tool, inputs: [], timeout_seconds: 60 });
  edits.bindInput([], "calculate", "parameters", { kind: "input", name: "data" });
  assert.throws(() => edits.bindInput([], "calculate", "invented", { kind: "number", value: 1 }), /unknown/);
  assert.equal(draft.snapshot.base!.definition.body.nodes.length, 1);
  catalog.deny(); assert.throws(() => edits.bindInput([], "calculate", "parameters", null));
  assert.equal(edits.scope().nodes.length, 2);
});

test("failed changes are atomic and node deletion exposes dangling dependencies for owner validation", async () => {
  const { edits, draft } = await fixture();
  assert.throws(() => edits.remove([], "done")); assert.equal(edits.scope().nodes.length, 1);
  edits.insert([], { kind: "finish", node_id: "other", outputs: [] });
  assert.throws(() => edits.insert([], { kind: "finish", node_id: "other", outputs: [] }), /exists/);
  edits.connect([], { source: "done", target: "other" });
  assert.throws(() => edits.connect([], { source: "done", target: "other", route: "next" }), /exists/);
  edits.remove([], "done");
  assert.deepEqual(edits.scope().edges, [{ source: "done", target: "other" }]);
  assert.throws(() => edits.replace([], "other", { kind: "finish", node_id: "renamed", outputs: [] }), /identity/);
  edits.disconnect([], 0); assert.deepEqual(edits.scope().edges, []);
  assert.throws(() => edits.disconnect([], 0), /not_found/);
  const copy = edits.scope(); copy.nodes[0]!.node_id = "outside";
  assert.equal(draft.snapshot.local.definition.body.nodes[0]!.node_id, "other");
});

test("parameter-node creation atomically binds exact reviewed artifact schema without replacing existing input", async () => {
  const { edits, release, reference } = await fixture(); edits.insertTool([], "calculate", release.lock.descriptor_sha256);
  edits.parameterNode([], "calculate", "parameters", "prepare");
  const node = edits.scope().nodes[2]!;
  assert.equal(node.kind, "artifact_materialize");
  if (node.kind === "artifact_materialize" && node.output.value_type.kind === "artifact") assert.deepEqual(node.output.value_type.schema_ref, reference);
  assert.deepEqual(edits.scope().edges, [{ source: "prepare", target: "calculate", route: "next" }]);
  assert.throws(() => edits.parameterNode([], "calculate", "parameters", "replacement"), /already_bound/);
  assert.equal(edits.scope().nodes.length, 3);
});

test("nested scope edits cannot accidentally target a same-named parent node", async () => {
  const { edits } = await fixture();
  edits.insert([], { kind: "iterate", node_id: "loop", body: { nodes: [{ kind: "finish", node_id: "done", outputs: [] }] },
    captures: [], state: [{ name: "value", value_type: { kind: "scalar", scalar: "number" }, initial: { kind: "number", value: 0 }, feedback_port: "value" }],
    max_iterations: 2, on_limit: "finish", until: { kind: "constant", value: true } });
  edits.replace(["loop"], "done", { kind: "finish", node_id: "done", outputs: [{ port: "x", source: { kind: "number", value: 1.25 } }] });
  assert.deepEqual(edits.scope().nodes[0], { kind: "finish", node_id: "done", outputs: [] });
  assert.throws(() => edits.scope(["done"]), /scope_node_required/);
  assert.throws(() => edits.scope(["missing"]), /not_found/);
});

test("materializer scalar forms require the exact reviewed output schema and preserve other bindings", async () => {
  const { edits, catalog, reference } = await fixture();
  edits.insert([], { kind: "artifact_materialize", node_id: "parameters", output: { name: "artifact", value_type: { kind: "artifact", representation: "numeric-vector", unit: "1", schema_ref: reference } },
    fields: [{ name: "other", mode: "inline", source: { kind: "input", name: "preserved" } }] });
  assert.throws(() => edits.materializedConstant([], "parameters", "gain", "1.25"), /reviewed/);
  await catalog.inspectSchema(reference); edits.materializedConstant([], "parameters", "gain", "1.25");
  const node = edits.scope().nodes[1]!;
  assert.equal(node.kind, "artifact_materialize");
  if (node.kind === "artifact_materialize") assert.deepEqual(node.fields, [
    { name: "other", mode: "inline", source: { kind: "input", name: "preserved" } }, { name: "gain", mode: "inline", source: { kind: "number", value: 1.25 } }]);
  assert.throws(() => edits.materializedConstant([], "parameters", "gain", "1e-9999"), /too small/);
  assert.throws(() => edits.materializedConstant([], "parameters", "gain", "3"), /reviewed/);
});
