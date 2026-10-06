import type { Checkpoint, CheckpointRequest, InspectionSnapshot, SupervisionWire } from "../../contracts/supervision.js";
import type { InspectionBinding, SupervisionSource } from "../../transport/supervision/client.js";
import { asReadFailure } from "../../transport/failure.js";
import { RequestLane } from "../request_lane.js";
export type InspectionTab = "checkpoints" | "requests" | "context" | "responses";
type Page = SupervisionWire[InspectionTab];
export interface InspectionState {
  readonly phase: "idle" | "loading" | "ready" | "empty" | "stale" | "denied" | "unavailable" | "failed";
  readonly tab: InspectionTab; readonly page: Page | null;
  readonly checkpoint: Checkpoint | null; readonly request: CheckpointRequest | null;
  readonly decision: SupervisionWire["decision"] | null;
  readonly decisionUnavailable: boolean;
}
const empty: InspectionState = { phase: "idle", tab: "checkpoints", page: null, checkpoint: null, request: null, decision: null, decisionUnavailable: false };
export class SupervisionModel {
  private state: InspectionState = empty;
  private binding: InspectionBinding | null = null;
  private window: InspectionSnapshot | null = null;
  private cursor: string | null = null;
  private disposed = false;
  private readonly lane = new RequestLane();
  private readonly listeners = new Set<() => void>();
  constructor(private readonly source: SupervisionSource) {}
  get snapshot() { return this.state; }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  bind(binding: InspectionBinding) {
    this.lane.cancel(); this.binding = structuredClone(binding); this.window = null; this.cursor = null; this.publish(empty);
  }
  dispose() { this.lane.cancel(); this.disposed = true; this.listeners.clear(); this.binding = null; this.window = null; this.state = empty; }
  invalidate() { this.lane.cancel(); this.window = null; this.publish({ ...this.state, phase: "stale", page: null, decision: null }); }
  async refresh() {
    if (!this.binding || this.disposed) return;
    const operation = this.lane.begin(), binding = this.binding, previous = this.state;
    this.publish({ ...previous, phase: "loading", page: null, decision: null });
    try {
      const index = await this.source.checkpoints(binding, null, operation.signal);
      if (!operation.current()) return;
      this.window = index.snapshot;
      if (previous.tab === "checkpoints") { this.cursor = null; this.publish({ ...empty, phase: index.total ? "ready" : "empty", page: index }); }
      else await this.load(previous.tab, null, previous.checkpoint, previous.request);
    } catch (error) { if (operation.current()) this.fail(error); }
  }
  checkpoints() { this.cursor = null; this.publish({ ...empty }); return this.refresh(); }
  selectCheckpoint(checkpoint: Checkpoint) { return this.load("requests", null, checkpoint, null); }
  selectRequest(request: CheckpointRequest) { return this.load("context", null, this.state.checkpoint, request); }
  tab(tab: "context" | "responses") { return this.load(tab, null, this.state.checkpoint, this.state.request); }
  requests() { return this.load("requests", null, this.state.checkpoint, null); }
  next() {
    if (this.state.phase !== "ready" || !this.state.page?.next_cursor) return Promise.resolve();
    return this.load(this.state.tab, this.state.page.next_cursor, this.state.checkpoint, this.state.request);
  }
  private async load(tab: InspectionTab, cursor: string | null, checkpoint: Checkpoint | null, request: CheckpointRequest | null) {
    if (!this.binding || !this.window || this.disposed) return;
    const operation = this.lane.begin(), binding = this.binding, snapshot = this.window;
    this.publish({ ...empty, phase: "loading", tab, checkpoint, request });
    try {
      const decision = checkpoint?.reference.decision_id;
      let page: Page;
      if (tab === "checkpoints") page = await this.source.checkpoints(binding, cursor, operation.signal);
      else if (!decision) throw new Error("missing_checkpoint");
      else if (tab === "requests") page = await this.source.requests(binding, decision, snapshot, cursor, operation.signal);
      else if (!request) throw new Error("missing_request");
      else page = await this.source[tab](binding, decision, request.request_sha256, snapshot, cursor, operation.signal);
      if (!operation.current()) return;
      if (page.snapshot.epoch !== snapshot.epoch) { this.invalidate(); return; }
      this.cursor = cursor;
      let outcome: SupervisionWire["decision"] | null = null, unavailable = false;
      if (decision) {
        try { outcome = await this.source.decision(binding, decision, operation.signal); }
        catch (error) {
          if (!operation.current()) return;
          const failure = asReadFailure(error);
          if (failure.kind === "denied") throw failure;
          unavailable = true;
        }
      }
      if (!operation.current()) return;
      this.publish({ phase: page.total ? "ready" : "empty", tab, page, checkpoint, request, decision: outcome, decisionUnavailable: unavailable });
    } catch (error) { if (operation.current()) this.fail(error); }
  }
  private fail(error: unknown) {
    const failure = asReadFailure(error);
    this.window = null;
    this.publish({ ...this.state, tab: failure.kind === "denied" ? "checkpoints" : this.state.tab, page: null, decision: null, request: failure.kind === "denied" ? null : this.state.request,
      checkpoint: failure.kind === "denied" ? null : this.state.checkpoint,
      phase: failure.kind === "denied" ? "denied" : failure.kind === "resnapshot" || failure.kind === "aborted" ? "stale" : failure.kind === "unavailable" ? "unavailable" : "failed" });
  }
  private publish(state: InspectionState) { if (this.disposed) return; this.state = Object.freeze(state); for (const listener of this.listeners) listener(); }
}
