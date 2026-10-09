import { test } from "node:test";
import assert from "node:assert/strict";
import { LaunchSubmission } from "../../../src/transport/launch/submission.js";
import { admission, command, profile, receipt } from "../../fixtures/launch.js";

test("nested admission bytes are retained; immutable request restores exactly", () => {
  const inner = admission(), cmd = LaunchSubmission.from(inner, profile);
  assert.ok(cmd.body.includes('"admission":' + inner.body));
  const value = cmd.request; value.identity.actor_id = "changed";
  assert.equal(cmd.request.identity.actor_id, "researcher");
  assert.equal(LaunchSubmission.restore(cmd.body).body, cmd.body);
  assert.throws(() => LaunchSubmission.restore(cmd.body.replace('"command_id":"launch-1"', '"command_id":"different"')));
});

test("run, receipt, profile, worker and revision changes cannot be adopted", () => {
  const cmd = command(), original = receipt(cmd, true);
  for (const change of [
    (v: typeof original) => { v.run_id = "other-run"; },
    (v: typeof original) => { v.profile.sha256 = "a".repeat(64); },
    (v: typeof original) => { v.workers.ready = 1; },
    (v: typeof original) => { v.revision = 0; },
    (v: typeof original) => { v.request_sha256 = "a".repeat(64); },
    (v: typeof original) => { v.admission = null; },
  ]) { const changed = structuredClone(original); change(changed); assert.throws(() => cmd.verify(changed, original)); }
  assert.deepEqual(cmd.verify(original), original);
});
