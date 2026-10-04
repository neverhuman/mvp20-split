import { test } from "node:test";
import assert from "node:assert/strict";
import { createServer } from "node:http";
import { once } from "node:events";
import type { AddressInfo } from "node:net";
import { KnowledgeClient } from "../../src/transport/scientific/knowledge.js";
import { ResearchClient } from "../../src/transport/scientific/research.js";
import { ScientificHTTP } from "../../src/transport/scientific/http.js";
import { ScientificReadFailure } from "../../src/transport/scientific/failure.js";
import { decodeKnowledge } from "../../src/contracts/scientific/knowledge.js";
import { decodeResearch } from "../../src/contracts/scientific/research.js";
import knowledge from "../fixtures/scientific/knowledge.json" with { type: "json" };
import research from "../fixtures/scientific/research.json" with { type: "json" };

const signal = () => new AbortController().signal;
const response = (value: unknown) => new Response(JSON.stringify(value), { headers: { "content-type": "application/json" } });
const failure = (kind: string) => (error: unknown) => error instanceof ScientificReadFailure && error.kind === kind;
const search = () => decodeKnowledge("search_request", structuredClone(knowledge.search_request));
const properties = () => decodeResearch("property_request", structuredClone(research.property_request));

test("scientific clients use only their reviewed same-origin owner routes", async () => {
  const seen: string[] = [];
  const replies: Record<string, unknown> = {
    "/api/knowledge/v1/graph-explore/catalog": knowledge.catalog,
    "/api/knowledge/v1/graph-explore/entities": knowledge.search_page,
    "/api/knowledge/v1/graph-explore/neighborhood": knowledge.neighborhood_page,
    "/api/knowledge/v1/graph-explore/object": knowledge.object_detail,
    "/api/research/v1/research-explore/catalog": research.catalog,
    "/api/research/v1/research-explore/specimens": research.specimen_page,
    "/api/research/v1/research-explore/properties": research.property_page,
    "/api/research/v1/research-explore/observation-series": research.series_page,
  };
  const server = createServer(async (request, reply) => {
    assert.equal(request.method, "POST");
    assert.equal(request.headers.authorization, undefined);
    assert.equal(request.headers["content-type"], "application/json");
    for await (const _chunk of request) { /* consume bounded fixture request */ }
    seen.push(request.url!);
    reply.setHeader("content-type", "application/json");
    reply.end(JSON.stringify(replies[request.url!]));
  });
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  const origin = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
  const fetcher: typeof fetch = (path, options) => {
    assert.equal(options?.credentials, "same-origin"); assert.equal(options?.redirect, "error");
    return fetch(origin + String(path), options);
  };
  try {
    const k = new KnowledgeClient(fetcher), r = new ResearchClient(fetcher);
    assert.deepEqual(await k.catalog(search().revision, signal()), knowledge.catalog);
    assert.deepEqual(await k.search(search(), signal()), knowledge.search_page);
    assert.deepEqual(await k.neighborhood(decodeKnowledge("neighborhood_request", knowledge.neighborhood_request), signal()), knowledge.neighborhood_page);
    assert.deepEqual(await k.detail(decodeKnowledge("object_request", knowledge.object_request), signal()), knowledge.object_detail);
    assert.deepEqual(await r.catalog(properties().experiment, signal()), research.catalog);
    assert.deepEqual(await r.specimens(decodeResearch("specimen_request", research.specimen_request), signal()), research.specimen_page);
    assert.deepEqual(await r.properties(properties(), signal()), research.property_page);
    assert.deepEqual(await r.series(decodeResearch("series_request", research.series_request), signal()), research.series_page);
    assert.deepEqual(new Set(seen), new Set(Object.keys(replies)));
  } finally { server.closeAllConnections(); await new Promise<void>(done => server.close(() => done())); }
});

test("omitted documented defaults match owner golden fingerprint without mutating caller", async () => {
  const input = { wire_version: "1" as const, revision: search().revision };
  const original = structuredClone(input);
  const client = new KnowledgeClient(async (_path, options) => {
    assert.deepEqual(JSON.parse(String(options?.body)), knowledge.search_request);
    return response(knowledge.search_page);
  });
  await client.search(input, signal());
  assert.deepEqual(input, original);
});

test("wrong response revision, digest, scope, row count and catalog pins are rejected", async () => {
  for (const mutate of [
    (v: typeof knowledge.search_page) => { v.request.revision.revision++; },
    (v: typeof knowledge.search_page) => { v.query_sha256 = "0".repeat(64); },
    (v: typeof knowledge.search_page) => { v.entities[0]!.reference.graph.scope.project_id = "foreign"; },
    (v: typeof knowledge.search_page) => { v.entities = []; },
  ]) {
    const value = structuredClone(knowledge.search_page); mutate(value);
    await assert.rejects(new KnowledgeClient(async () => response(value)).search(search(), signal()), failure("invalid_response"));
  }
  const catalog = structuredClone(knowledge.catalog); catalog.views[0]!.result_schema.sha256 = "0".repeat(64);
  await assert.rejects(new KnowledgeClient(async () => response(catalog)).catalog(search().revision, signal()), failure("invalid_response"));
  const value = structuredClone(research.property_page); value.rows[0]!.reference.revision++;
  await assert.rejects(new ResearchClient(async () => response(value)).properties(properties(), signal()), failure("invalid_response"));
});

test("foreign reported binding remains a claim while authoritative row identity stays pinned", async () => {
  const value = decodeResearch("property_page", structuredClone(research.property_page));
  value.rows[0]!.binding.target.experiment!.scope.project_id = "claimed-other-project";
  value.rows[0]!.context_link = "different_experiment"; value.rows[0]!.expectation = null;
  const page = await new ResearchClient(async () => response(value)).properties(properties(), signal());
  assert.equal(page.rows[0]!.binding.target.experiment!.scope.project_id, "claimed-other-project");
});

test("invalid input, duplicate selections and retargeted positions never issue a fetch", async () => {
  let calls = 0;
  const fetcher: typeof fetch = async () => { calls++; return response({}); };
  await assert.rejects(new KnowledgeClient(fetcher).search({ ...search(), limit: 51 }, signal()), failure("invalid_request"));
  await assert.rejects(new KnowledgeClient(fetcher).search({ ...search(), position: { query_sha256: "0".repeat(64), entity_offset: 0, assertion_offset: 0 } }, signal()), failure("query_conflict"));
  const query = properties(); query.observations.push(structuredClone(query.observations[0]!));
  await assert.rejects(new ResearchClient(fetcher).properties(query, signal()), failure("invalid_request"));
  await assert.rejects(new ScientificHTTP(fetcher).post("https://external.invalid", {}, v => v, signal()), failure("invalid_request"));
  assert.equal(calls, 0);
});

for (const [status, kind] of [[401, "denied"], [403, "denied"], [404, "unavailable"], [409, "query_conflict"], [413, "limit"], [422, "invalid_request"], [503, "network"]] as const)
  test(`scientific HTTP ${status} maps to sanitized ${kind}`, async () => {
    await assert.rejects(new KnowledgeClient(async () => new Response("private owner error", { status })).search(search(), signal()), failure(kind));
  });

test("malformed, oversized and invalid UTF-8 responses fail closed", async () => {
  for (const make of [() => response({}), () => new Response("{}", { headers: { "content-type": "text/html" } }),
    () => new Response(new Uint8Array([255]), { headers: { "content-type": "application/json" } }),
    () => new Response("{}", { headers: { "content-type": "application/json", "content-length": "1048577" } }),
    () => response({ value: "x".repeat(1048576) })]) {
    await assert.rejects(new KnowledgeClient(async () => make()).search(search(), signal()), failure("invalid_response"));
  }
});

test("cancellation and timeout include delayed fetch and prevent late successful delivery", async () => {
  const pending: typeof fetch = (_path, options) => new Promise((_resolve, reject) => options!.signal!.addEventListener("abort", () => reject(new Error("aborted")), { once: true }));
  await assert.rejects(new KnowledgeClient(pending, 5).search(search(), signal()), failure("timeout"));
  const controller = new AbortController(); controller.abort();
  await assert.rejects(new KnowledgeClient(async () => { throw new Error("must not fetch"); }).search(search(), controller.signal), failure("aborted"));
  const delayed = new AbortController();
  const client = new KnowledgeClient(async () => { delayed.abort(); return response(knowledge.search_page); });
  await assert.rejects(client.search(search(), delayed.signal), failure("aborted"));
});

test("actual streamed HTTP body remains within the caller deadline", async () => {
  let sent = false;
  const server = createServer((_request, reply) => {
    reply.setHeader("content-type", "application/json");
    reply.write("{"); sent = true;
    // The body intentionally never finishes; disconnect is the cleanup boundary.
  });
  server.listen(0, "127.0.0.1"); await once(server, "listening");
  const origin = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
  try {
    const client = new KnowledgeClient((path, options) => fetch(origin + String(path), options), 150);
    await assert.rejects(client.search(search(), signal()), failure("timeout"));
    assert.equal(sent, true);
  } finally { server.closeAllConnections(); await new Promise<void>(done => server.close(() => done())); }
});
