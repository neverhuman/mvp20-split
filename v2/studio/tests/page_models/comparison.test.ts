/** Labeled future-owner fixtures; no scientific production endpoint or acceptance receipt exists here. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { PropertySeries, comparisonKey, evidenceLane, type Measurement } from "../../src/page_models/comparison.js";

const measurement = (id: string, state = "uncured", observedAt = "2026-09-01T12:00:00Z"): Measurement => ({ id,
  context: { scope: { tenant_id: "fixture", project_id: "comparison" }, material: { id: "nominal-polymer", state },
    property: "strength", method: { id: "fixture-method", version: "1" }, unit: "MPa", applicability: "fixture-context-v1", basis: { kind: "measured" } },
  observedAt, value: "12.50", evidence: `fixture-evidence-${id}` });

test("VIEW-03 the same nominal polymer retains separate processing-state histories", () => {
  const before = measurement("before"), after = measurement("after", "cured", "2026-09-02T12:00:00Z");
  const groups = PropertySeries.partition([after, before]);
  assert.equal(groups.length, 2);
  assert.deepEqual(groups.map(group => group.latest[0]?.id).sort(), ["after", "before"]);
});
test("latest means observation time within exact context, preserving tied observations and history", () => {
  const old = measurement("old"), newer = measurement("newer", "uncured", "2026-09-03T12:00:00Z");
  const tie = { ...newer, id: "tie", evidence: "fixture-tie", value: "13.00" };
  const series = PropertySeries.partition([newer, old, tie])[0]!;
  assert.deepEqual(series.latest.map(record => record.id), ["newer", "tie"]);
  assert.equal(series.history.length, 3);
  assert.throws(() => { series.history[0]!.context.scope.tenant_id = "mutated"; });
});
test("method, units, applicability, prediction/model and scope are independent comparison boundaries", () => {
  const base = measurement("base"), context = base.context;
  const contexts = [
    { ...context, method: { ...context.method, version: "2" } }, { ...context, unit: "Pa" },
    { ...context, applicability: "another-context" }, { ...context, property: "elongation" },
    { ...context, basis: { kind: "predicted" as const, model: "model", version: "1" } },
    { ...context, basis: { kind: "predicted" as const, model: "model", version: "2" } },
    { ...context, scope: { ...context.scope, project_id: "other" } },
  ];
  assert.equal(PropertySeries.partition([base, ...contexts.map((context, index) => ({ ...base, id: `variant-${index}`, context }))]).length, 8);
  assert.throws(() => comparisonKey({ ...context, material: { ...context.material, state: "" } }));
});
test("invalid dates, duplicate identities and oversized comparison windows fail explicitly", () => {
  const base = measurement("base");
  for (const observedAt of ["yesterday", "2026-02-30T12:00:00Z", "2026-09-01T12:00:00+00:00"])
    assert.throws(() => PropertySeries.partition([{ ...base, observedAt }]));
  assert.throws(() => PropertySeries.partition([base, base]));
  assert.throws(() => PropertySeries.partition(Array(1001).fill(base)));
  assert.deepEqual(PropertySeries.partition([]), []);
});
test("model explanations and feature attribution stay separate from assertions", () => {
  assert.equal(evidenceLane("feature_attribution"), "explanation");
  assert.equal(evidenceLane("model_explanation"), "explanation");
  assert.equal(evidenceLane("causal_assertion"), "assertion");
  assert.equal(evidenceLane("hypothesis"), "assertion");
});
