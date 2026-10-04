import type { KnowledgeClient } from "../../transport/scientific/knowledge.js";
import type { ResearchClient } from "../../transport/scientific/research.js";
import type { DataProvenanceClient } from "../../transport/provenance/data.js";
import type { GraphEntitySearchRequest, GraphNeighborhoodRequest, GraphObjectRequest } from "../../contracts/scientific/knowledge.js";
import type { SpecimenViewRequest, PropertyViewRequest, ObservationSeriesRequest } from "../../contracts/scientific/research.js";
import type { SourceSpan } from "../../contracts/scientific/provenance.js";
import { ScientificReadFailure } from "../../transport/scientific/failure.js";
import { RequestLane } from "../request_lane.js";
import { ExploreContext, immutable } from "./context.js";
import type { ExplorePins } from "./context.js";
import { ExploreProjection, regionNames } from "./projection.js";
import type { ExploreValues, ExploreRegion, ExplorePhase } from "./projection.js";

export interface ExploreSources {
  knowledge: Pick<KnowledgeClient, "search" | "neighborhood" | "detail">;
  research: Pick<ResearchClient, "specimens" | "properties" | "series">;
  data: Pick<DataProvenanceClient, "span">;
}

export class ExploreModel {
  private context: ExploreContext | null = null;
  private projection = ExploreProjection.empty(null);
  private readonly lanes = Object.fromEntries(regionNames.map(name => [name, new RequestLane()])) as Record<ExploreRegion, RequestLane>;
  private readonly listeners = new Set<() => void>();
  private disposed = false;
  constructor(private readonly sources: ExploreSources) {}
  get snapshot() { return this.projection.snapshot; }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  bind(pins: ExplorePins | null) {
    if (this.disposed) return;
    const context = pins ? new ExploreContext(pins) : null;
    this.cancel(); this.context = context;
    this.publish(ExploreProjection.empty(context?.pins ?? null, this.snapshot.visible));
  }
  visibility(visible: boolean) {
    if (this.disposed || visible === this.snapshot.visible) return;
    this.cancel(); this.publish(ExploreProjection.empty(this.context?.pins ?? null, visible, "stale"));
  }
  dispose() { this.disposed = true; this.cancel(); this.listeners.clear(); this.context = null; this.projection = ExploreProjection.empty(null, false); }

  search(request: GraphEntitySearchRequest) {
    const query = immutable(request);
    return this.read("search", (context, signal) => { context.graph(query.revision); return this.sources.knowledge.search(query, signal); },
      page => page.next_position ? "partial" : page.entities.length ? "ready" : "empty");
  }
  neighborhood(request: GraphNeighborhoodRequest) {
    const query = immutable(request);
    return this.read("neighborhood", (context, signal) => { context.graph(query.revision); return this.sources.knowledge.neighborhood(query, signal); },
      page => page.next_position || page.unresolved_entities.length ? "partial" : page.entities.length || page.assertions.length ? "ready" : "empty");
  }
  detail(request: GraphObjectRequest) {
    const query = immutable(request);
    this.lanes.source.cancel();
    return this.read("detail", (context, signal) => { context.graph(query.revision); return this.sources.knowledge.detail(query, signal); }, () => "ready", true);
  }
  specimens(request: SpecimenViewRequest) {
    const query = immutable(request);
    return this.read("specimens", (context, signal) => { context.experiment(query.experiment); return this.sources.research.specimens(query, signal); },
      page => page.next_position ? "partial" : page.rows.length ? "ready" : "empty");
  }
  properties(request: PropertyViewRequest) {
    const query = immutable(request);
    return this.read("properties", (context, signal) => { context.experiment(query.experiment); context.observations(query.observations); return this.sources.research.properties(query, signal); },
      page => page.next_position ? "partial" : page.rows.length ? "ready" : "empty");
  }
  series(request: ObservationSeriesRequest) {
    const query = immutable(request);
    return this.read("series", (context, signal) => { context.observation(query.observation); return this.sources.research.series(query, signal); },
      page => page.next_position ? "partial" : page.points.length ? "ready" : "empty");
  }
  source(span: SourceSpan) {
    const query = immutable(span);
    return this.read("source", (context, signal) => { context.scope(query.source.scope); return this.sources.data.span(query, signal); }, () => "ready");
  }

  private async read<K extends ExploreRegion>(region: K, operation: (context: ExploreContext, signal: AbortSignal) => Promise<ExploreValues[K]>, classify: (value: ExploreValues[K]) => ExplorePhase, clearSource = false) {
    if (this.disposed || !this.snapshot.visible || !this.context) return;
    const context = this.context, request = this.lanes[region].begin();
    const pending = clearSource ? this.projection.region("source", "idle") : this.projection;
    this.publish(pending.region(region, "loading"));
    if (!request.current()) return;
    try {
      const value = await operation(context, request.signal);
      if (request.current()) this.publish(this.projection.region(region, classify(value), value));
    } catch (raw) {
      if (!request.current()) return;
      const error = raw instanceof ScientificReadFailure ? raw : new ScientificReadFailure("network");
      if (error.kind === "denied" || error.kind === "query_conflict") {
        this.cancel();
        this.publish(ExploreProjection.empty(this.context?.pins ?? null, this.snapshot.visible, error.kind === "denied" ? "denied" : "stale", error));
      } else this.publish(this.projection.region(region, error.kind === "aborted" ? "stale" : error.kind === "unavailable" ? "unavailable" : "failed", null, error));
    }
  }
  private cancel() { for (const lane of Object.values(this.lanes)) lane.cancel(); }
  private publish(projection: ExploreProjection) {
    if (this.disposed) return;
    this.projection = projection;
    for (const listener of this.listeners) listener();
  }
}
