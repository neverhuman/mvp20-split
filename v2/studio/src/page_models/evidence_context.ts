import type { ArtifactRef, CompletionRecord, GraphNodeDetail, GraphSnapshotPage, GraphValuePage } from "../contracts/observations.js";
import { cutKey, requireContext } from "./graph_window.js";
import { ReadFailure } from "../transport/failure.js";

export const artifactKey = (ref: ArtifactRef) => JSON.stringify([ref.scope.tenant_id, ref.scope.project_id,
  ref.artifact_id, ref.sha256, ref.size_bytes, ref.media_type, ref.schema_ref.schema_id, ref.schema_ref.version, ref.schema_ref.sha256]);

/** Context and immutable identity checks belong here, not in renderer conditionals. */
export class EvidenceContext {
  readonly anchor: GraphSnapshotPage["snapshot"];
  readonly detail: GraphNodeDetail;
  constructor(anchor: GraphSnapshotPage["snapshot"], detail: GraphNodeDetail) {
    if (cutKey(anchor.cut) !== cutKey(detail.cut)) throw new ReadFailure("resnapshot");
    this.anchor = structuredClone(anchor); this.detail = structuredClone(detail);
  }
  attempt(id: string) {
    const attempt = this.detail.attempts.find(value => value.attempt_id === id);
    if (!attempt?.completion_id) throw new ReadFailure("unavailable");
    return attempt;
  }
  completion(attemptId: string, record: CompletionRecord) {
    const attempt = this.attempt(attemptId), cut = this.anchor.cut;
    requireContext({ scope: cut.scope, run: cut.run_id }, record.scope, record.run_id);
    if (record.activation_id !== this.detail.node.activation_id || record.completion_id !== attempt.completion_id ||
        record.result.attempt_id !== attempt.attempt_id || record.result.invocation_id !== attempt.invocation_id ||
        record.result.fence !== attempt.fence || record.accepted_run_revision > cut.revision ||
        record.canonical_result !== attempt.canonical_result) throw new ReadFailure("invalid_response");
    if (record.result.outcome.status === "succeeded") {
      for (const binding of record.result.outcome.outputs) this.scopedArtifact(binding.artifact);
      if (record.result.outcome.checkpoint) this.scopedArtifact(record.result.outcome.checkpoint);
    }
    return structuredClone(record);
  }
  values(port: string, page: GraphValuePage, loaded: number) {
    const summary = this.detail.outputs.find(output => output.port === port);
    if (!summary) throw new ReadFailure("unavailable");
    if (cutKey(page.cut) !== cutKey(this.anchor.cut)) throw new ReadFailure("resnapshot");
    const count = loaded + page.items.length;
    if (page.activation_id !== this.detail.node.activation_id || page.port !== port || page.item_count !== summary.item_count ||
        count > page.item_count || page.items.some((item, index) => item.index !== loaded + index) ||
        page.next_cursor === null && count !== page.item_count ||
        page.next_cursor !== null && (page.items.length === 0 || count >= page.item_count)) throw new ReadFailure("invalid_response");
    for (const item of page.items) if (item.value.kind === "artifact") this.scopedArtifact(item.value.artifact);
    return structuredClone(page);
  }
  scopedArtifact(ref: ArtifactRef) {
    const scope = this.anchor.cut.scope;
    if (ref.scope.tenant_id !== scope.tenant_id || ref.scope.project_id !== scope.project_id) throw new ReadFailure("invalid_response");
  }
  artifact(expected: ArtifactRef, actual: ArtifactRef) {
    this.scopedArtifact(expected);
    if (artifactKey(expected) !== artifactKey(actual)) throw new ReadFailure("invalid_response");
    return structuredClone(actual);
  }
}
