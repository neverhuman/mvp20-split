import { test } from "node:test";
import assert from "node:assert/strict";
import { DraftActivation } from "../../../src/page_models/design/draft_activation.js";
import { AuthoringFailure } from "../../../src/transport/authoring.js";
import type { DraftValidation, CommandReceipt } from "../../../src/contracts/authoring.js";
import type { Submission } from "../../../src/transport/submission.js";
import { accepted, local, session, scope } from "../../fixtures/authoring.js";

function validated() {
  const state = session(), command = state.beginValidation("validate");
  const result: DraftValidation = { scope, draft_id: "draft", revision: 1, content_sha256: "1".repeat(64),
    validation_id: "validation", universe_sha256: "a".repeat(64), structurally_valid: true,
    plan_sha256: "b".repeat(64), findings: [], pending_checks: ["activation"], scientific_acceptance: "not_established" };
  state.reconcile(command, accepted(command, result), result); return state;
}
const parameters = () => ({ inputs: [], budget: { limit: 10 } });
const admitted = (command: Submission): CommandReceipt => ({ outcome: { status: "accepted", binding: {
  identity: command.identity, operation_id: "admission", request_sha256: "a".repeat(64) },
  committed: { kind: "run", object_id: "next-run", revision: 0 } } });

test("only the exact saved and validated draft can request admission", async () => {
  let posts = 0;
  const state = validated(), model = new DraftActivation(state, { submit: async command => {
    posts++;
    const body = JSON.parse(command.body);
    assert.equal(body.payload.draft.validation_id, "validation"); assert.equal(body.payload.draft.revision, 1);
    return admitted(command);
  }, receipt: async command => admitted(command) });
  state.edit({ ...local(), title: "Not saved" });
  assert.equal(model.canRequest, false); assert.throws(() => model.request("invalid", parameters()));
  state.edit(local()); assert.equal(model.canRequest, true);
  assert.throws(() => model.request("bad-budget", { ...parameters(), budget: { limit: -1 } }));
  await model.request("activate", parameters());
  assert.equal(model.snapshot.phase, "accepted"); assert.equal(model.snapshot.runId, "next-run");
  assert.equal(model.canRequest, false); assert.equal(posts, 1);
});

test("lost acknowledgement reconciles the original admission after local edits without another POST", async () => {
  const state = validated(); let posts = 0, original: Submission | undefined;
  const model = new DraftActivation(state, { submit: async command => { posts++; original = command; throw new AuthoringFailure("network", true); },
    receipt: async command => { assert.equal(command, original); return admitted(command); } });
  await model.request("original", parameters()); state.edit({ ...local(), title: "Next-next campaign" });
  assert.throws(() => model.request("new-id", parameters())); await model.reconcile();
  assert.equal(model.snapshot.phase, "accepted"); assert.equal(model.snapshot.draftRevision, 1);
  assert.equal(state.snapshot.local.title, "Next-next campaign"); assert.equal(posts, 1);
});

test("rejected admission preserves the draft and requires a deliberate new request", async () => {
  const state = validated(); let posts = 0;
  const model = new DraftActivation(state, { submit: async command => { posts++; return { outcome: {
    status: "rejected", binding: admitted(command).outcome.binding, reason_code: "active_run_exists" } }; },
    receipt: async () => { throw new Error("unexpected"); } });
  await model.request("blocked", parameters()); assert.equal(model.snapshot.phase, "rejected");
  assert.equal(model.canRequest, true); assert.equal(state.snapshot.validationMatchesDraft, true);
  assert.equal(posts, 1); assert.throws(() => model.reconcile());
});

test("identity collision cannot adopt another receipt or send a fresh identity", async () => {
  const state = validated(); let reads = 0;
  const model = new DraftActivation(state, { submit: async () => { throw new AuthoringFailure("command_conflict", true); },
    receipt: async command => { reads++; return admitted(command); } });
  await model.request("collision", parameters()); assert.equal(model.snapshot.phase, "conflict");
  assert.throws(() => model.reconcile()); assert.throws(() => model.request("new", parameters()));
  assert.equal(reads, 0); assert.equal(state.snapshot.validationMatchesDraft, true);
});

test("denied session fences a late accepted receipt and preserves local content", async () => {
  const state = validated(); let deliver!: () => void;
  const model = new DraftActivation(state, { submit: async command => new Promise(resolve => { deliver = () => resolve(admitted(command)); }),
    receipt: async () => { throw new Error("unexpected"); } });
  const pending = model.request("activate", parameters()); state.deny(); deliver(); await pending;
  assert.equal(model.snapshot.phase, "denied"); assert.equal(model.snapshot.runId, null);
  assert.equal(state.snapshot.base, undefined); assert.deepEqual(state.snapshot.local, local());
});

test("malformed run commit and changed terminal receipt never produce admission success", async () => {
  const state = validated(); let reads = 0;
  const model = new DraftActivation(state, { submit: async command => {
    const result = admitted(command); if (result.outcome.status === "accepted") result.outcome.committed.revision = 1; return result;
  }, receipt: async command => { reads++; return admitted(command); } });
  await model.request("activate", parameters()); await model.reconcile();
  assert.equal(model.snapshot.phase, "unresolved"); assert.equal(model.snapshot.reason, "invalid_response");
  assert.equal(model.snapshot.runId, null); assert.equal(reads, 1);
});


test("only an authoritative pending receipt permits exact original activation resume", async () => {
  const state = validated(), bodies: string[] = []; let ready = false;
  const model = new DraftActivation(state, { submit: async command => { bodies.push(command.body);
    if (!ready) throw new AuthoringFailure("network", true); return admitted(command);
  }, receipt: async command => ({ outcome: { status: "pending", binding: admitted(command).outcome.binding } }) });
  await model.request("resume-me", parameters()); assert.throws(() => model.resume());
  await model.reconcile(); assert.equal(model.canResume, true); ready = true; await model.resume();
  assert.equal(model.snapshot.phase, "accepted"); assert.equal(new Set(bodies).size, 1); assert.equal(bodies.length, 2);
});
