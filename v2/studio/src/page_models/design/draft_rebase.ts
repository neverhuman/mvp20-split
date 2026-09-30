import type { DraftRevision } from "../../contracts/authoring.js";
import type { AuthoringClient } from "../../transport/authoring.js";
import { AuthoringFailure } from "../../transport/authoring.js";
import { RequestLane } from "../request_lane.js";
import type { DraftSession } from "./draft_session.js";

/** Read/review a newer head, then explicitly preserve local content against that base. */
export class DraftRebase {
  private readonly lane = new RequestLane();
  private readonly listeners = new Set<() => void>();
  private disposed = false;
  private phase: "idle" | "loading" | "ready" | "applied" | "unavailable" | "denied" = "idle";
  private head: DraftRevision | undefined;
  private reason: string | undefined;
  constructor(private readonly session: DraftSession, private readonly source: Pick<AuthoringClient, "draft">) {}
  get snapshot() { return structuredClone({ phase: this.phase, head: this.head, reason: this.reason }); }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  private notify() { for (const listener of this.listeners) listener(); }
  private requireActive() {
    if (this.disposed || this.session.snapshot.denied) throw new Error("session_unavailable");
    if (this.session.unresolvedCommand) throw new Error("command_unresolved");
  }
  async review() {
    this.requireActive();
    const request = this.lane.begin();
    this.phase = "loading"; this.head = undefined; this.reason = undefined; this.notify();
    try {
      const head = await this.source.draft(this.session.draftId, undefined, request.signal);
      if (!request.current() || this.disposed) return;
      if (this.session.snapshot.denied) { this.deny(); return; }
      this.session.inspectBase(head);
      this.head = structuredClone(head); this.phase = "ready";
    } catch (error) {
      if (!request.current() || this.disposed) return;
      if (this.session.snapshot.denied || error instanceof AuthoringFailure && error.kind === "denied") { this.deny(); return; }
      this.phase = "unavailable";
      this.reason = error instanceof AuthoringFailure ? error.kind : "newer_compatible_base_required";
    }
    this.notify();
  }
  apply() {
    this.requireActive();
    if (this.phase !== "ready" || !this.head) throw new Error("review_base_first");
    this.session.rebase(this.head);
    this.head = undefined; this.phase = "applied"; this.notify();
  }
  deny() {
    this.lane.cancel(); this.session.deny(); this.head = undefined;
    this.phase = "denied"; this.reason = "denied"; this.notify();
  }
  dispose() { this.disposed = true; this.lane.cancel(); this.head = undefined; this.listeners.clear(); }
}
