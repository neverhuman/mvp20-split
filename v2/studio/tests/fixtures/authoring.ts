import type { DraftCommandReceipt, DraftRevision, DraftValidation, SaveDraft } from "../../src/contracts/authoring.js";
import { DraftSession } from "../../src/page_models/design/draft_session.js";
import type { Submission } from "../../src/transport/submission.js";

export const scope = { tenant_id: "synthetic", project_id: "authoring" };
export const local = (): Pick<SaveDraft, "title" | "definition"> => ({ title: "Next campaign", definition: {
  schema_version: "4", profile: "deterministic-v3", campaign_id: "campaign", revision: 1, scope,
  body: { nodes: [{ kind: "finish", node_id: "done", outputs: [] }] },
} });
export function revision(index = 1, content = local()): DraftRevision {
  return { scope, definition: content.definition, head: { draft_id: "draft", revision: index, title: content.title, content_sha256: String(index).repeat(64) }, parent_revision: index - 1 };
}
export function accepted(command: Submission, record: DraftRevision | DraftValidation): DraftCommandReceipt {
  const commit = "head" in record ? { kind: "draft_revision" as const, object_id: record.head.draft_id, revision: record.head.revision, content_sha256: record.head.content_sha256 }
    : { kind: "draft_validation" as const, object_id: record.validation_id, revision: record.revision, content_sha256: record.content_sha256 };
  return { outcome: { status: "accepted", binding: { identity: command.identity, operation_id: "operation", request_sha256: "e".repeat(64) }, committed: commit } };
}
export const session = () => new DraftSession("researcher", scope, "draft", local(), revision());

