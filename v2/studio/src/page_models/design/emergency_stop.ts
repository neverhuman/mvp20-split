import type { GraphSnapshotPage } from "../../contracts/observations.js";
import { decodeAuthoring } from "../../contracts/authoring.js";
import type { AuthoringClient } from "../../transport/authoring.js";
import { AuthoringFailure } from "../../transport/authoring.js";
import { Submission } from "../../transport/submission.js";
import { contextKey, requireContext } from "../graph_window.js";
import type { RunContext } from "../graph_window.js";
import { RequestLane } from "../request_lane.js";

interface StopView {
  phase: "idle" | "submitting" | "unresolved" | "reconciling" | "accepted" | "rejected" | "denied";
  revision: number | null;
  status: string | null;
  commandId: string | null;
  committedRevision: number | null;
  reason: string | null;
}

/** One operational cancellation identity, independent of draft state and topology. */
export class EmergencyStop {
  private readonly context: RunContext;
  private readonly lane = new RequestLane();
  private readonly listeners = new Set<() => void>();
  private command: Submission<"cancel"> | undefined;
  private binding: string | undefined;
  private terminal: string | undefined;
  private disposed = false;
  private view: Readonly<StopView> = Object.freeze({ phase: "idle", revision: null, status: null, commandId: null, committedRevision: null, reason: null });

  constructor(private readonly actor: string, context: RunContext, private readonly source: Pick<AuthoringClient, "submit" | "receipt">) {
    this.context = structuredClone(context);
  }
  get snapshot() { return this.view; }
  matches(context: RunContext) { return contextKey(context) === contextKey(this.context); }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }

  observe(snapshot: GraphSnapshotPage["snapshot"] | null, denied = false) {
    if (this.disposed || this.view.phase === "denied") return;
    if (denied) { this.deny(); return; }
    if (!snapshot) { this.patch({ revision: null, status: null }); return; }
    try {
      requireContext(this.context, snapshot.cut.scope, snapshot.cut.run_id);
      if (!Number.isSafeInteger(snapshot.cut.revision) || snapshot.cut.revision < 0) throw new Error("invalid_run_revision");
    } catch {
      this.patch({ revision: null, status: null }); throw new Error("stop_observation_mismatch");
    }
    this.patch({ revision: snapshot.cut.revision, status: snapshot.status });
  }

  request(id: string) {
    this.requireActive();
    if (this.command || this.view.phase !== "idle" || this.view.revision === null || this.view.status !== "running") throw new Error("stop_not_available");
    this.command = new Submission("cancel", { actor_id: this.actor, scope: this.context.scope, command_family: "runtime.cancel", command_id: id },
      { run_id: this.context.run, expected_run_revision: this.view.revision, reason_code: "operator_emergency_stop" });
    this.patch({ commandId: id });
    return this.perform(true);
  }

  reconcile() {
    this.requireActive();
    if (!this.command || this.view.phase !== "unresolved") throw new Error("stop_not_unresolved");
    return this.perform(false);
  }
  deny() {
    this.lane.cancel();
    this.patch({ phase: "denied", revision: null, status: null, committedRevision: null, reason: "denied" });
  }
  dispose() { this.disposed = true; this.lane.cancel(); this.listeners.clear(); }
  private requireActive() { if (this.disposed || this.view.phase === "denied") throw new Error("stop_unavailable"); }
  private patch(fields: Partial<StopView>) {
    if (this.disposed) return;
    const next = { ...this.view, ...fields };
    if (Object.entries(next).every(([key, value]) => this.view[key as keyof StopView] === value)) return;
    this.view = Object.freeze(next);
    for (const listener of this.listeners) listener();
  }

  private async perform(submit: boolean) {
    const command = this.command!, request = this.lane.begin();
    this.patch({ phase: submit ? "submitting" : "reconciling", reason: null });
    try {
      const raw = await (submit ? this.source.submit(command, request.signal) : this.source.receipt(command, request.signal));
      if (!request.current()) return;
      const receipt = decodeAuthoring("execution_receipt", raw); command.verify(receipt);
      const outcome = receipt.outcome;
      const binding = JSON.stringify([outcome.binding.operation_id, outcome.binding.request_sha256]);
      if (this.binding && binding !== this.binding) throw new Error("stop_receipt_binding_changed");
      this.binding = binding;
      const terminal = JSON.stringify(outcome.status === "accepted" ? [outcome.status, outcome.committed.kind, outcome.committed.object_id, outcome.committed.revision]
        : outcome.status === "rejected" ? [outcome.status, outcome.reason_code] : ["pending"]);
      if (this.terminal && this.terminal !== terminal) throw new Error("stop_terminal_changed");
      if (outcome.status !== "pending") this.terminal = terminal;
      if (outcome.status === "accepted") {
        const original = JSON.parse(command.body) as { payload: { expected_run_revision: number } };
        if (outcome.committed.kind !== "run" || outcome.committed.object_id !== this.context.run || outcome.committed.revision !== original.payload.expected_run_revision + 1)
          throw new Error("stop_commit_mismatch");
        this.patch({ phase: "accepted", committedRevision: outcome.committed.revision });
      } else this.patch({ phase: outcome.status === "pending" ? "unresolved" : "rejected",
        reason: outcome.status === "rejected" ? outcome.reason_code : null });
    } catch (error) {
      if (!request.current()) return;
      if (error instanceof AuthoringFailure && error.kind === "denied") { this.deny(); return; }
      this.patch({ phase: "unresolved", reason: error instanceof AuthoringFailure ? error.kind : "invalid_response" });
    }
  }
}
