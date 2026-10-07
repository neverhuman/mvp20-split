import type { FollowupSelection, FollowupSource } from "../../transport/followup/client.js";
import { ScientificReadFailure } from "../../transport/scientific/failure.js";
import { RequestLane } from "../request_lane.js";
import { ProposalProjection } from "./projection.js";
import type { ProposalPage } from "./projection.js";

export interface FollowupState {
  readonly phase: "idle" | "loading" | "ready" | "unsupported" | "denied" | "stale" | "unavailable" | "failed";
  readonly projection: ProposalProjection | null;
  readonly page: ProposalPage | null;
}
const empty: FollowupState = Object.freeze({ phase: "idle", projection: null, page: null });
export class FollowupModel {
  private state = empty;
  private readonly lane = new RequestLane();
  private readonly listeners = new Set<() => void>();
  private disposed = false;
  constructor(private readonly source: FollowupSource) {}
  get snapshot() { return this.state; }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  clear() { this.lane.cancel(); this.publish(empty); }
  invalidate() { this.lane.cancel(); this.publish({ ...empty, phase: "stale" }); }
  dispose() { this.lane.cancel(); this.disposed = true; this.state = empty; this.listeners.clear(); }
  async select(input: FollowupSelection) {
    if (this.disposed) return;
    const operation = this.lane.begin(), selection = structuredClone(input);
    this.publish({ ...empty, phase: "loading" });
    if (!operation.current()) return; // A subscriber may hide or replace this region.
    try {
      const retained = await this.source.load(selection, operation.signal);
      if (!operation.current()) return;
      if (!retained.document) { this.publish({ ...empty, phase: "unsupported" }); return; }
      const projection = new ProposalProjection(retained.document, selection.checkpoint.scope);
      this.publish({ phase: "ready", projection, page: projection.page() });
    } catch (error) {
      if (!operation.current()) return;
      const kind = error instanceof ScientificReadFailure ? error.kind : "invalid_response";
      this.publish({ ...empty, phase: kind === "denied" ? "denied" : kind === "unavailable" ? "unavailable" :
        kind === "aborted" || kind === "query_conflict" ? "stale" : "failed" });
    }
  }
  page(offset: number) {
    if (this.disposed || this.state.phase !== "ready" || !this.state.projection) return;
    this.publish({ ...this.state, page: this.state.projection.page(offset) });
  }
  private publish(state: FollowupState) {
    if (this.disposed) return;
    this.state = Object.freeze(state);
    for (const listener of this.listeners) listener();
  }
}
