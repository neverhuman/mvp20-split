import { test } from "node:test";
import assert from "node:assert/strict";
import { QualityLinkModel } from "../../../src/page_models/quality/runtime_link.js";
import { WorkspaceQualityOutputSelection } from "../../../src/page_models/session/quality_output_selection.js";
import { ReadFailure } from "../../../src/transport/failure.js";
import { snapshot, context, id, deferred } from "../../fixtures/observations.js";
import { evidenceDetail, values } from "../../fixtures/evidence.js";

const pins = { activation_id: id(1), port: "result" };
const source = () => ({ snapshot: async () => snapshot(), detail: async () => evidenceDetail(), values: async () => values() });
test("runtime link reads one bounded pinned output and does not invent consumers", async () => {
  const model = new QualityLinkModel(source()); model.bind(context, pins);
  await model.refresh(); assert.equal(model.snapshot.phase, "idle");
  model.visibility(true); await model.refresh();
  assert.equal(model.snapshot.phase, "ready"); assert.equal(model.snapshot.attachment!.activationId, id(1));
  assert.equal(model.snapshot.attachment!.nodeLabel, "node-1");
  model.visibility(false); assert.equal(model.snapshot.attachment, null); model.dispose();
});
test("foreign campaign, wrong activation and denied reads clear links", async () => {
  for (const variant of ["foreign", "activation", "denied"] as const) {
    const reader = source();
    if (variant === "foreign") reader.snapshot = async () => snapshot({ run: "other" });
    if (variant === "activation") reader.detail = async () => ({ ...evidenceDetail(), node: { ...evidenceDetail().node, activation_id: id(2) } });
    if (variant === "denied") reader.values = async () => { throw new ReadFailure("denied"); };
    const model = new QualityLinkModel(reader); model.bind(context, pins); model.visibility(true); await model.refresh();
    assert.equal(model.snapshot.phase, variant === "denied" ? "denied" : "failed");
    assert.equal(model.snapshot.attachment, null); model.dispose();
  }
});
test("late and reentrant replies cannot resurrect an unbound output", async () => {
  const pending = deferred<ReturnType<typeof snapshot>>(), reader = source(); reader.snapshot = async () => pending.promise;
  const model = new QualityLinkModel(reader); model.bind(context, pins); model.visibility(true);
  const first = model.refresh(); model.bind(context, null); pending.resolve(snapshot()); await first;
  assert.equal(model.snapshot.attachment, null);
  model.subscribe(() => { if (model.snapshot.phase === "loading") model.bind(context, null); });
  model.bind(context, pins); await model.refresh(); assert.equal(model.snapshot.attachment, null);
  model.dispose(); await model.refresh(); assert.equal(model.snapshot.phase, "idle");
});
test("output launcher selection cannot redirect into another run or arbitrary path", () => {
  const query = (value: unknown) => new URLSearchParams({ quality_output: JSON.stringify(value) }).toString();
  assert.equal(new WorkspaceQualityOutputSelection(query(pins)).phase, "ready");
  assert.equal(new WorkspaceQualityOutputSelection("").phase, "missing");
  for (const value of [{ ...pins, run_id: "foreign" }, { ...pins, port: "../secrets" }, { ...pins, activation_id: "other" }]) {
    assert.equal(new WorkspaceQualityOutputSelection(query(value)).phase, "invalid");
  }
  assert.equal(new WorkspaceQualityOutputSelection(query(pins) + "&" + query(pins)).phase, "invalid");
});
