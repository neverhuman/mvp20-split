import { test } from "node:test";
import assert from "node:assert/strict";
import { createServer } from "node:http";
import { once } from "node:events";
import type { AddressInfo } from "node:net";
import { ObservationClient } from "../../src/transport/observations.js";
import { ReadFailure } from "../../src/transport/failure.js";
import { snapshot, detail, events, id } from "../fixtures/observations.js";

const signal = () => new AbortController().signal;
const response = (body: unknown) => new Response(JSON.stringify(body), { headers: { "content-type": "application/json" } });
const failure = (kind: string) => (error: unknown) => error instanceof ReadFailure && error.kind === kind;

test("actual HTTP transport encodes identifiers/cursors, stays bounded and sends no owner credential", async () => {
  const seen: string[] = [];
  const server = createServer((request, reply) => {
    assert.equal(request.headers.authorization, undefined);
    seen.push(request.url!);
    reply.setHeader("content-type", "application/json");
    reply.end(JSON.stringify(snapshot()));
  });
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  const origin = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
  const client = new ObservationClient((path, options) => fetch(origin + String(path), options));
  try {
    assert.equal((await client.snapshot("run/slash", { frontier_only: true }, "a+b/c", signal())).nodes.length, 2);
    const url = new URL(seen[0]!, origin);
    assert.ok(url.pathname.endsWith("/run%2Fslash/nodes"));
    assert.equal(url.searchParams.get("cursor"), "a+b/c");
    assert.equal(url.searchParams.get("limit"), "50");
    assert.equal(url.searchParams.get("frontier_only"), "true");
  } finally { server.closeAllConnections(); await new Promise<void>((done) => server.close(() => done())); }
});

test("detail, values and invalidations use separate contract roots", async () => {
  const client = new ObservationClient(async (path) => {
    const url = String(path);
    if (url.includes("/invalidations")) return response(events([2]));
    if (url.includes("/outputs/")) return response({ cut: snapshot().snapshot.cut, activation_id: id(1), port: "result",
      item_count: 0, items: [], next_cursor: null });
    return response(detail(1));
  });
  assert.equal((await client.detail("run-1", id(1), "snapshot", undefined, signal())).node.activation_id, id(1));
  assert.equal((await client.values("run-1", id(1), "result", "snapshot", undefined, signal())).item_count, 0);
  assert.equal((await client.events("run-1", "cursor", signal())).observed_revision, 2);
});

for (const [status, kind] of [[401, "denied"], [403, "denied"], [404, "unavailable"], [409, "resnapshot"], [410, "resnapshot"], [503, "network"]] as const)
  test(`HTTP ${status} maps to sanitized ${kind}`, async () => {
    const client = new ObservationClient(async () => new Response("private backend detail", { status }));
    await assert.rejects(client.snapshot("run", {}, undefined, signal()), failure(kind));
  });

test("JSON, schema, UTF-8 and declared/streamed size failures reject without exposing payload", async () => {
  const make = [() => response({}), () => new Response("bad", { headers: { "content-type": "text/html" } }),
    () => new Response("{", { headers: { "content-type": "application/json" } }),
    () => new Response(new Uint8Array([255]), { headers: { "content-type": "application/json" } }),
    () => new Response("{}", { headers: { "content-type": "application/json", "content-length": "9999" } }),
    () => response({ text: "x".repeat(1000) })];
  for (const create of make) {
    const client = new ObservationClient(async () => create(), "/api/runtime", 1000, 100);
    await assert.rejects(client.snapshot("run", {}, undefined, signal()), failure("invalid_response"));
  }
});

test("caller cancellation and timeout abort the fetch, including already-cancelled requests", async () => {
  let calls = 0;
  const pending: typeof fetch = (_path, options) => new Promise((_resolve, reject) => {
    calls++;
    options!.signal!.addEventListener("abort", () => reject(new DOMException("cancelled", "AbortError")), { once: true });
  });
  const controller = new AbortController();
  const client = new ObservationClient(pending);
  const request = client.snapshot("run", {}, undefined, controller.signal);
  controller.abort();
  await assert.rejects(request, failure("aborted"));
  await assert.rejects(client.snapshot("run", {}, undefined, controller.signal), failure("aborted"));
  assert.equal(calls, 1);
  await assert.rejects(new ObservationClient(pending, "/api/runtime", 5).snapshot("run", {}, undefined, signal()), failure("timeout"));
});

test("transport rejects cross-origin configuration and sanitizes network failures", async () => {
  assert.throws(() => new ObservationClient(fetch, "https://foreign.invalid"));
  assert.throws(() => new ObservationClient(fetch, "//foreign.invalid"));
  const client = new ObservationClient(async () => { throw new Error("secret diagnostic"); });
  await assert.rejects(client.snapshot("run", {}, undefined, signal()), failure("network"));
});
