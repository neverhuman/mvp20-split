import type { CriterionRef } from "../../contracts/followup.js";
import type { CriterionRecords, CriterionSource } from "../../transport/followup/criterion.js";
import { ScientificReadFailure } from "../../transport/scientific/failure.js";
import { immutable } from "../explore/context.js";
import { RequestLane } from "../request_lane.js";
export interface CriterionState {
  readonly phase: "idle" | "loading" | "ready" | "denied" | "unavailable" | "stale" | "failed";
  readonly records: CriterionRecords | null;
}
const empty: CriterionState = Object.freeze({ phase: "idle", records: null });
export class CriterionModel {
  private state = empty;
  private readonly lane = new RequestLane();
  private readonly listeners = new Set<() => void>();
  private disposed = false;
  constructor(private readonly source: CriterionSource) {}
  get snapshot() { return this.state; }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  clear() { this.lane.cancel(); this.publish(empty); }
  dispose() { this.lane.cancel(); this.disposed = true; this.state = empty; this.listeners.clear(); }
  async select(ref: CriterionRef) {
    if (this.disposed) return;
    const operation = this.lane.begin(), selection = structuredClone(ref);
    this.publish({ ...empty, phase: "loading" });
    if (!operation.current()) return;
    try {
      const records = await this.source.load(selection, operation.signal);
      if (operation.current()) this.publish({ phase: "ready", records: immutable(records) });
    } catch (error) {
      if (!operation.current()) return;
      const kind = error instanceof ScientificReadFailure ? error.kind : "invalid_response";
      this.publish({ ...empty, phase: kind === "denied" ? "denied" : kind === "unavailable" ? "unavailable" : kind === "aborted" || kind === "query_conflict" ? "stale" : "failed" });
    }
  }
  private publish(state: CriterionState) { if (this.disposed) return; this.state = Object.freeze(state); for (const listener of this.listeners) listener(); }
}
