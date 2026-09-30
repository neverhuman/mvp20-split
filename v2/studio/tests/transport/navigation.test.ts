import { test } from "node:test";
import assert from "node:assert/strict";
import { ObservationClient } from "../../src/transport/observations.js";
import { scopes, topology, catalog, lineage } from "../fixtures/navigation.js";
import { id } from "../fixtures/observations.js";

test("navigation transport binds scope, snapshot and neighborhood on separate roots", async () => {
  const seen: URL[] = [];
  const client = new ObservationClient(async path => {
    const url = new URL(String(path), "http://localhost"); seen.push(url);
    return new Response(JSON.stringify(url.pathname.endsWith("/topology") ? topology() : scopes()),
      { headers: { "content-type": "application/json" } });
  });
  const signal = new AbortController().signal;
  await client.scopes("run/slash", "snapshot+/", id(9), "cursor+/", signal);
  await client.topology("run/slash", id(100), "snapshot+/", { focus_activation_id: id(1), radius: 2 }, undefined, signal);
  assert.equal(seen[0]!.pathname, "/api/runtime/v1/graph-observations/run%2Fslash/scopes");
  assert.equal(seen[0]!.searchParams.get("parent_activation_id"), id(9));
  assert.equal(seen[0]!.searchParams.get("cursor"), "cursor+/");
  assert.equal(seen[1]!.pathname, `/api/runtime/v1/graph-observations/run%2Fslash/scopes/${id(100)}/topology`);
  assert.equal(seen[1]!.searchParams.get("focus_activation_id"), id(1));
  assert.equal(seen[1]!.searchParams.get("radius"), "2");
  for (const url of seen) {
    assert.equal(url.searchParams.get("snapshot_token"), "snapshot+/");
    assert.equal(url.searchParams.get("limit"), "50");
  }
});

test("catalog and immutable lineage use their own public namespaces", async () => {
  const seen: URL[] = [];
  const client = new ObservationClient(async path => {
    const url = new URL(String(path), "http://localhost"); seen.push(url);
    return new Response(JSON.stringify(url.pathname.endsWith("/views") ? catalog() : lineage()),
      { headers: { "content-type": "application/json" } });
  });
  const signal = new AbortController().signal;
  assert.equal((await client.catalog("run-1", "pin", signal)).views.length, 2);
  assert.equal((await client.lineage("run-1", signal)).predecessor.revision, 8);
  assert.equal(seen[0]!.pathname, "/api/runtime/v1/graph-observations/run-1/views");
  assert.equal(seen[0]!.searchParams.get("snapshot_token"), "pin");
  assert.equal(seen[1]!.pathname, "/api/runtime/v1/graph-runs/run-1/lineage");
});
