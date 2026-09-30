import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { EditorCatalog } from "../../../src/page_models/design/editor_catalog.js";
import { AuthoringFailure } from "../../../src/transport/authoring.js";
import type { DefinitionSchema, DefinitionUniverse, ReleasePage } from "../../../src/contracts/authoring.js";
import { scope } from "../../fixtures/authoring.js";
import { registryFixture } from "../../fixtures/registry.js";

function fixture() {
  const { release, universe } = registryFixture();
  const bytes = Buffer.from('{"type":"object","properties":{},"additionalProperties":false}');
  const reference = { schema_id: "numeric-input", version: "1" as const, sha256: createHash("sha256").update(bytes).digest("hex") };
  release.lock.input_schemas[0]!.schema_ref = reference;
  release.descriptor.tool.inputs[0]!.schema_ref = reference;
  universe.reviewed_tools = [structuredClone(release.lock)]; universe.schemas = [reference];
  const record: DefinitionSchema = { reference, scope, universe_sha256: universe.universe_sha256, schema_bytes_base64: bytes.toString("base64") };
  return { release, universe, reference, record };
}

test("editor discovery replaces one bounded page and fetches verified schemas only on selection", async () => {
  const { release, universe, reference, record } = fixture();
  let schemaReads = 0, pages = 0;
  const catalog = new EditorCatalog(scope, {
    universe: async () => universe,
    releases: async after => { pages++; return { items: after ? [] : [release], next_after: after ? null : release.lock.descriptor_sha256 }; },
    schema: async (actual, digest) => { schemaReads++; assert.deepEqual(actual, reference); assert.equal(digest, universe.universe_sha256); return record; },
  });
  await catalog.refresh(); assert.equal(schemaReads, 0); assert.equal(catalog.snapshot.nextAfter, release.lock.descriptor_sha256);
  assert.equal(catalog.select(release.lock.descriptor_sha256).revision, 1);
  await catalog.inspectSchema(reference); assert.equal(catalog.snapshot.schemaPhase, "ready"); assert.equal(schemaReads, 1);
  await catalog.refresh(release.lock.descriptor_sha256); assert.equal(pages, 2); assert.deepEqual(catalog.snapshot.choices, []);
  assert.equal(catalog.snapshot.schema, undefined);
});

test("a refreshed universe fences an uncancellable old schema response", async () => {
  const { release, universe, reference, record } = fixture();
  let finish!: (value: DefinitionSchema) => void;
  const catalog = new EditorCatalog(scope, { universe: async () => universe, releases: async () => ({ items: [release], next_after: null }),
    schema: async () => new Promise(resolve => { finish = resolve; }) });
  await catalog.refresh(); const loading = catalog.inspectSchema(reference);
  await catalog.refresh(); finish(record); await loading;
  assert.equal(catalog.snapshot.schema, undefined); assert.equal(catalog.snapshot.schemaPhase, "idle");
});

test("unreviewed schema requests are blocked locally and universe conflict makes selections stale", async () => {
  const { release, universe, reference } = fixture(); let reads = 0;
  const catalog = new EditorCatalog(scope, { universe: async () => universe, releases: async () => ({ items: [release], next_after: null }),
    schema: async () => { reads++; throw new AuthoringFailure("stale", false); } });
  await catalog.refresh();
  await assert.rejects(catalog.inspectSchema({ ...reference, schema_id: "unknown" })); assert.equal(reads, 0);
  await catalog.inspectSchema(reference); assert.equal(catalog.snapshot.phase, "stale");
  assert.throws(() => catalog.select(release.lock.descriptor_sha256));
});

test("late authorization denial clears metadata even after the sibling read failed first", async () => {
  const { release, universe } = fixture();
  let fail = false, deny!: (error: Error) => void;
  const catalog = new EditorCatalog(scope, {
    universe: async (): Promise<DefinitionUniverse> => { if (fail) throw new AuthoringFailure("network", false); return universe; },
    releases: async (): Promise<ReleasePage> => fail ? new Promise((_resolve, reject) => { deny = reject; }) : { items: [release], next_after: null },
    schema: async () => { throw new Error("unexpected"); },
  });
  await catalog.refresh(); fail = true; await catalog.refresh();
  assert.equal(catalog.snapshot.phase, "stale"); assert.ok(catalog.snapshot.choices?.length);
  deny(new AuthoringFailure("denied", false)); await new Promise(resolve => setImmediate(resolve));
  assert.equal(catalog.snapshot.phase, "denied"); assert.equal(catalog.snapshot.choices, undefined);
  assert.equal(catalog.snapshot.universe, undefined);
});
