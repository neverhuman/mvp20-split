import { test } from "node:test";
import assert from "node:assert/strict";
import { decodeObservation } from "../../src/contracts/observations.js";
import { scopes, topology } from "../fixtures/navigation.js";

test("navigation roots validate without coercion or unknown query options", () => {
  const page = topology(), original = structuredClone(page);
  assert.equal(decodeObservation("topology", page), page);
  assert.deepEqual(page, original);
  assert.equal(decodeObservation("scopes", scopes()).scope_count, 1);
  for (const query of [{ radius: 3 }, { radius: "1" }, { radius: 1, arbitrary: true }])
    assert.throws(() => decodeObservation("topology", { ...page, query }));
  assert.throws(() => decodeObservation("scopes", { ...scopes(), scopes: Array(101).fill(scopes().scopes[0]) }));
  assert.throws(() => decodeObservation("topology", { ...page, edges: [{ ...page.edges[0], route: "inferred" }] }));
});
