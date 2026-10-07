import { test } from "node:test";
import assert from "node:assert/strict";
import { FollowupModel } from "../../../src/page_models/followup/model.js";
import type { RetainedProposal } from "../../../src/transport/followup/client.js";
import { ScientificReadFailure } from "../../../src/transport/scientific/failure.js";
import { fixture } from "../../fixtures/followup.js";
test("hiding the region fences an uncancellable read", async () => {
  const f = fixture(); let release!: (value: RetainedProposal) => void;
  const model = new FollowupModel({ load: () => new Promise(resolve => { release = resolve; }) });
  const pending = model.select(f.selection); model.clear();
  release({ selection: f.selection, record: f.record, document: { kind: "followup", draft: f.document } }); await pending;
  assert.equal(model.snapshot.phase, "idle"); assert.equal(model.snapshot.projection, null);
});
test("denied refresh clears prior protected content", async () => {
  const f = fixture(); let deny = false;
  const model = new FollowupModel({ async load() { if (deny) throw new ScientificReadFailure("denied"); return { selection: f.selection, record: f.record, document: { kind: "followup", draft: f.document } }; } });
  await model.select(f.selection); assert.equal(model.snapshot.phase, "ready"); deny = true;
  await model.select(f.selection); assert.equal(model.snapshot.phase, "denied"); assert.equal(model.snapshot.page, null);
});
test("reentrant hiding avoids even starting the protected read", async () => {
  let calls = 0; const model = new FollowupModel({ async load() { calls++; throw Error(); } });
  model.subscribe(() => { if (model.snapshot.phase === "loading") model.clear(); });
  await model.select(fixture().selection); assert.equal(calls, 0); assert.equal(model.snapshot.phase, "idle");
});
