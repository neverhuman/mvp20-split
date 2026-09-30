import { test } from "node:test";
import assert from "node:assert/strict";
import type { DraftCommandReceipt, DraftRevision, DraftValidation, SaveDraft } from "../../../src/contracts/authoring.js";
import { DraftSession } from "../../../src/page_models/design/draft_session.js";
import type { Submission } from "../../../src/transport/submission.js";

const scope = { tenant_id: "synthetic", project_id: "authoring" };
const local = (): Pick<SaveDraft, "title" | "definition"> => ({ title: "Next campaign", definition: {
  schema_version: "4", profile: "deterministic-v3", campaign_id: "campaign", revision: 1, scope,
  body: { nodes: [{ kind: "finish", node_id: "done", outputs: [] }] },
} });
function revision(index = 1, content = local()): DraftRevision {
  return { scope, definition: content.definition, head: { draft_id: "draft", revision: index, title: content.title, content_sha256: String(index).repeat(64) }, parent_revision: index - 1 };
}
function accepted(command: Submission, record: DraftRevision | DraftValidation): DraftCommandReceipt {
  const commit = "head" in record ? { kind: "draft_revision" as const, object_id: record.head.draft_id, revision: record.head.revision, content_sha256: record.head.content_sha256 }
    : { kind: "draft_validation" as const, object_id: record.validation_id, revision: record.revision, content_sha256: record.content_sha256 };
  return { outcome: { status: "accepted", binding: { identity: command.identity, operation_id: "operation", request_sha256: "e".repeat(64) }, committed: commit } };
}
const session = () => new DraftSession("researcher", scope, "draft", local(), revision());

test("new and saved sessions expose copied local work, stable scope and truthful dirty state", () => {
  const fresh = new DraftSession("researcher", scope, "draft", local());
  assert.equal(fresh.snapshot.dirty, true);
  assert.throws(() => fresh.beginValidation("validate"), /save_before_validation/);
  const current = session();
  assert.equal(current.dirty, false);
  current.snapshot.local.title = "external mutation";
  assert.equal(current.snapshot.local.title, "Next campaign");
  const changed = local(); changed.definition.scope = { ...scope, project_id: "other" };
  assert.throws(() => current.edit(changed), /scope_mismatch/);
  assert.throws(() => new DraftSession("researcher", scope, "draft", local(), { ...revision(), scope: { ...scope, tenant_id: "other" } }));
});

test("an older save advances the acknowledged base while preserving newer edits and selection", () => {
  const current = session();
  current.edit({ ...local(), title: "Submitted title" }); current.select("done");
  const command = current.beginSave("save1");
  current.edit({ ...local(), title: "Newer title" });
  const saved = revision(2, { ...local(), title: "Submitted title" });
  assert.equal(current.reconcile(command, accepted(command, saved), saved), true);
  assert.equal(current.snapshot.base?.head.revision, 2);
  assert.equal(current.snapshot.local.title, "Newer title");
  assert.equal(current.snapshot.selected, "done");
  assert.equal(current.dirty, true);
  const next = current.beginSave("save2");
  assert.equal((JSON.parse(next.body) as { payload: SaveDraft }).payload.expected_revision, 2);
  assert.equal(current.reconcile(command, accepted(command, saved), saved), false);
  assert.equal(current.unresolvedCommand, next);
});

test("pending commands survive missing acknowledgements and mismatched committed records", () => {
  const current = session(), command = current.beginSave("save1"), saved = revision(2);
  assert.throws(() => current.beginSave("save2"), /command_unresolved/);
  assert.throws(() => current.beginValidation("validate"), /command_unresolved/);
  assert.throws(() => current.reconcile(command, accepted(command, saved)), /invalid_authoring_response/);
  assert.throws(() => current.reconcile(command, accepted(command, saved), revision(3)), /save_record_mismatch/);
  assert.equal(current.unresolvedCommand, command);
  assert.equal(current.snapshot.base?.head.revision, 1);
  assert.equal(current.reconcile(command, accepted(command, saved), saved), true);
  assert.equal(current.dirty, false);
});

test("rejected save preserves local work and base without silently rebasing", () => {
  const current = session(); current.edit({ ...local(), title: "Keep this" });
  const command = current.beginSave("save1");
  current.reconcile(command, { outcome: { status: "rejected", binding: { identity: command.identity, operation_id: "operation", request_sha256: "e".repeat(64) }, reason_code: "draft_revision_conflict" } });
  assert.equal(current.snapshot.reason, "draft_revision_conflict");
  assert.equal(current.snapshot.local.title, "Keep this");
  assert.equal(current.snapshot.base?.head.revision, 1);
  assert.equal(current.unresolvedCommand, undefined);
});

test("pinned validation becomes historical after local edits and cannot imply execution authority", () => {
  const current = session(), command = current.beginValidation("validate1");
  const result: DraftValidation = { scope, draft_id: "draft", revision: 1, content_sha256: "1".repeat(64), validation_id: "validation",
    universe_sha256: "c".repeat(64), plan_sha256: "d".repeat(64), structurally_valid: true, findings: [], pending_checks: ["current_eligibility"], scientific_acceptance: "not_established" };
  assert.throws(() => current.reconcile(command, accepted(command, result), { ...result, content_sha256: "2".repeat(64) }), /validation_record_mismatch/);
  assert.equal(current.reconcile(command, accepted(command, result), result), true);
  assert.equal(current.snapshot.validationMatchesDraft, true);
  current.edit({ ...local(), title: "Changed" });
  assert.equal(current.snapshot.validationMatchesDraft, false);
  assert.equal(current.snapshot.validation?.validation_id, "validation");
});

test("denial clears server projections, preserves local work and fences late results/transmission", () => {
  const current = session(); current.edit({ ...local(), title: "Recover me" });
  const command = current.beginSave("save1"), saved = revision(2, { ...local(), title: "Recover me" });
  current.deny();
  assert.equal(current.snapshot.base, undefined);
  assert.equal(current.snapshot.local.title, "Recover me");
  assert.equal(current.snapshot.denied, true);
  assert.equal(current.unresolvedCommand, command);
  assert.equal(current.reconcile(command, accepted(command, saved), saved), false);
  assert.throws(() => current.beginSave("other"), /session_denied/);
  assert.throws(() => current.beginValidation("other"), /session_denied/);
});

test("pending receipt pins operation and owner request digest without claiming a browser canonical hash", () => {
  const current = session(), command = current.beginSave("save1"), saved = revision(2), receipt = accepted(command, saved);
  assert.equal(current.reconcile(command, { outcome: { status: "pending", binding: receipt.outcome.binding } }), false);
  const changed = structuredClone(receipt); changed.outcome.binding.request_sha256 = "f".repeat(64);
  assert.throws(() => current.reconcile(command, changed, saved), /receipt_binding_changed/);
  assert.equal(current.unresolvedCommand, command);
  assert.equal(current.reconcile(command, receipt, saved), true);
});
