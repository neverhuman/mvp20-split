import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { decodeAuthoring } from "../../src/contracts/authoring.js";
import type { DefinitionUniverse } from "../../src/contracts/authoring.js";
import { reviewedSchema } from "../../src/contracts/reviewed_schema.js";

const scope = { tenant_id: "tenant", project_id: "project" };
function material(bytes: Uint8Array = new TextEncoder().encode('{"type":"object"}')) {
  const reference = { schema_id: "example", version: "1" as const, sha256: createHash("sha256").update(bytes).digest("hex") };
  const universe: DefinitionUniverse = { scope, universe_sha256: "a".repeat(64), authority: "compiler_configuration", reviewed_tools: [], schemas: [reference] };
  return { universe, reference, record: { scope, universe_sha256: universe.universe_sha256, reference, schema_bytes_base64: Buffer.from(bytes).toString("base64") } };
}

test("authoring generation pins fourteen published roots without changing observation ownership", async () => {
  const manifest = JSON.parse(await readFile("src/contracts/generated/authoring/manifest.json", "utf8")) as Record<string, { source: string; sha256: string }>;
  assert.deepEqual(Object.keys(manifest).sort(), ["admit", "cancel", "draft", "execution_receipt", "identity", "page", "receipt", "release", "releases", "save", "schema", "universe", "validate", "validation"]);
  for (const entry of Object.values(manifest)) assert.equal(createHash("sha256").update(await readFile("../" + entry.source)).digest("hex"), entry.sha256);
});

test("authoring schemas reject coercion and extra fields without mutating received metadata", () => {
  const { universe } = material(), original = structuredClone(universe);
  assert.equal(decodeAuthoring("universe", universe), universe);
  assert.deepEqual(universe, original);
  assert.throws(() => decodeAuthoring("universe", { ...universe, authority: "execution_eligible" }));
  assert.throws(() => decodeAuthoring("validate", { draft_id: "draft", revision: "1", content_sha256: "a".repeat(64) }));
  assert.throws(() => decodeAuthoring("universe", { ...universe, surprise: true }));
});

test("schema verification requires exact scope, universe, full reference and retained byte digest", async () => {
  const { universe, reference, record } = material();
  assert.deepEqual(await reviewedSchema(record, universe, reference), { type: "object" });
  for (const bad of [
    { ...record, scope: { ...scope, project_id: "other" } },
    { ...record, universe_sha256: "b".repeat(64) },
    { ...record, reference: { ...reference, schema_id: "other" } },
    { ...record, schema_bytes_base64: Buffer.from('{"type":"string"}').toString("base64") },
  ]) await assert.rejects(reviewedSchema(bad, universe, reference));
  await assert.rejects(reviewedSchema(record, { ...universe, schemas: [] }, reference));
});

test("schema verification rejects noncanonical base64, oversize bytes, invalid UTF8 and non-object JSON", async () => {
  const fixture = material(new TextEncoder().encode("{}"));
  await assert.rejects(reviewedSchema({ ...fixture.record, schema_bytes_base64: "e31=" }, fixture.universe, fixture.reference));
  for (const bytes of [new Uint8Array(65_537), new Uint8Array([255, 255, 255]), new TextEncoder().encode("[]"), new TextEncoder().encode("null")]) {
    const { universe, reference, record } = material(bytes);
    await assert.rejects(reviewedSchema(record, universe, reference));
  }
});
