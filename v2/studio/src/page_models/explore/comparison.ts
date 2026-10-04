import { decodeResearch } from "../../contracts/scientific/research.js";
import type { SpecimenViewPage, PropertyViewPage } from "../../contracts/scientific/research.js";
import { canonical, requireReply, same } from "../../transport/scientific/identity.js";
import { ScientificReadFailure } from "../../transport/scientific/failure.js";
import { immutable } from "./context.js";

type Property = PropertyViewPage["rows"][number];
type Specimen = SpecimenViewPage["rows"][number];
export interface ComparedObservation {
  readonly identity: string;
  readonly observation: Property;
  readonly specimen: Specimen | null;
  readonly specimenContext: "exact" | "unbound" | "outside_window" | "conflicting";
}
export interface ContextDifference {
  readonly field: "sample" | "candidate" | "prepared_state" | "method" | "applicability" | "readout" | "units" | "experiment" | "role";
  readonly relationship: "same" | "different" | "unknown";
}
function units(value: Property["value"]): unknown {
  if (value.kind === "missing") return null;
  if (value.kind === "numeric") return ["scalar", value.quantity.unit];
  if (value.kind === "censored") {
    const lower = value.lower?.quantity.unit, upper = value.upper?.quantity.unit;
    return !lower && !upper || lower && upper && lower !== upper ? null : ["scalar", lower ?? upper];
  }
  if (value.kind === "series") return ["series", value.x_unit, value.y_unit];
  return ["categorical"];
}
function values(row: ComparedObservation): Record<ContextDifference["field"], unknown> {
  const r = row.observation, specimen = row.specimenContext === "exact" ? row.specimen : null;
  return { sample: r.binding.specimen.sample, candidate: specimen?.sample.candidate ?? null,
    prepared_state: r.binding.specimen.material_state, method: r.binding.measurement.method,
    applicability: r.binding.measurement.context, readout: r.expectation?.readout ?? null,
    units: units(r.value), experiment: r.binding.target.experiment, role: r.binding.role };
}

export class ScientificPair {
  readonly differences: readonly ContextDifference[];
  readonly evidenceIdentity: "same_pinned_record" | "distinct_records";
  readonly contextIdentity: "same" | "different" | "incomplete";
  readonly reuseAuthority = "owner_policy_required";
  constructor(readonly left: ComparedObservation, readonly right: ComparedObservation) {
    const a = values(left), b = values(right);
    this.differences = immutable((Object.keys(a) as ContextDifference["field"][]).map(field => ({ field,
      relationship: a[field] === null || b[field] === null ? "unknown" : same(a[field], b[field]) ? "same" : "different" })));
    this.contextIdentity = this.differences.some(d => d.relationship === "different") ? "different" :
      this.differences.some(d => d.relationship === "unknown") || left.specimenContext !== "exact" || right.specimenContext !== "exact" ? "incomplete" : "same";
    this.evidenceIdentity = same(left.observation, right.observation) ? "same_pinned_record" : "distinct_records";
    Object.freeze(this);
  }
}

/** One bounded pair of actual owner pages; no timestamps, aggregation or cache authority. */
export class ScientificComparison {
  readonly rows: readonly ComparedObservation[];
  readonly omittedSpecimens: number;
  readonly omittedObservations: number;
  constructor(specimens: SpecimenViewPage, properties: PropertyViewPage) {
    decodeResearch("specimen_page", specimens); decodeResearch("property_page", properties);
    requireReply(same(specimens.request.experiment, properties.request.experiment));
    const scope = properties.request.experiment.scope;
    requireReply(specimens.rows.every(s => same(s.sample.reference.scope, scope) && same(s.sample.candidate.scope, scope)));
    for (const s of specimens.rows) for (const ref of [s.sample.identity_evidence, s.sample.material_state, s.material?.reference, s.material?.candidate]) if (ref) requireReply(same(ref.scope, scope));
    requireReply(new Set(specimens.rows.map(s => canonical(s.sample.reference))).size === specimens.rows.length);
    requireReply(new Set(properties.rows.map(r => canonical(r.reference))).size === properties.rows.length);
    requireReply(properties.rows.every(r => same(r.reference.scope, scope) && same(r.source.scope, scope) && properties.request.observations.some(ref => same(ref, r.reference))));
    for (const r of properties.rows) for (const ref of [r.binding.specimen.sample, r.binding.specimen.material_state, r.binding.target.experiment, r.binding.measurement.context]) if (ref) requireReply(same(ref.scope, scope));
    this.rows = immutable(properties.rows.map(observation => {
      const selected = observation.binding.specimen.sample;
      const specimen = selected === null ? null : specimens.rows.find(s => same(s.sample.reference, selected)) ?? null;
      const exact = specimen && same(specimen.sample.material_state, observation.binding.specimen.material_state)
        && (specimen.material === null ? specimen.sample.material_state === null : same(specimen.material.reference, specimen.sample.material_state) && same(specimen.material.candidate, specimen.sample.candidate));
      return { identity: canonical(observation.reference), observation, specimen,
        specimenContext: selected === null ? "unbound" : !specimen ? "outside_window" : exact ? "exact" : "conflicting" } as ComparedObservation;
    }));
    this.omittedSpecimens = specimens.total - specimens.rows.length;
    this.omittedObservations = properties.total - properties.rows.length;
    requireReply(this.omittedSpecimens >= 0 && this.omittedObservations >= 0);
    Object.freeze(this);
  }
  pair(left: string, right: string) {
    const a = this.rows.find(row => row.identity === left), b = this.rows.find(row => row.identity === right);
    if (!a || !b) throw new ScientificReadFailure("invalid_request");
    return new ScientificPair(a, b);
  }
}
