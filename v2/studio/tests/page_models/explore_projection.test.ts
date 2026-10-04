import { test } from "node:test";
import assert from "node:assert/strict";
import { domainScene } from "../../src/page_models/explore/scene.js";
import { measurementText } from "../../src/page_models/explore/measurement.js";
import { decodeKnowledge } from "../../src/contracts/scientific/knowledge.js";
import knowledge from "../fixtures/scientific/knowledge.json" with { type: "json" };

test("domain canvas draws only declared edges between exact returned revisions", () => {
  const page = decodeKnowledge("neighborhood_page", structuredClone(knowledge.neighborhood_page));
  const original = structuredClone(page);
  assert.equal(domainScene(page).edges.length, 0); // The other endpoint is outside this returned window.
  const other = { ...structuredClone(page.entities[0]!), reference: page.assertions[0]!.object, label: "Other concept" };
  page.entities.push(other);
  const scene = domainScene(page);
  assert.equal(scene.edges.length, 1); assert.equal(scene.edges[0]!.label, "correlates with (affirmed)");
  assert.equal(scene.omittedEntities, 0); assert.equal(scene.omittedAssertions, 0);
  page.entities[1]!.reference = { ...other.reference, revision: 2 };
  assert.equal(domainScene(page).edges.length, 0);
  assert.equal(original.entities.length, 1);
});

test("measurement labels preserve lexical precision, units, censor inclusivity and uncertainty", () => {
  assert.equal(measurementText({ kind: "numeric", quantity: { value: "1.2500", unit: "mg/L" }, uncertainty: null }), "1.2500 mg/L");
  assert.equal(measurementText({ kind: "numeric", quantity: { value: "1.00", unit: "mg/L" }, uncertainty: { description: "reported interval",
    lower: { value: "0.90", unit: "mg/L" }, upper: { value: "1.10", unit: "mg/L" } } }), "1.00 mg/L; reported interval: 0.90 mg/L to 1.10 mg/L");
  assert.equal(measurementText({ kind: "censored", lower: null, upper: { inclusive: false, quantity: { value: "0.050", unit: "mg/L" } } }), "< 0.050 mg/L");
  assert.equal(measurementText({ kind: "censored", lower: { inclusive: true, quantity: { value: "2", unit: "s" } }, upper: { inclusive: true, quantity: { value: "3", unit: "s" } } }), ">= 2 s; <= 3 s");
  assert.equal(measurementText({ kind: "missing", reason: "not_reported" }), "Missing: not_reported");
  assert.equal(measurementText({ kind: "categorical", label: "unknown" }), "unknown");
  assert.equal(measurementText({ kind: "series", point_count: 2, x_unit: "s", y_unit: "mg/L" }), "2 points (s, mg/L)");
});
