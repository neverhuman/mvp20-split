import type { FeedbackClient } from "../../transport/feedback/client.js";
import type { ResearchRecordClient } from "../../transport/provenance/research.js";
import { ScientificReadFailure } from "../../transport/scientific/failure.js";
import { RequestLane } from "../request_lane.js";
import { FeedbackContext } from "./context.js";
import type { FeedbackPins } from "./context.js";
import { FeedbackLineage } from "./lineage.js";

export interface FeedbackSources {
  research: Pick<ResearchRecordClient, "question" | "need">;
  feedback: Pick<FeedbackClient, "assessment" | "publication" | "proposal" | "change" | "correction">;
}
export interface FeedbackState {
  readonly context: FeedbackPins | null;
  readonly visible: boolean;
  readonly phase: "idle" | "loading" | "ready" | "stale" | "denied" | "unavailable" | "failed";
  readonly lineage: FeedbackLineage | null;
  readonly error: ScientificReadFailure | null;
}
export class FeedbackModel {
  private context: FeedbackContext | null = null;
  private state: FeedbackState = Object.freeze({ context: null, visible: true, phase: "idle", lineage: null, error: null });
  private readonly lane = new RequestLane();
  private readonly listeners = new Set<() => void>();
  private disposed = false;
  constructor(private readonly sources: FeedbackSources) {}
  get snapshot() { return this.state; }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  bind(pins: FeedbackPins | null) {
    if (this.disposed) return;
    const context = pins ? new FeedbackContext(pins) : null;
    this.lane.cancel(); this.context = context; this.publish("idle");
  }
  visibility(visible: boolean) {
    if (this.disposed || visible === this.state.visible) return;
    this.lane.cancel(); this.publish("stale", null, null, visible);
  }
  dispose() { this.disposed = true; this.lane.cancel(); this.listeners.clear(); this.context = null; this.state = Object.freeze({ context: null, visible: false, phase: "idle", lineage: null, error: null }); }
  async refresh() {
    if (this.disposed || !this.state.visible || !this.context) return;
    const context = this.context, pins = context.pins, request = this.lane.begin(), signal = request.signal;
    this.publish("loading");
    if (!request.current()) return;
    try {
      const [question, need, assessment, proposal, corrections] = await Promise.all([
        this.sources.research.question(pins.question, signal),
        this.sources.research.need(pins.need, signal),
        pins.assessment ? this.sources.feedback.assessment(pins.assessment, signal) : null,
        pins.proposal ? this.sources.feedback.proposal(pins.proposal.graph, pins.proposal.change_id, signal) : null,
        pins.corrections ? Promise.all([
          this.sources.feedback.correction(pins.corrections.owner, pins.corrections.previous, signal),
          this.sources.feedback.correction(pins.corrections.owner, pins.corrections.next, signal),
        ]).then(([previous, next]) => ({ previous, next })) : null,
      ]);
      if (!request.current()) return;
      const [publication, change] = await Promise.all([
        pins.publication ? this.sources.feedback.publication(pins.publication, signal) : null,
        proposal?.decision?.decision.outcome === "accepted" ? this.sources.feedback.change(proposal.decision.decision.head.change, signal) : null,
      ]);
      if (!request.current()) return;
      this.publish("ready", new FeedbackLineage(context, { question, need, assessment, publication, proposal, change, corrections }));
    } catch (raw) {
      if (!request.current()) return;
      this.lane.cancel();
      const error = raw instanceof ScientificReadFailure ? raw : new ScientificReadFailure("network");
      this.publish(error.kind === "denied" ? "denied" : error.kind === "query_conflict" || error.kind === "aborted" ? "stale" : error.kind === "unavailable" ? "unavailable" : "failed", null, error);
    }
  }
  private publish(phase: FeedbackState["phase"], lineage: FeedbackLineage | null = null, error: ScientificReadFailure | null = null, visible = this.state.visible) {
    if (this.disposed) return;
    this.state = Object.freeze({ context: this.context?.pins ?? null, visible, phase, lineage, error });
    for (const listener of this.listeners) listener();
  }
}
