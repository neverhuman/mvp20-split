import { test } from "node:test";
import assert from "node:assert/strict";
import { EmergencyStop } from "../../../src/page_models/design/emergency_stop.js";
import { AuthoringFailure } from "../../../src/transport/authoring.js";
import type { AuthoringClient } from "../../../src/transport/authoring.js";
import type { CommandReceipt } from "../../../src/contracts/authoring.js";
import type { Submission } from "../../../src/transport/submission.js";
import { context, snapshot } from "../../fixtures/observations.js";

const accepted = (command: Submission): CommandReceipt => ({ outcome: { status: "accepted", binding: {
  identity: command.identity, operation_id: "stop", request_sha256: "a".repeat(64) }, committed: { kind: "run", object_id: context.run, revision: 2 } } });
type Source = Pick<AuthoringClient, "submit" | "receipt">;

test("a newly admitted revision-zero run can be stopped before any work begins", async () => {
  const source: Source = { submit: async command => {
    assert.equal(JSON.parse(command.body).payload.expected_run_revision, 0);
    const result = accepted(command); if (result.outcome.status === "accepted") result.outcome.committed.revision = 1; return result;
  }, receipt: async () => { throw new Error("unexpected"); } };
  const model = new EmergencyStop("operator", context, source);
  model.observe(snapshot({ revision: 0, ids: [] }).snapshot); await model.request("stop-zero");
  assert.equal(model.snapshot.phase, "accepted"); assert.equal(model.snapshot.committedRevision, 1);
});

test("lost emergency acknowledgement reconciles original identity without another POST", async () => {
  let posts = 0, original: Submission | undefined;
  const source: Source = { submit: async command => { posts++; original = command; throw new AuthoringFailure("network", true); },
    receipt: async command => { assert.equal(command, original); return accepted(command); } };
  const model = new EmergencyStop("operator", context, source);
  model.observe(snapshot().snapshot); await model.request("stop-1");
  assert.equal(model.snapshot.phase, "unresolved");
  assert.throws(() => model.request("stop-2"));
  model.observe(snapshot({ revision: 9 }).snapshot);
  await model.reconcile();
  assert.equal(model.snapshot.phase, "accepted");
  assert.equal(model.snapshot.committedRevision, 2);
  assert.equal(JSON.parse(original!.body).payload.expected_run_revision, 1);
  assert.equal(posts, 1);
});

test("stale and terminal observations never enable a new stop; rejection is not cancellation", async () => {
  const source: Source = { submit: async command => ({ outcome: { status: "rejected", binding: accepted(command).outcome.binding, reason_code: "run_revision_conflict" } }),
    receipt: async () => { throw new Error("unexpected"); } };
  const model = new EmergencyStop("operator", context, source);
  assert.throws(() => model.request("stop"));
  model.observe({ ...snapshot().snapshot, status: "completed" }); assert.throws(() => model.request("stop"));
  model.observe(snapshot().snapshot); model.observe(null); assert.throws(() => model.request("stop"));
  model.observe(snapshot().snapshot); await model.request("stop");
  assert.equal(model.snapshot.phase, "rejected"); assert.equal(model.snapshot.reason, "run_revision_conflict");
  assert.throws(() => model.reconcile());
});

test("foreign commit and changed pending binding remain unresolved", async () => {
  let wrong = false;
  const source: Source = { submit: async command => ({ outcome: { status: "pending", binding: accepted(command).outcome.binding } }),
    receipt: async command => { const result = accepted(command); if (wrong) result.outcome.binding.operation_id = "different";
      else if (result.outcome.status === "accepted") result.outcome.committed.object_id = "foreign"; return result; } };
  const model = new EmergencyStop("operator", context, source);
  model.observe(snapshot().snapshot); await model.request("stop"); await model.reconcile();
  assert.equal(model.snapshot.phase, "unresolved"); wrong = true; await model.reconcile();
  assert.equal(model.snapshot.reason, "invalid_response");
});

test("denial fences late stop receipt and removes protected observations", async () => {
  let release: ((value: CommandReceipt) => void) | undefined, command: Submission | undefined;
  const source: Source = { submit: async value => { command = value; return new Promise<CommandReceipt>(resolve => { release = resolve; }); }, receipt: async () => { throw new Error("unexpected"); } };
  const model = new EmergencyStop("operator", context, source);
  model.observe(snapshot().snapshot); const request = model.request("stop");
  model.deny(); release!(accepted(command!)); await request;
  assert.equal(model.snapshot.phase, "denied"); assert.equal(model.snapshot.revision, null);
  assert.throws(() => model.reconcile()); model.dispose();
});

test("untrusted terminal outcomes cannot change during original receipt recovery", async () => {
  const source: Source = { submit: async command => { const result = accepted(command);
    if (result.outcome.status === "accepted") result.outcome.committed.object_id = "foreign"; return result; },
    receipt: async command => accepted(command) };
  const model = new EmergencyStop("operator", context, source);
  model.observe(snapshot().snapshot); await model.request("stop"); await model.reconcile();
  assert.equal(model.snapshot.phase, "unresolved"); assert.equal(model.snapshot.reason, "invalid_response");
});

test("foreign observations clear the stop anchor; transport denial permanently disables its session", async () => {
  const source: Source = { submit: async () => { throw new AuthoringFailure("denied", true); }, receipt: async () => { throw new Error("unexpected"); } };
  const model = new EmergencyStop("operator", context, source);
  let notices = 0; const unsubscribe = model.subscribe(() => { notices++; });
  model.observe(snapshot().snapshot); model.observe(snapshot().snapshot); assert.equal(notices, 1);
  assert.throws(() => model.observe(snapshot({ run: "other" }).snapshot), /mismatch/);
  assert.equal(model.snapshot.revision, null); assert.equal(model.matches({ ...context, run: "other" }), false);
  model.observe(snapshot().snapshot); await model.request("stop");
  assert.equal(model.snapshot.phase, "denied"); model.observe(snapshot().snapshot);
  assert.equal(model.snapshot.revision, null); unsubscribe(); model.dispose();
});


test("command collision cannot adopt a previous stop receipt or silently issue another stop", async () => {
  let reads = 0;
  const model = new EmergencyStop("operator", context, {
    submit: async () => { throw new AuthoringFailure("command_conflict", true); },
    receipt: async command => { reads++; return accepted(command); },
  });
  model.observe(snapshot().snapshot); await model.request("colliding-id");
  assert.equal(model.snapshot.phase, "conflict");
  assert.equal(model.snapshot.committedRevision, null);
  assert.throws(() => model.reconcile()); assert.throws(() => model.request("new-id"));
  assert.equal(reads, 0);
});


test("pending stop resumes exact original revision and identity after receipt verification", async () => {
  const bodies: string[] = []; let ready = false;
  const model = new EmergencyStop("operator", context, { submit: async command => { bodies.push(command.body);
    if (!ready) throw new AuthoringFailure("network", true); return accepted(command);
  }, receipt: async command => ({ outcome: { status: "pending", binding: accepted(command).outcome.binding } }) });
  model.observe(snapshot().snapshot); await model.request("resume-me"); assert.throws(() => model.resume());
  await model.reconcile(); assert.equal(model.canResume, true);
  model.observe(snapshot({ revision: 9 }).snapshot); ready = true; await model.resume();
  assert.equal(model.snapshot.phase, "accepted"); assert.equal(new Set(bodies).size, 1); assert.equal(bodies.length, 2);
  assert.equal(JSON.parse(bodies[1]!).payload.expected_run_revision, 1);
});
