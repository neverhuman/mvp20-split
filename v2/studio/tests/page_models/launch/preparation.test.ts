import { test } from "node:test";
import assert from "node:assert/strict";
import { LaunchPreparation } from "../../../src/page_models/launch/preparation.js";
import { CampaignLaunch } from "../../../src/page_models/launch/model.js";
import { LaunchJournal } from "../../../src/page_models/launch/journal.js";
import type { DraftValidation } from "../../../src/contracts/authoring.js";
import { accepted, revision, scope } from "../../fixtures/authoring.js";
import { profile, storage, receipt } from "../../fixtures/launch.js";

function fixture() {
  const draft = revision(); let validations = 0, posts = 0;
  const context = { actor_id: "researcher", scope };
  const validation: DraftValidation = { scope, draft_id: "draft", revision: 1, content_sha256: draft.head.content_sha256,
    validation_id: "checked", universe_sha256: "c".repeat(64), structurally_valid: true, plan_sha256: "a".repeat(64),
    findings: [], pending_checks: ["activation"], scientific_acceptance: "not_established" };
  const prepare = new LaunchPreparation(context, {
    drafts: async () => ({ scope, drafts: [draft.head], next_after: null }), draft: async () => draft,
    submit: async command => { validations++; assert.equal(command.action, "validate"); return accepted(command, validation); },
    receipt: async command => accepted(command, validation), validation: async () => validation,
  }, { profiles: async () => ({ scope, profiles: [{ reference: profile, scope, title: "Installed tools",
    tools: [{ capability_id: "science", release: "0.1.0", contract_version: "1", image_sha256: "a".repeat(64) }],
    maximum_invocations: 8, maximum_deadline_seconds: 300 }] }) });
  const launch = new CampaignLaunch({ submit: async command => { posts++; return receipt(command); }, receipt: async command => receipt(command) }, new LaunchJournal(context, storage()));
  return { prepare, launch, draft, counts: () => ({ validations, posts }) };
}
test("selection and checking do not admit; Run sends only the checked saved draft to Deployment", async () => {
  const f = fixture(); await f.prepare.load(); await f.prepare.select("draft");
  assert.equal(f.prepare.snapshot.canRun, false); assert.throws(() => f.prepare.run("too-early", f.launch));
  await f.prepare.validate("check"); assert.equal(f.prepare.snapshot.canRun, true);
  assert.deepEqual(f.counts(), { validations: 1, posts: 0 });
  await f.prepare.run("launch", f.launch);
  assert.equal(f.launch.request?.payload.admission.payload.draft.validation_id, "checked");
  assert.equal(f.launch.request?.payload.admission.payload.limits?.deadline_seconds, 300);
  assert.equal(f.launch.snapshot.phase, "ready"); assert.deepEqual(f.counts(), { validations: 1, posts: 1 });
});
test("unbound graph inputs remain explicit and cannot launch as an empty input list", async () => {
  const f = fixture(); f.draft.definition.body.inputs = [{ name: "required", value_type: { kind: "scalar", scalar: "integer", unit: "1" } }];
  await f.prepare.load(); await f.prepare.select("draft"); await f.prepare.validate("check");
  assert.equal(f.prepare.snapshot.canRun, false); assert.match(f.prepare.snapshot.message!, /input bindings/);
  assert.throws(() => f.prepare.run("launch", f.launch)); assert.equal(f.counts().posts, 0);
});
test("changed draft head and foreign scope cannot become launchable", async () => {
  const f = fixture(); await f.prepare.load(); f.draft.scope = { ...scope, project_id: "foreign" };
  await f.prepare.select("draft"); assert.equal(f.prepare.snapshot.phase, "failed"); assert.equal(f.prepare.snapshot.canRun, false);
});
