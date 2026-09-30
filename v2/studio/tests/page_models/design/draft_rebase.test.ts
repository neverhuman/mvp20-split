import { test } from "node:test";
import assert from "node:assert/strict";
import { DraftRebase } from "../../../src/page_models/design/draft_rebase.js";
import { AuthoringFailure } from "../../../src/transport/authoring.js";
import type { DraftRevision, DraftValidation } from "../../../src/contracts/authoring.js";
import { accepted, local, revision, session, scope } from "../../fixtures/authoring.js";

test("explicit rebase preserves all local edits, clears old validation and requires saving before new validation", async () => {
  const state = session(), validation: DraftValidation = { scope, draft_id: "draft", revision: 1, content_sha256: "1".repeat(64),
    validation_id: "validation", universe_sha256: "a".repeat(64), structurally_valid: true, plan_sha256: "b".repeat(64),
    findings: [], pending_checks: [], scientific_acceptance: "not_established" };
  const validate = state.beginValidation("validate"); state.reconcile(validate, accepted(validate, validation), validation);
  state.edit({ ...local(), title: "Local work" });
  const remote = revision(2, { ...local(), title: "Someone else's revision" });
  const review = new DraftRebase(state, { draft: async () => remote });
  await review.review();
  assert.equal(state.snapshot.base?.head.revision, 1); assert.equal(state.snapshot.validationMatchesDraft, false);
  review.snapshot.head!.head.title = "Tampered preview";
  state.edit({ ...local(), title: "Even newer local work" }); review.apply();
  assert.equal(state.snapshot.local.title, "Even newer local work");
  assert.equal(state.snapshot.base?.head.title, "Someone else's revision");
  assert.equal(state.snapshot.validation, undefined);
  assert.throws(() => state.beginValidation("new-validation"), /save_before_validation/);
  const save = state.beginSave("explicit-save"); assert.equal(JSON.parse(save.body).payload.expected_revision, 2);
});

test("rebase refuses rollback, another draft/campaign/scope, and unresolved command state", async () => {
  const state = session();
  for (const change of [(r: DraftRevision) => { r.head.revision = 1; r.parent_revision = 0; },
    (r: DraftRevision) => { r.head.draft_id = "other"; }, (r: DraftRevision) => { r.definition.campaign_id = "other"; },
    (r: DraftRevision) => { r.scope.project_id = "other"; }]) {
    const wrong = revision(2); change(wrong);
    assert.throws(() => state.rebase(wrong));
  }
  const review = new DraftRebase(state, { draft: async () => revision(2) });
  await review.review(); state.beginSave("unresolved"); assert.throws(() => review.apply(), /command_unresolved/);
  assert.equal(state.snapshot.base?.head.revision, 1);
});

test("superseded reads and denied late responses cannot restore a protected rebase preview", async () => {
  const state = session(); let deliver!: (r: DraftRevision) => void;
  let calls = 0;
  const review = new DraftRebase(state, { draft: async () => ++calls === 1 ? new Promise(resolve => { deliver = resolve; }) : revision(3) });
  const pending = review.review(); await review.review(); deliver(revision(2)); await pending;
  assert.equal(review.snapshot.head?.head.revision, 3);
  review.deny(); assert.equal(review.snapshot.head, undefined); assert.equal(state.snapshot.denied, true);
  assert.throws(() => review.apply());
  const other = session(), late = new DraftRebase(other, { draft: async () => new Promise(resolve => { deliver = resolve; }) });
  const inflight = late.review(); other.deny(); deliver(revision(2)); await inflight;
  assert.equal(late.snapshot.phase, "denied"); assert.equal(late.snapshot.head, undefined);
});

test("failed head read preserves local state and denial clears only protected projections", async () => {
  const state = session(); state.edit({ ...local(), title: "Keep this" });
  let denied = false;
  const review = new DraftRebase(state, { draft: async () => { throw new AuthoringFailure(denied ? "denied" : "network", false); } });
  await review.review(); assert.equal(review.snapshot.phase, "unavailable"); assert.equal(state.snapshot.base?.head.revision, 1);
  denied = true; await review.review(); assert.equal(review.snapshot.phase, "denied");
  assert.equal(state.snapshot.base, undefined); assert.equal(state.snapshot.local.title, "Keep this");
});
