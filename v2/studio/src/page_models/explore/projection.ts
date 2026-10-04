import type { GraphEntitySearchPage, GraphNeighborhoodPage, GraphObjectDetail } from "../../contracts/scientific/knowledge.js";
import type { SpecimenViewPage, PropertyViewPage, ObservationSeriesPage } from "../../contracts/scientific/research.js";
import type { VerifiedSourceText } from "../../transport/provenance/integrity.js";
import type { ScientificReadFailure } from "../../transport/scientific/failure.js";
import { immutable } from "./context.js";
import type { ExplorePins } from "./context.js";

export type ExplorePhase = "idle" | "loading" | "empty" | "partial" | "ready" | "stale" | "denied" | "unavailable" | "failed";
export interface ExploreValues {
  search: GraphEntitySearchPage;
  neighborhood: GraphNeighborhoodPage;
  detail: GraphObjectDetail;
  specimens: SpecimenViewPage;
  properties: PropertyViewPage;
  series: ObservationSeriesPage;
  source: VerifiedSourceText;
}
export type ExploreRegion = keyof ExploreValues;
export interface RegionState<T> { readonly phase: ExplorePhase; readonly value: T | null; readonly error: ScientificReadFailure | null; }
export type ExploreRegions = { readonly [K in ExploreRegion]: RegionState<ExploreValues[K]> };
export interface ExploreState { readonly context: ExplorePins | null; readonly visible: boolean; readonly regions: ExploreRegions; }
export const regionNames: ExploreRegion[] = ["search", "neighborhood", "detail", "specimens", "properties", "series", "source"];

export class ExploreProjection {
  private constructor(readonly snapshot: ExploreState) { Object.freeze(snapshot); }
  static empty(context: ExplorePins | null, visible = true, phase: ExplorePhase = "idle", error: ScientificReadFailure | null = null) {
    const regions = Object.fromEntries(regionNames.map(name => [name, Object.freeze({ phase, value: null, error })])) as unknown as ExploreRegions;
    return new ExploreProjection({ context, visible, regions: Object.freeze(regions) });
  }
  region<K extends ExploreRegion>(name: K, phase: ExplorePhase, value: ExploreValues[K] | null = null, error: ScientificReadFailure | null = null) {
    return new ExploreProjection({ ...this.snapshot, regions: Object.freeze({ ...this.snapshot.regions,
      [name]: Object.freeze({ phase, value: value === null ? null : immutable(value), error }) }) });
  }
}
