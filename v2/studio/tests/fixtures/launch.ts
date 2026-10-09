import type { LaunchReceipt } from "../../src/contracts/launch.js";
import { Submission } from "../../src/transport/submission.js";
import { LaunchSubmission } from "../../src/transport/launch/submission.js";
export const context = { actor_id: "researcher", scope: { tenant_id: "internal", project_id: "demo" } };
export const profile = { profile_id: "scientific", version: "1" as const, sha256: "d".repeat(64) };
export const admission = (id = "launch-1") => new Submission("admit", { ...context, command_id: id, command_family: "graph.admit_draft" }, {
  inputs: [], budget: { limit: 8 }, plan_sha256: "a".repeat(64),
  draft: { draft_id: "draft", revision: 1, content_sha256: "b".repeat(64), validation_id: "validation", universe_sha256: "c".repeat(64) },
});
export const command = () => LaunchSubmission.from(admission(), profile);
export function receipt(cmd = command(), admitted = false): LaunchReceipt {
  return { identity: cmd.request.identity, profile, request_sha256: "e".repeat(64), revision: admitted ? 3 : 0,
    phase: admitted ? "admitted_not_engaged" : "preparing", reason_code: null,
    created_at: "2026-10-09T12:00:00Z", updated_at: "2026-10-09T12:00:00Z", run_id: admitted ? "actual-run" : null,
    workers: { expected: 0, ready: 0 }, admission: admitted ? { outcome: { status: "accepted", binding: {
      identity: cmd.request.payload.admission.identity, operation_id: "admission-op", request_sha256: "f".repeat(64) },
      committed: { kind: "run", object_id: "actual-run", revision: 0 } } } : null };
}
export function storage() {
  const records = new Map<string, string>();
  return { records, getItem: (key: string) => records.get(key) ?? null, setItem: (key: string, value: string) => { records.set(key, value); } };
}
