import { decodeKnowledge } from "../../contracts/scientific/knowledge.js";
import type { DomainRevisionRef } from "../../contracts/scientific/knowledge.js";
import { decodeResearch } from "../../contracts/scientific/research.js";
import type { PropertyViewRequest } from "../../contracts/scientific/research.js";
import { same } from "../../transport/scientific/identity.js";
import { ScientificReadFailure } from "../../transport/scientific/failure.js";

export function immutable<T>(value: T): T {
  const copy = structuredClone(value);
  function freeze(item: unknown) {
    if (item && typeof item === "object") {
      for (const child of Object.values(item)) freeze(child);
      Object.freeze(item);
    }
  }
  freeze(copy); return copy;
}

export interface ExplorePins {
  graph: DomainRevisionRef | null;
  experiment: PropertyViewRequest["experiment"] | null;
  observations: PropertyViewRequest["observations"];
}

/** View context is an explicit immutable selection, never inferred scientific compatibility. */
export class ExploreContext {
  readonly pins: ExplorePins;
  constructor(input: ExplorePins) {
    try {
      const graph = input.graph === null ? null : decodeKnowledge("search_request", { wire_version: "1", revision: input.graph }).revision;
      const science = input.experiment === null ? null : decodeResearch("property_request", { wire_version: "1", experiment: input.experiment, observations: input.observations });
      if ((!graph && !science) || (!science && input.observations.length)) throw new Error("missing_context");
      this.pins = immutable({ graph, experiment: science?.experiment ?? null, observations: science?.observations ?? [] });
      if (science) this.scope(science.experiment.scope);
      for (const ref of this.pins.observations) this.scope(ref.scope);
      if (new Set(this.pins.observations.map(ref => ref.observation_id + ":" + ref.revision)).size !== this.pins.observations.length) throw new Error("duplicate");
    } catch { throw new ScientificReadFailure("invalid_request"); }
    Object.freeze(this);
  }
  scope(scope: object) { this.require(same(scope, this.pins.graph?.graph.scope ?? this.pins.experiment?.scope)); }
  graph(revision: DomainRevisionRef) { this.require(same(revision, this.pins.graph)); }
  experiment(reference: object) { this.require(same(reference, this.pins.experiment)); }
  observations(references: object[]) { this.require(same(references, this.pins.observations)); }
  observation(reference: object) { this.require(this.pins.observations.some(ref => same(ref, reference))); }
  private require(value: boolean) { if (!value) throw new ScientificReadFailure("invalid_request"); }
}
