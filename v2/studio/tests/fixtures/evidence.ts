import type { ArtifactRef, CompletionRecord, GraphValuePage } from "../../src/contracts/observations.js";
import { detail, id, scope, snapshot } from "./observations.js";

export const artifact = (): ArtifactRef => ({ artifact_id: "artifact-1", scope, sha256: id(900),
  media_type: "application/json", schema_ref: { schema_id: "synthetic-result", version: "1", sha256: id(901) }, size_bytes: 17 });
export function evidenceDetail() {
  const result = detail(1);
  result.attempts = [{ attempt_id: "attempt-1", invocation_id: "invocation-1", worker_id: "worker-1", fence: 1,
    status: "succeeded", settled: true, completion_id: "completion-1", canonical_result: true }];
  result.outputs = [{ port: "result", kind: "artifact", item_count: 1, missing_count: 0, artifact: artifact() }];
  return result;
}
export function completion(): CompletionRecord {
  return { schema_version: "1", scope, run_id: "run-1", completion_id: "completion-1", activation_id: id(1),
    accepted_run_revision: 1, canonical_result: true, retention_reservation_ids: ["reservation-1"],
    result: { schema_version: "1", invocation_id: "invocation-1", attempt_id: "attempt-1", fence: 1,
      outcome: { status: "succeeded", outputs: [{ port: "result", artifact: artifact() }], checkpoint: null } } };
}
export function values(): GraphValuePage {
  return { schema_version: "1", cut: snapshot().snapshot.cut, activation_id: id(1), port: "result", item_count: 1,
    items: [{ index: 0, value: { kind: "artifact", artifact: artifact(), representation: "fixture", unit: "1" } }], next_cursor: null };
}
