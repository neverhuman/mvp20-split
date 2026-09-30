import type { GraphSnapshotPage } from "../contracts/observations.js";
import type { NamedViewSource } from "../transport/observations.js";
import { asReadFailure } from "../transport/failure.js";
import { NamedViewProjection } from "./named_view_projection.js";
import { RequestLane } from "./request_lane.js";
import { ViewCatalog } from "./view_catalog.js";

export type { NamedViewsState } from "./named_view_projection.js";
type Region = "catalog" | "lineage";

/** Rebuildable request coordinator; projection and capability objects own their policies. */
export class NamedViewsModel {
  private projection = NamedViewProjection.empty();
  private readonly lanes = { catalog: new RequestLane(), lineage: new RequestLane() };
  private readonly listeners = new Set<() => void>();
  private disposed = false;

  constructor(private readonly source: NamedViewSource) {}
  get snapshot() { return this.projection.snapshot; }
  subscribe(listener: () => void) {
    this.listeners.add(listener);
    return () => { this.listeners.delete(listener); };
  }
  dispose() {
    this.disposed = true;
    this.cancel(); this.listeners.clear();
  }

  async load(anchor: GraphSnapshotPage["snapshot"] | null) {
    if (this.disposed) return;
    this.cancel();
    if (!anchor) { this.publish(NamedViewProjection.empty()); return; }
    await this.read("catalog", NamedViewProjection.empty("loading"), async signal => {
      const page = await this.source.catalog(anchor.cut.run_id, anchor.snapshot_token, signal);
      return this.projection.catalogReady(ViewCatalog.open(anchor.cut, page));
    });
  }

  async lineage() {
    const { catalog, phase } = this.snapshot;
    if (this.disposed || !catalog || phase !== "ready") return;
    await this.read("lineage", this.projection.lineagePending(), async signal => {
      catalog.resolve("successor_lineage", {});
      const page = await this.source.lineage(catalog.page.cut.run_id, signal);
      return this.projection.lineageReady(catalog.acceptLineage(page));
    });
  }

  private async read(region: Region, starting: NamedViewProjection, operation: (signal: AbortSignal) => Promise<NamedViewProjection>) {
    const request = this.lanes[region].begin();
    this.publish(starting);
    if (!request.current()) return;
    try {
      const next = await operation(request.signal);
      if (request.current()) this.publish(next);
    } catch (raw) {
      if (!request.current()) return;
      const error = asReadFailure(raw);
      if (error.kind === "denied" || error.kind === "resnapshot") this.cancel();
      this.publish(this.projection.rejected(error, region));
    }
  }
  private cancel() { this.lanes.catalog.cancel(); this.lanes.lineage.cancel(); }
  private publish(projection: NamedViewProjection) {
    if (this.disposed || projection === this.projection) return;
    this.projection = projection;
    for (const listener of this.listeners) listener();
  }
}
