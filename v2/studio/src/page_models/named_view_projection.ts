import type { SuccessorLineage } from "../contracts/observations.js";
import type { ReadFailure } from "../transport/failure.js";
import type { RegionPhase } from "./monitor.js";
import type { ViewCatalog } from "./view_catalog.js";

export interface NamedViewsState {
  readonly phase: RegionPhase;
  readonly catalog: ViewCatalog | null;
  readonly lineage: SuccessorLineage | null;
  readonly lineagePhase: RegionPhase;
  readonly error: ReadFailure | null;
}

/** Capability/lineage presentation policy, without requests or subscriptions. */
export class NamedViewProjection {
  private constructor(readonly snapshot: NamedViewsState) { Object.freeze(snapshot); }
  static empty(phase: RegionPhase = "idle", error: ReadFailure | null = null) {
    return new NamedViewProjection({ phase, catalog: null, lineage: null, lineagePhase: "idle", error });
  }
  catalogReady(catalog: ViewCatalog) {
    return new NamedViewProjection({ ...this.snapshot, phase: "ready", catalog });
  }
  lineagePending() {
    return new NamedViewProjection({ ...this.snapshot, lineage: null, lineagePhase: "loading", error: null });
  }
  lineageReady(lineage: SuccessorLineage) {
    return new NamedViewProjection({ ...this.snapshot, lineage, lineagePhase: "ready" });
  }
  rejected(error: ReadFailure, region: "catalog" | "lineage") {
    if (error.kind === "aborted") return this;
    if (error.kind === "denied" || error.kind === "resnapshot")
      return NamedViewProjection.empty(error.kind === "denied" ? "denied" : "stale", error);
    return new NamedViewProjection({ ...this.snapshot, error,
      ...(region === "catalog" ? { phase: "failed" as const } : { lineagePhase: "failed" as const }) });
  }
}
