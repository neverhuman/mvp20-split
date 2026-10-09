import { decodeLaunch } from "../../contracts/launch.js";
import type { LaunchRequest, LaunchReceipt } from "../../contracts/launch.js";
import { Submission } from "../submission.js";
import { same } from "../scientific/identity.js";

const identityKey = (value: LaunchRequest["identity"]) => JSON.stringify([
  value.scope.tenant_id, value.scope.project_id, value.actor_id, value.command_family, value.command_id]);
const profileKey = (value: LaunchRequest["payload"]["profile"]) => JSON.stringify([value.profile_id, value.version, value.sha256]);
function freeze<T>(value: T): T {
  if (value && typeof value === "object") { Object.values(value).forEach(freeze); Object.freeze(value); }
  return value;
}

/** One immutable launch envelope; the nested Runtime command retains its original numeric encoding. */
export class LaunchSubmission {
  readonly body: string;
  private constructor(body: string) {
    if (new TextEncoder().encode(body).byteLength > 262_144) throw new Error("launch_request_too_large");
    const request = decodeLaunch("request", JSON.parse(body));
    const inner = request.payload.admission;
    if (request.identity.command_family !== "campaign.launch" || inner.identity.command_family !== "graph.admit_draft" ||
      identityKey(request.identity) !== identityKey({ ...inner.identity, command_family: "campaign.launch" }))
      throw new Error("launch_identity_mismatch");
    this.body = body; Object.freeze(this);
  }
  static from(admission: Submission<"admit">, profile: LaunchRequest["payload"]["profile"]) {
    // Splice the already-validated original wire bytes, never parse/reserialize numerical inputs.
    return new LaunchSubmission('{"encoding":"amphora-command-v2","identity":' +
      JSON.stringify({ ...admission.identity, command_family: "campaign.launch" }) +
      ',"payload":{"profile":' + JSON.stringify(profile) + ',"admission":' + admission.body + '}}');
  }
  static restore(body: string) { return new LaunchSubmission(body); }
  get request(): LaunchRequest { return JSON.parse(this.body); }
  verify(raw: unknown, previous?: LaunchReceipt): LaunchReceipt {
    const receipt = decodeLaunch("receipt", raw), request = this.request;
    if (identityKey(receipt.identity) !== identityKey(request.identity) || profileKey(receipt.profile) !== profileKey(request.payload.profile) ||
      receipt.workers.ready > receipt.workers.expected) throw new Error("launch_receipt_mismatch");
    const outcome = receipt.admission?.outcome;
    if (outcome && identityKey(outcome.binding.identity) !== identityKey(request.payload.admission.identity))
      throw new Error("launch_admission_mismatch");
    if (receipt.run_id !== null && (!outcome || outcome.status !== "accepted" || outcome.committed.kind !== "run" ||
      outcome.committed.revision !== 0 || outcome.committed.object_id !== receipt.run_id)) throw new Error("launch_run_mismatch");
    if (outcome?.status === "accepted" && receipt.run_id !== outcome.committed.object_id) throw new Error("launch_run_missing");
    if (["admitted_not_engaged", "engaging", "engaged", "draining", "released"].includes(receipt.phase) && !receipt.run_id)
      throw new Error("launch_admission_missing");
    if (previous) {
      if (receipt.revision === previous.revision && !same(receipt, previous)) throw new Error("launch_revision_changed");
      if (receipt.request_sha256 !== previous.request_sha256 || receipt.revision < previous.revision ||
        receipt.created_at !== previous.created_at || previous.run_id && previous.run_id !== receipt.run_id)
        throw new Error("launch_binding_changed");
      const old = previous.admission?.outcome;
      if (old && (!outcome || old.binding.operation_id !== outcome.binding.operation_id ||
        old.binding.request_sha256 !== outcome.binding.request_sha256)) throw new Error("launch_admission_binding_changed");
      if (old && old.status !== "pending" && (old.status !== outcome?.status ||
        old.status === "rejected" && outcome.status === "rejected" && old.reason_code !== outcome.reason_code))
        throw new Error("launch_admission_terminal_changed");
      if (["released", "rejected"].includes(previous.phase) && receipt.phase !== previous.phase)
        throw new Error("launch_terminal_changed");
    }
    return freeze(structuredClone(receipt));
  }
}
