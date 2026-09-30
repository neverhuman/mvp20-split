import { test } from "node:test";
import assert from "node:assert/strict";
import { SchemaFields } from "../../../src/page_models/design/schema_fields.js";

test("schema fields derive scalar controls while structured inputs remain explicit bindings", () => {
  const form = new SchemaFields({ type: "object", additionalProperties: false, required: ["gain", "samples"], properties: {
    gain: { type: "number", minimum: 0, maximum: 2 }, samples: { type: "array", items: { type: "number" }, maxItems: 20 },
    version: { type: "string", const: "1" }, enabled: { type: "boolean" }, mode: { type: "string", enum: ["a", "b"] },
  } });
  assert.equal(form.unavailable, undefined);
  assert.deepEqual(form.constant("gain", "1.25"), { kind: "number", value: 1.25 });
  assert.deepEqual(form.constant("enabled", "false"), { kind: "boolean", value: false });
  assert.equal(form.snapshot.fields.find(field => field.name === "samples")?.kind, "binding");
  for (const [name, text] of [["gain", "3"], ["gain", "1e-9999"], ["samples", "[]"], ["version", "2"], ["mode", "c"], ["enabled", "0"], ["unknown", "1"]])
    assert.throws(() => form.constant(name!, text!));
});

test("local scalar definitions preserve constraints; remote and cyclic refs never fetch", () => {
  const form = new SchemaFields({ type: "object", additionalProperties: false, $defs: {
    count: { type: "integer", minimum: 1, maximum: 10 }, loop: { $ref: "#/$defs/loop" },
  }, properties: { count: { $ref: "#/$defs/count" }, cyclic: { $ref: "#/$defs/loop" }, remote: { $ref: "https://untrusted.invalid/schema" } } });
  assert.deepEqual(form.constant("count", "2"), { kind: "integer", value: 2 });
  assert.throws(() => form.constant("count", "1.00000000000001"));
  assert.equal(form.snapshot.fields.filter(field => field.kind === "binding").length, 2);
});

test("unsupported whole-object constraints cannot masquerade as supported forms", () => {
  for (const schema of [{ type: "array" }, { type: "object", additionalProperties: true, properties: {} },
    { type: "object", additionalProperties: false, properties: {}, anyOf: [] },
    { type: "object", additionalProperties: false, properties: {}, required: ["missing"] }])
    assert.ok(new SchemaFields(schema).unavailable);
  const form = new SchemaFields({ type: "object", additionalProperties: false, properties: { name: { type: "string", minLength: 2 } } });
  assert.throws(() => form.constant("name", "a"));
  form.snapshot.fields[0]!.name = "mutated";
  assert.equal(form.snapshot.fields[0]?.name, "name");
});
