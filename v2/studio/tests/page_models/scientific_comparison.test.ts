import { test } from "node:test";
import assert from "node:assert/strict";
import fixture from "../fixtures/scientific/research.json" with { type: "json" };
import { decodeResearch } from "../../src/contracts/scientific/research.js";
import { ScientificComparison } from "../../src/page_models/explore/comparison.js";
import { ScientificReadFailure } from "../../src/transport/scientific/failure.js";

function pages() {
  const specimens = decodeResearch("specimen_page", structuredClone(fixture.specimen_page));
  const properties = decodeResearch("property_page", structuredClone(fixture.property_page));
  const s = structuredClone(specimens.rows[0]!);
  s.sample.reference.sample_id = "second-sample";
  assert.ok(s.material && s.sample.material_state);
  s.sample.material_state.material_state_id = "second-preparation";
  s.material.reference.material_state_id = "second-preparation";
  const r = structuredClone(properties.rows[0]!);
  r.reference.observation_id = "second-measurement";
  r.binding.specimen.sample = s.sample.reference;
  r.binding.specimen.material_state = s.material.reference;
  specimens.rows.push(s); specimens.total = 2;
  properties.rows.push(r); properties.total = 2; properties.request.observations.push(r.reference);
  return { specimens, properties };
}
function pair(f = pages()) { const model = new ScientificComparison(f.specimens, f.properties); return model.pair(model.rows[0]!.identity, model.rows[1]!.identity); }
const invalid = (kind: string) => (e: unknown) => e instanceof ScientificReadFailure && e.kind === kind;

test("same nominal candidate retains different prepared states and samples", () => {
  const result = pair();
  assert.equal(result.differences.find(d => d.field === "candidate")?.relationship, "same");
  assert.equal(result.differences.find(d => d.field === "prepared_state")?.relationship, "different");
  assert.equal(result.differences.find(d => d.field === "sample")?.relationship, "different");
  assert.equal(result.contextIdentity, "different"); assert.equal(result.evidenceIdentity, "distinct_records");
  assert.equal(result.reuseAuthority, "owner_policy_required");
});

test("nominal equality cannot fill a sample omitted from the loaded window", () => {
  const f = pages(); f.specimens.rows.pop();
  const model = new ScientificComparison(f.specimens, f.properties);
  assert.equal(model.rows[1]?.specimenContext, "outside_window"); assert.equal(model.rows[1]?.specimen, null);
  assert.equal(model.omittedSpecimens, 1);
  assert.equal(model.pair(model.rows[1]!.identity, model.rows[1]!.identity).contextIdentity, "incomplete");
});

test("method and applicability identity include their full pinned hashes", () => {
  const f = pages(), b = f.properties.rows[1]!.binding.measurement;
  assert.ok(b.method && b.context); b.method.sha256 = "d".repeat(64); b.context.sha256 = "e".repeat(64);
  const result = pair(f);
  assert.equal(result.differences.find(d => d.field === "method")?.relationship, "different");
  assert.equal(result.differences.find(d => d.field === "applicability")?.relationship, "different");
});

test("comparison preserves source order, decimal spelling, missingness and quality flags", () => {
  const f = pages();
  f.properties.rows[0]!.value = { kind: "numeric", quantity: { value: "1.000", unit: "MPa" }, uncertainty: null };
  f.properties.rows[1]!.value = { kind: "missing", reason: "not_reported" };
  f.properties.rows[1]!.quality.flags = ["review_next_campaign"];
  const model = new ScientificComparison(f.specimens, f.properties);
  assert.deepEqual(model.rows.map(r => r.observation.value), f.properties.rows.map(r => r.value));
  assert.deepEqual(model.rows[1]!.observation.quality.flags, ["review_next_campaign"]);
  assert.equal(model.pair(model.rows[0]!.identity, model.rows[1]!.identity).differences.find(d => d.field === "units")?.relationship, "unknown");
  f.properties.rows.reverse(); assert.equal(model.rows[1]!.observation.reference.observation_id, "second-measurement");
});

test("uncertain quality does not turn a comparison into a global eligibility rejection", () => {
  const f = pages(); f.properties.rows[0]!.quality.controls = "failed";
  const model = new ScientificComparison(f.specimens, f.properties), selected = model.rows[0]!;
  const result = model.pair(selected.identity, selected.identity);
  assert.equal(result.evidenceIdentity, "same_pinned_record"); assert.equal(result.contextIdentity, "same");
  assert.equal(result.left.observation.quality.controls, "failed"); assert.equal(result.reuseAuthority, "owner_policy_required");
});

test("cross-experiment pages and foreign embedded evidence never form a pair", () => {
  const f = pages(); f.specimens.request.experiment.revision++;
  assert.throws(() => new ScientificComparison(f.specimens, f.properties), invalid("invalid_response"));
  const other = pages(); other.properties.rows[0]!.binding.measurement.context!.scope.project_id = "foreign";
  assert.throws(() => new ScientificComparison(other.specimens, other.properties), invalid("invalid_response"));
});

test("same sample with conflicting preparation stays visibly unresolved", () => {
  const f = pages(); f.properties.rows[1]!.binding.specimen.material_state!.revision++;
  const model = new ScientificComparison(f.specimens, f.properties);
  assert.equal(model.rows[1]?.specimenContext, "conflicting");
  assert.equal(model.pair(model.rows[1]!.identity, model.rows[1]!.identity).contextIdentity, "incomplete");
});

test("unknown sample and readout remain unknown instead of being inferred", () => {
  const f = pages(); f.properties.rows[1]!.binding.specimen.sample = null; f.properties.rows[1]!.expectation = null;
  const model = new ScientificComparison(f.specimens, f.properties);
  assert.equal(model.rows[1]?.specimenContext, "unbound");
  assert.equal(model.pair(model.rows[0]!.identity, model.rows[1]!.identity).differences.find(d => d.field === "readout")?.relationship, "unknown");
});

test("duplicate or unselected observation identity cannot silently collapse results", () => {
  const f = pages(); f.properties.rows[1]!.reference = f.properties.rows[0]!.reference;
  assert.throws(() => new ScientificComparison(f.specimens, f.properties), invalid("invalid_response"));
  const other = pages(); other.properties.request.observations.pop();
  assert.throws(() => new ScientificComparison(other.specimens, other.properties), invalid("invalid_response"));
  const model = new ScientificComparison(pages().specimens, pages().properties);
  assert.throws(() => model.pair("missing", model.rows[0]!.identity), invalid("invalid_request"));
});

test("series, categories and incompatible scalar units remain separate shapes", () => {
  for (const value of [
    { kind: "series", point_count: 2, x_unit: "s", y_unit: "MPa" },
    { kind: "categorical", label: "reported" },
    { kind: "censored", lower: { quantity: { value: "1", unit: "kPa" }, inclusive: true }, upper: null },
  ] as const) {
    const f = pages(); f.properties.rows[0]!.value = { kind: "numeric", quantity: { value: "1", unit: "MPa" }, uncertainty: null }; f.properties.rows[1]!.value = value;
    assert.equal(pair(f).differences.find(d => d.field === "units")?.relationship, "different");
  }
});
