import { test } from "node:test";
import assert from "node:assert/strict";
import { EvidenceContext } from "../../src/page_models/evidence_context.js";
import { EvidenceModel } from "../../src/page_models/evidence.js";
import type { EvidenceSource } from "../../src/transport/observations.js";
import { ReadFailure } from "../../src/transport/failure.js";
import { artifact, completion, evidenceDetail, values } from "../fixtures/evidence.js";
import { deferred, id, snapshot } from "../fixtures/observations.js";

const source = (): EvidenceSource => ({ completion: async () => completion(), artifact: async () => artifact(), values: async () => values() });
const context = () => new EvidenceContext(snapshot().snapshot, evidenceDetail());
test("completion provenance binds every execution identity and the observed revision", () => {
  const selected = context(), record = completion();
  assert.deepEqual(selected.completion("attempt-1", record), record);
  for (const bad of [{ ...record, scope: { tenant_id: "other", project_id: "other" } },
    { ...record, run_id: "other" }, { ...record, activation_id: id(2) }, { ...record, completion_id: "other" },
    { ...record, accepted_run_revision: 2 }, { ...record, canonical_result: false },
    { ...record, result: { ...record.result, fence: 2 } }, { ...record, result: { ...record.result, invocation_id: "other" } },
    { ...record, result: { ...record.result, attempt_id: "other" } }])
    assert.throws(() => selected.completion("attempt-1", bad));
  assert.throws(() => selected.completion("not-selected", record));
  assert.throws(() => new EvidenceContext(snapshot({ revision: 2 }).snapshot, evidenceDetail()));
});
test("artifact metadata must match every retained reference field", () => {
  const selected = context(), expected = artifact();
  assert.deepEqual(selected.artifact(expected, expected), expected);
  for (const actual of [{ ...expected, sha256: id(99) }, { ...expected, size_bytes: 18 }, { ...expected, media_type: "text/plain" },
    { ...expected, artifact_id: "other" }, { ...expected, scope: { tenant_id: "other", project_id: "other" } },
    { ...expected, schema_ref: { ...expected.schema_ref, sha256: id(99) } }]) assert.throws(() => selected.artifact(expected, actual));
});
test("output pages cannot change cut, membership, port or completeness", () => {
  const selected = context(), page = values(); assert.deepEqual(selected.values("result", page, 0), page);
  for (const bad of [{ ...page, cut: snapshot({ revision: 2 }).snapshot.cut }, { ...page, activation_id: id(2) },
    { ...page, port: "other" }, { ...page, items: [] }, { ...page, next_cursor: "false-more" },
    { ...page, items: [{ ...page.items[0]!, index: 1 }] }]) assert.throws(() => selected.values("result", bad, 0));
});
test("evidence follows completion to exact artifact metadata without fetching content", async () => {
  const peer = source(), seen: string[] = [];
  peer.artifact = async id => { seen.push(id); return artifact(); };
  const model = new EvidenceModel(peer); model.bind(snapshot().snapshot, evidenceDetail());
  await model.completion("attempt-1"); await model.values("result"); await model.artifact(artifact());
  assert.equal(model.snapshot.completion.value?.canonical_result, true);
  assert.deepEqual(model.snapshot.artifact.value, artifact()); assert.deepEqual(seen, ["artifact-1"]);
  await model.artifact({ ...artifact(), artifact_id: "unlinked" }); assert.equal(model.snapshot.artifact.error?.kind, "unavailable");
  assert.deepEqual(seen, ["artifact-1"]);
});
test("new selection and denied evidence fence uncancellable responses", async () => {
  const peer = source(), model = new EvidenceModel(peer), held = deferred<ReturnType<typeof completion>>();
  peer.completion = () => held.promise; model.bind(snapshot().snapshot, evidenceDetail());
  const pending = model.completion("attempt-1"); model.bind(null, null); held.resolve(completion()); await pending;
  assert.equal(model.snapshot.completion.value, null);
  model.bind(snapshot().snapshot, evidenceDetail()); peer.values = async () => { throw new ReadFailure("denied"); };
  await model.values("result"); assert.equal(model.snapshot.values.phase, "denied");
  await model.artifact(artifact()); assert.equal(model.snapshot.artifact.phase, "idle");
  model.dispose();
});
