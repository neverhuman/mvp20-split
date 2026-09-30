import { decodeAuthoring } from "../../contracts/authoring.js";
import type { AuthoringClient } from "../../transport/authoring.js";
import { AuthoringFailure } from "../../transport/authoring.js";
import type { Submission } from "../../transport/submission.js";
import { RequestLane } from "../request_lane.js";
import type { ActivationParameters, DraftSession } from "./draft_session.js";

interface ActivationView {
  phase: "idle" | "submitting" | "unresolved" | "reconciling" | "accepted" | "rejected" | "conflict" | "denied";
  draftRevision: number | null;
  commandId: string | null;
  runId: string | null;
  reason: string | null;
}

/** Requests admission of one exact validated revision. Runtime alone decides admission. */
export class DraftActivation {
  private readonly lane = new RequestLane();
  private readonly listeners = new Set<() => void>();
  private command: Submission<"admit"> | undefined;
  private binding: string | undefined;
  private terminal: string | undefined;
  private disposed = false;
  private view: Readonly<ActivationView> = Object.freeze({ phase: "idle", draftRevision: null, commandId: null, runId: null, reason: null });
  constructor(readonly session: DraftSession, private readonly source: Pick<AuthoringClient, "submit" | "receipt">) {}
  get snapshot() { return this.view; }
  get canRequest() {
    const draft = this.session.snapshot;
    return !this.disposed && !draft.denied && !draft.pending && draft.validationMatchesDraft &&
      !!draft.validation?.structurally_valid && ["idle", "rejected"].includes(this.view.phase);
  }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  request(id: string, parameters: ActivationParameters) {
    if (!this.canRequest) throw new Error("activation_not_available");
    this.command = this.session.admission(id, parameters);
    this.binding = undefined; this.terminal = undefined;
    this.patch({ commandId: id, draftRevision: this.session.snapshot.base!.head.revision, runId: null });
    return this.perform(true);
  }
  reconcile() {
    if (this.disposed || this.session.snapshot.denied || this.view.phase !== "unresolved") throw new Error("activation_not_unresolved");
    return this.perform(false);
  }
  deny() {
    this.lane.cancel(); this.session.deny();
    this.patch({ phase: "denied", runId: null, draftRevision: null, reason: "denied" });
  }
  dispose() { this.disposed = true; this.lane.cancel(); this.listeners.clear(); }
  private patch(fields: Partial<ActivationView>) {
    if (this.disposed) return;
    this.view = Object.freeze({ ...this.view, ...fields });
    for (const listener of this.listeners) listener();
  }
  private async perform(submit: boolean) {
    const command = this.command!, request = this.lane.begin();
    this.patch({ phase: submit ? "submitting" : "reconciling", reason: null });
    try {
      const raw = await (submit ? this.source.submit(command, request.signal) : this.source.receipt(command, request.signal));
      if (!request.current()) return;
      if (this.session.snapshot.denied) { this.deny(); return; }
      const receipt = decodeAuthoring("execution_receipt", raw); command.verify(receipt);
      const outcome = receipt.outcome, binding = JSON.stringify([outcome.binding.operation_id, outcome.binding.request_sha256]);
      if (this.binding && this.binding !== binding) throw new Error("activation_receipt_binding_changed");
      this.binding = binding;
      const terminal = JSON.stringify(outcome.status === "accepted" ? [outcome.status, outcome.committed.kind, outcome.committed.object_id, outcome.committed.revision]
        : outcome.status === "rejected" ? [outcome.status, outcome.reason_code] : ["pending"]);
      if (this.terminal && this.terminal !== terminal) throw new Error("activation_terminal_changed");
      if (outcome.status !== "pending") this.terminal = terminal;
      if (outcome.status === "accepted") {
        if (outcome.committed.kind !== "run" || outcome.committed.revision !== 0) throw new Error("activation_commit_mismatch");
        this.patch({ phase: "accepted", runId: outcome.committed.object_id });
      } else this.patch({ phase: outcome.status === "pending" ? "unresolved" : "rejected",
        reason: outcome.status === "rejected" ? outcome.reason_code : null });
    } catch (error) {
      if (!request.current()) return;
      if (this.session.snapshot.denied || error instanceof AuthoringFailure && error.kind === "denied") { this.deny(); return; }
      this.patch({ phase: error instanceof AuthoringFailure && error.kind === "command_conflict" ? "conflict" : "unresolved",
        reason: error instanceof AuthoringFailure ? error.kind : "invalid_response" });
    }
  }
}
