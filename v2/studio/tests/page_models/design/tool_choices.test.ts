import { test } from "node:test";
import assert from "node:assert/strict";
import type { ReleaseSnapshot } from "../../../src/contracts/authoring.js";
import { ToolChoices } from "../../../src/page_models/design/tool_choices.js";
import { scope } from "../../fixtures/authoring.js";

import { registryFixture as fixture } from "../../fixtures/registry.js";

test("Registry choices join exact compiler pins while retaining distinct execution eligibility", () => {
  const { release, universe } = fixture(), choices = new ToolChoices(universe, [release]);
  assert.equal(choices.snapshot[0]?.authoringAvailable, true);
  assert.equal(choices.snapshot[0]?.executionEligibility, "not_checked");
  assert.deepEqual(choices.select(release.lock.descriptor_sha256).lock, release.lock);
  release.descriptor.tool.purpose = "changed outside";
  choices.snapshot[0]!.release.status = "revoked";
  assert.equal(choices.snapshot[0]?.release.status, "active");
  assert.equal(choices.snapshot[0]?.release.descriptor.tool.purpose, "Synthetic example");
});

test("discoverable unreviewed, inactive and schema-incomplete tools explain unavailable selections", () => {
  for (const reason of ["not_reviewed", "release_inactive", "schema_unavailable"] as const) {
    const { universe, release } = fixture();
    if (reason === "not_reviewed") universe.reviewed_tools = [];
    if (reason === "release_inactive") release.status = "revoked";
    if (reason === "schema_unavailable") universe.schemas = [];
    const choices = new ToolChoices(universe, [release]);
    assert.equal(choices.snapshot[0]?.authoringAvailable, false);
    assert.ok(choices.snapshot[0]?.reasons.includes(reason));
    assert.throws(() => choices.select(release.lock.descriptor_sha256));
  }
});

test("matching capability names do not mask image, descriptor or port/schema drift", () => {
  const changes: ((release: ReleaseSnapshot) => void)[] = [
    value => { value.lock.descriptor_sha256 = "e".repeat(64); },
    value => { value.lock.input_schemas[0]!.schema_ref = { ...value.lock.input_schemas[0]!.schema_ref, version: "1", schema_id: "other" }; },
    value => { value.descriptor.tool.binding = { ...value.descriptor.tool.binding, image_sha256: "e".repeat(64) }; },
    value => { value.descriptor.tool.inputs.push(structuredClone(value.descriptor.tool.inputs[0]!)); },
  ];
  for (const change of changes) {
    const { release, universe } = fixture(); change(release);
    const choices = new ToolChoices(universe, [release]);
    assert.ok(choices.snapshot[0]?.reasons.includes("metadata_mismatch"));
    assert.equal(choices.snapshot[0]?.authoringAvailable, false);
  }
});

test("scoped discovery is bounded and rejects duplicate identity projections", () => {
  const { release, universe } = fixture();
  assert.throws(() => new ToolChoices(universe, [{ ...release, scope: { ...scope, project_id: "foreign" } }]));
  assert.throws(() => new ToolChoices(universe, [release, release]));
  assert.throws(() => new ToolChoices(universe, Array(101).fill(release)));
  assert.throws(() => new ToolChoices({ ...universe, schemas: [...universe.schemas, ...universe.schemas] }, [release]));
  assert.throws(() => new ToolChoices({ ...universe, reviewed_tools: [...universe.reviewed_tools, ...universe.reviewed_tools] }, [release]));
});
