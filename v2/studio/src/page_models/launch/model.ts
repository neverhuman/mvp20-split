import type { LaunchReceipt, LaunchRequest } from "../../contracts/launch.js";
import { LaunchFailure } from "../../transport/launch/client.js";
import type { LaunchClient } from "../../transport/launch/client.js";
import { LaunchSubmission } from "../../transport/launch/submission.js";
import type { Submission } from "../../transport/submission.js";
import { RequestLane } from "../request_lane.js";
import { LaunchJournal } from "./journal.js";

interface LaunchView {
  phase: "idle" | "submitting" | "unresolved" | "reconciling" | "ready" | "conflict" | "denied" | "storage_failed";
  receipt: LaunchReceipt | null;
  requestId: string | null;
  reason: string | null;
}
/** Launch progress is Deployment-owned; execution progress always comes from Runtime. */
export class CampaignLaunch {
  private readonly lane = new RequestLane();
  private readonly listeners = new Set<() => void>();
  private command: LaunchSubmission | undefined;
  private previous: LaunchReceipt | undefined;
  private disposed = false;
  private view: Readonly<LaunchView> = Object.freeze({ phase: "idle", receipt: null, requestId: null, reason: null });
  constructor(private readonly source: Pick<LaunchClient, "submit" | "receipt">, private readonly journal: LaunchJournal) {
    try {
      const saved = journal.load();
      if (saved) { this.command = saved.command; this.previous = saved.receipt;
        this.patch({ phase: "unresolved", requestId: saved.command.request.identity.command_id }); }
    } catch { this.patch({ phase: "storage_failed", reason: "recovery_record_unavailable" }); }
  }
  get snapshot() { return this.view; }
  get request() { return this.command?.request; }
  get submission() { return this.command; }
  get canRequest() { return !this.disposed && (this.view.phase === "idle" || this.view.phase === "ready" &&
    ["released", "rejected"].includes(this.view.receipt?.phase ?? "")); }
  get canReconcile() { return !this.disposed && !!this.command && ["unresolved", "ready"].includes(this.view.phase); }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  requestLaunch(admission: Submission<"admit">, profile: LaunchRequest["payload"]["profile"]) {
    if (!this.canRequest) throw new Error("launch_not_available");
    const command = LaunchSubmission.from(admission, profile);
    try { this.journal.save(command); }
    catch { this.patch({ phase: "storage_failed", reason: "recovery_record_unavailable" }); return Promise.resolve(); }
    this.command = command; this.previous = undefined;
    this.patch({ receipt: null, requestId: command.request.identity.command_id });
    return this.perform(true);
  }
  reconcile() {
    if (!this.canReconcile) throw new Error("launch_not_reconcilable");
    return this.perform(false);
  }
  /** Explicit retry always reuses retained bytes, including when no receipt was observed. */
  retryOriginal() {
    if (!this.canReconcile || this.view.phase !== "unresolved") throw new Error("launch_not_retryable");
    return this.perform(true);
  }
  deny() { this.lane.cancel(); this.patch({ phase: "denied", receipt: null, reason: "denied" }); }
  dispose() { this.disposed = true; this.lane.cancel(); this.listeners.clear(); }
  private patch(fields: Partial<LaunchView>) {
    if (this.disposed) return;
    this.view = Object.freeze({ ...this.view, ...fields });
    for (const listener of this.listeners) listener();
  }
  private async perform(post: boolean) {
    const command = this.command!, request = this.lane.begin();
    this.patch({ phase: post ? "submitting" : "reconciling", reason: null });
    try {
      const raw = await (post ? this.source.submit(command, request.signal) : this.source.receipt(command, request.signal));
      if (!request.current()) return;
      const receipt = command.verify(raw, this.previous);
      try { this.journal.save(command, receipt); }
      catch { this.patch({ phase: "storage_failed", receipt: null, reason: "recovery_record_unavailable" }); return; }
      this.previous = receipt;
      this.patch({ phase: "ready", receipt, reason: receipt.reason_code });
    } catch (error) {
      if (!request.current()) return;
      if (error instanceof LaunchFailure && error.kind === "denied") { this.deny(); return; }
      this.patch({ phase: error instanceof LaunchFailure && error.kind === "conflict" ? "conflict" : "unresolved",
        reason: error instanceof LaunchFailure ? error.kind : "invalid_response" });
    }
  }
}
