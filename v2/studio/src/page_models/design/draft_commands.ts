import { decodeAuthoring } from "../../contracts/authoring.js";
import type { AuthoringClient } from "../../transport/authoring.js";
import { AuthoringFailure } from "../../transport/authoring.js";
import type { Submission } from "../../transport/submission.js";
import { RequestLane } from "../request_lane.js";
import { DraftActivation } from "./draft_activation.js";
import { DraftRebase } from "./draft_rebase.js";
import { DraftSession } from "./draft_session.js";

export type DraftCommandSource = Pick<AuthoringClient, "submit" | "receipt" | "draft" | "validation">;
export type DraftCommandPhase = "idle" | "submitting" | "reconciling" | "unresolved" | "settled" | "conflict" | "denied";

/** Owns asynchronous command/record reads for one immutable scoped editing session. */
export class DraftCommands {
  private readonly lane = new RequestLane();
  private readonly listeners = new Set<() => void>();
  private disposed = false;
  private view: { phase: DraftCommandPhase; error: AuthoringFailure | undefined } = { phase: "idle", error: undefined };

  readonly rebase: DraftRebase;
  readonly activation: DraftActivation;
  constructor(readonly session: DraftSession, private readonly source: DraftCommandSource) { this.rebase = new DraftRebase(session, source); this.activation = new DraftActivation(session, source); }
  get snapshot() { return this.view; }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }

  save(id: string) { this.requireActive(); return this.perform(this.session.beginSave(id), true); }
  validate(id: string) { this.requireActive(); return this.perform(this.session.beginValidation(id), true); }
  reconcile() {
    this.requireActive();
    const command = this.session.unresolvedCommand;
    if (!command) throw new Error("no_unresolved_command");
    return this.perform(command, false);
  }

  deny() {
    this.lane.cancel(); this.session.deny(); this.rebase.deny(); this.activation.deny();
    this.patch("denied", new AuthoringFailure("denied", !!this.session.unresolvedCommand));
  }
  dispose() { this.disposed = true; this.lane.cancel(); this.rebase.dispose(); this.activation.dispose(); this.listeners.clear(); }

  private requireActive() { if (this.view.phase === "conflict") throw new Error("command_identity_conflict"); if (this.disposed || this.session.snapshot.denied) throw new Error("session_unavailable"); }
  private patch(phase: DraftCommandPhase, error?: AuthoringFailure) {
    if (this.disposed) return;
    this.view = Object.freeze({ phase, error });
    for (const listener of this.listeners) listener();
  }

  private async perform(command: Submission, submit: boolean) {
    const request = this.lane.begin();
    this.patch(submit ? "submitting" : "reconciling");
    try {
      const raw = await (submit ? this.source.submit(command, request.signal) : this.source.receipt(command, request.signal));
      if (!request.current()) return;
      const receipt = decodeAuthoring("receipt", raw);
      if (!this.session.observeReceipt(command, receipt)) return;
      if (receipt.outcome.status !== "accepted") {
        this.session.reconcile(command, receipt);
        this.patch(receipt.outcome.status === "pending" ? "unresolved" : "settled");
        return;
      }
      const committed = receipt.outcome.committed;
      if ((command.action === "save") !== (committed.kind === "draft_revision")) throw new Error("commit_kind_mismatch");
      // Fetch exactly the committed immutable record, never a potentially newer draft head.
      const record = committed.kind === "draft_revision"
        ? await this.source.draft(committed.object_id, committed.revision, request.signal)
        : await this.source.validation(committed.object_id, request.signal);
      if (!request.current()) return;
      this.session.reconcile(command, receipt, record);
      this.patch("settled");
    } catch (error) {
      if (!request.current()) return;
      if (error instanceof AuthoringFailure && error.kind === "denied") { this.deny(); return; }
      if (error instanceof AuthoringFailure && error.kind === "command_conflict") {
        this.session.commandConflict(command); this.patch("conflict", error); return;
      }
      // Even a failed follow-up read leaves the original submission unresolved.
      this.patch("unresolved", new AuthoringFailure(error instanceof AuthoringFailure ? error.kind : "invalid_response", true));
    }
  }
}
