/** Comparison policy only; scientific view producers/acceptance remain unavailable until their owners ship. */
import type { ReadCut } from "../contracts/observations.js";

export interface MeasurementContext {
  readonly scope: ReadCut["scope"];
  readonly material: { readonly id: string; readonly state: string };
  readonly property: string;
  readonly method: { readonly id: string; readonly version: string };
  readonly unit: string;
  readonly applicability: string;
  readonly basis: { readonly kind: "measured" } | { readonly kind: "predicted"; readonly model: string; readonly version: string };
}
export interface Measurement {
  readonly id: string;
  readonly context: MeasurementContext;
  readonly observedAt: string;
  readonly value: string;
  readonly evidence: string;
}

function required(value: string) {
  if (!value.trim() || value.length > 512) throw new Error("incomplete_comparison_context");
  return value;
}
export function comparisonKey(context: MeasurementContext) {
  return JSON.stringify([context.scope.tenant_id, context.scope.project_id, context.material.id, context.material.state,
    context.property, context.method.id, context.method.version, context.unit, context.applicability,
    context.basis.kind, ...(context.basis.kind === "predicted" ? [context.basis.model, context.basis.version] : [])].map(required));
}
function observedTime(value: string) {
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/.test(value)) throw new Error("invalid_observation_time");
  const time = Date.parse(value);
  if (!Number.isFinite(time) || new Date(time).toISOString().slice(0, 19) !== value.slice(0, 19)) throw new Error("invalid_observation_time");
  return time;
}
function retain(record: Measurement): Measurement {
  const copy = structuredClone(record), context = copy.context;
  Object.freeze(context.scope); Object.freeze(context.material); Object.freeze(context.method); Object.freeze(context.basis);
  Object.freeze(context);
  return Object.freeze(copy);
}

/** No unit conversion, state equivalence, evidence promotion or interpretation of a numeric value. */
export class PropertySeries {
  private constructor(readonly key: string, readonly history: readonly Measurement[]) {}
  static partition(records: readonly Measurement[]): readonly PropertySeries[] {
    if (records.length > 1000) throw new Error("comparison_window_exceeded");
    const ids = new Set<string>(), groups = new Map<string, Measurement[]>();
    for (const record of records) {
      const key = comparisonKey(record.context);
      const identity = JSON.stringify([record.context.scope.tenant_id, record.context.scope.project_id, required(record.id)]);
      if (ids.has(identity)) throw new Error("duplicate_measurement_identity");
      ids.add(identity); observedTime(record.observedAt); required(record.evidence); required(record.value);
      const group = groups.get(key) ?? []; group.push(retain(record)); groups.set(key, group);
    }
    return [...groups.entries()].map(([key, rows]) => new PropertySeries(key,
      Object.freeze(rows.sort((a, b) => observedTime(b.observedAt) - observedTime(a.observedAt) || a.id.localeCompare(b.id)))));
  }
  get latest(): readonly Measurement[] {
    const newest = this.history[0];
    return newest ? this.history.filter(record => observedTime(record.observedAt) === observedTime(newest.observedAt)) : [];
  }
}

export type ExplanationRole = "feature_attribution" | "model_explanation";
export type AssertionRole = "causal_assertion" | "hypothesis";
/** Preserve the owner's classification; a feature or explanation never enters the causal-assertion lane. */
export function evidenceLane(role: ExplanationRole | AssertionRole): "explanation" | "assertion" {
  return role === "feature_attribution" || role === "model_explanation" ? "explanation" : "assertion";
}
