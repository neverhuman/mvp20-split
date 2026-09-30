import type { GraphSnapshotPage, SuccessorLineage } from "../contracts/observations.js";
import type { NamedViewSource } from "../transport/observations.js";
import { asReadFailure, type ReadFailure } from "../transport/failure.js";
import { RequestLane } from "./request_lane.js";
import { ViewCatalog } from "./view_catalog.js";
import type { RegionPhase } from "./monitor.js";

export interface NamedViewsState {
  readonly phase: RegionPhase;
  readonly catalog: ViewCatalog | null;
  readonly lineage: SuccessorLineage | null;
  readonly lineagePhase: RegionPhase;
  readonly error: ReadFailure | null;
}

export class NamedViewsModel {
  private readonly catalogLane = new RequestLane();
  private readonly lineageLane = new RequestLane();
  private readonly listeners = new Set<() => void>();
  private disposed = false;
  private state: NamedViewsState = Object.freeze({ phase: "idle", catalog: null, lineage: null, lineagePhase: "idle", error: null });
  constructor(private readonly source: NamedViewSource) {}
  get snapshot() { return this.state; }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  private patch(fields: Partial<NamedViewsState>) {
    if (this.disposed) return;
    this.state = Object.freeze({ ...this.state, ...fields });
    for (const listener of this.listeners) listener();
  }
  async load(anchor: GraphSnapshotPage["snapshot"] | null) {
    if (this.disposed) return;
    const ticket = this.catalogLane.begin(); this.lineageLane.cancel();
    this.patch({ phase: anchor ? "loading" : "idle", catalog: null, lineage: null, lineagePhase: "idle", error: null });
    if (!anchor) return;
    try {
      const page = await this.source.catalog(anchor.cut.run_id, anchor.snapshot_token, ticket.signal);
      if (ticket.current()) this.patch({ phase: "ready", catalog: ViewCatalog.open(anchor.cut, page) });
    } catch (error) { if (ticket.current()) this.fail(error); }
  }
  async lineage() {
    const catalog = this.state.catalog;
    if (this.disposed || !catalog || this.state.phase !== "ready") return;
    const ticket = this.lineageLane.begin();
    this.patch({ lineage: null, lineagePhase: "loading", error: null });
    try {
      catalog.resolve("successor_lineage", {});
      const page = await this.source.lineage(catalog.page.cut.run_id, ticket.signal);
      if (ticket.current()) this.patch({ lineage: catalog.acceptLineage(page), lineagePhase: "ready" });
    } catch (error) { if (ticket.current()) this.fail(error, true); }
  }
  private fail(raw: unknown, lineage = false) {
    const error = asReadFailure(raw);
    if (error.kind === "aborted") return;
    if (error.kind === "denied" || error.kind === "resnapshot") {
      this.catalogLane.cancel(); this.lineageLane.cancel();
      this.patch({ phase: error.kind === "denied" ? "denied" : "stale", catalog: null, lineage: null, lineagePhase: "idle", error });
    } else this.patch(lineage ? { lineagePhase: "failed", error } : { phase: "failed", error });
  }
  dispose() { this.catalogLane.cancel(); this.lineageLane.cancel(); this.listeners.clear(); this.disposed = true; }
}
