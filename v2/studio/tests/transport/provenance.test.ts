import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { createServer } from "node:http";
import { once } from "node:events";
import type { AddressInfo } from "node:net";
import { DataProvenanceClient } from "../../src/transport/provenance/data.js";
import { verifyText } from "../../src/transport/provenance/integrity.js";
import { ScientificHTTP } from "../../src/transport/scientific/http.js";
import { ScientificReadFailure } from "../../src/transport/scientific/failure.js";
import { decodeProvenance } from "../../src/contracts/scientific/provenance.js";
import traceFixture from "../fixtures/scientific/provenance-trace.json" with { type: "json" };

const digest = (bytes: Uint8Array) => createHash("sha256").update(bytes).digest("hex");
const signal = () => new AbortController().signal;
const failure = (kind: string) => (error: unknown) => error instanceof ScientificReadFailure && error.kind === kind;
const json = (value: unknown) => new Response(JSON.stringify(value), { headers: { "content-type": "application/json" } });

function fixture(text = "\uFEFFmass: \u03bcg\n") {
  const bytes = new TextEncoder().encode(text);
  const scope = { tenant_id: "synthetic", project_id: "provenance" };
  const raw = { artifact_id: "raw:1", scope, sha256: digest(bytes), size_bytes: bytes.length,
    media_type: "text/plain", schema_ref: { schema_id: "fixture", version: "1", sha256: "a".repeat(64) } };
  const reference = { scope, source_id: "document:1", revision_id: "revision:1", raw };
  const span = decodeProvenance("span", { source: reference, unit: "byte", start: 0, end: bytes.length, sha256: digest(bytes) });
  const source = decodeProvenance("source", { wire_version: "1", reference,
    delivery: { issuer_id: "fixture", delivery_id: "delivery-1" },
    method: { connector_id: "document", connector_version: "1", configuration_sha256: "b".repeat(64), format: "utf8_document" },
    rights: { scope, rights_id: "fixture-rights", revision: 1 }, supersedes: null, completeness: "unknown" });
  return { bytes, span, source, raw };
}

test("source display verifies full artifact and selected byte hashes, preserving BOM and Unicode", async () => {
  const f = fixture();
  const calls: string[] = [];
  const client = new DataProvenanceClient(async (path, options) => {
    calls.push(String(path));
    assert.equal(options?.method, "GET");
    assert.equal(options?.body, undefined);
    assert.equal(options?.credentials, "same-origin");
    assert.equal(options?.redirect, "error");
    if (String(path).endsWith("/content")) return new Response(f.bytes, { headers: { "content-type": "text/plain; charset=utf-8" } });
    return json(String(path).includes("/sources/") ? f.source : f.raw);
  });
  const result = await client.span(f.span, signal());
  assert.equal(result.text, "\uFEFFmass: \u03bcg\n");
  assert.equal(result.artifact_sha256, digest(f.bytes));
  assert.deepEqual(calls, ["/api/data/v1/acquisition/sources/document%3A1/revision%3A1", "/api/data/v1/artifacts/raw%3A1", "/api/data/v1/artifacts/raw%3A1/content"]);
  f.span.end = 0;
  assert.equal(result.span.end, f.bytes.length);
});

test("historical metadata cannot authorize denied content", async () => {
  const f = fixture();
  const client = new DataProvenanceClient(async path => String(path).endsWith("/content") ? new Response("", { status: 403 }) : json(String(path).includes("/sources/") ? f.source : f.raw));
  await assert.rejects(client.span(f.span, signal()), failure("denied"));
});

test("native HTTP verifies source bytes without sending owner credentials", async () => {
  const f = fixture();
  const server = createServer((request, response) => {
    assert.equal(request.method, "GET"); assert.equal(request.headers.authorization, undefined);
    if (request.url?.endsWith("/content")) { response.setHeader("content-type", "text/plain"); response.end(f.bytes); }
    else { response.setHeader("content-type", "application/json"); response.end(JSON.stringify(request.url?.includes("/sources/") ? f.source : f.raw)); }
  });
  server.listen(0, "127.0.0.1"); await once(server, "listening");
  const origin = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
  try {
    const client = new DataProvenanceClient((path, options) => fetch(origin + String(path), options));
    assert.equal((await client.span(f.span, signal())).text, "\uFEFFmass: \u03bcg\n");
  } finally { server.closeAllConnections(); await new Promise<void>(done => server.close(() => done())); }
});

test("unsupported media and inspector bounds fail before any network read", async () => {
  let calls = 0;
  const client = new DataProvenanceClient(async () => { calls++; return json({}); });
  const f = fixture();
  const binary = structuredClone(f.span); binary.source.raw.media_type = "application/octet-stream";
  await assert.rejects(client.span(binary, signal()), failure("unavailable"));
  const large = structuredClone(f.span); large.source.raw.size_bytes = 4194305;
  await assert.rejects(client.span(large, signal()), failure("limit"));
  const wide = structuredClone(f.span); wide.source.raw.size_bytes = 65537; wide.end = 65537;
  await assert.rejects(client.span(wide, signal()), failure("limit"));
  const reversed = structuredClone(f.span); reversed.start = reversed.end + 1;
  await assert.rejects(client.span(reversed, signal()), failure("invalid_request"));
  assert.equal(calls, 0);
});

test("trace identity reproduces the independent Python canonical digest", async () => {
  const ref = decodeProvenance("trace_ref", traceFixture.reference);
  const client = new DataProvenanceClient(async () => json(traceFixture.trace));
  assert.deepEqual(await client.trace(ref, signal()), traceFixture.trace);
  await assert.rejects(client.trace({ ...ref, sha256: "0".repeat(64) }, signal()), failure("invalid_response"));
  const changed = structuredClone(traceFixture.trace); changed.transforms[0]!.version = "2";
  await assert.rejects(new DataProvenanceClient(async () => json(changed)).trace(ref, signal()), failure("invalid_response"));
});

test("derivation keeps exact output, origin scope and every input scope", async () => {
  const raw = fixture().span.source.raw;
  const receipt = decodeProvenance("derivation", { artifact: raw, schema_version: "1", upload_id: "upload", request_sha256: "c".repeat(64),
    origin: { schema_version: "1", scope: raw.scope, actor_id: "fixture", command_family: "derive", command_id: "command" },
    declaration: { schema_version: "1", transformation: { transformation_id: "copy", version: "1", sha256: "b".repeat(64) }, inputs: [raw] } });
  assert.deepEqual(await new DataProvenanceClient(async () => json(receipt)).derivation(raw, signal()), receipt);
  const changed = structuredClone(receipt); changed.declaration.inputs[0]!.scope.project_id = "foreign";
  await assert.rejects(new DataProvenanceClient(async () => json(changed)).derivation(raw, signal()), failure("invalid_response"));
});

test("size, whole hash, span hash and invalid UTF8 never produce displayed text", async () => {
  const f = fixture();
  for (const mutate of [
    (s: typeof f.span) => { s.source.raw.size_bytes++; },
    (s: typeof f.span) => { s.source.raw.sha256 = "0".repeat(64); },
    (s: typeof f.span) => { s.sha256 = "0".repeat(64); },
    (s: typeof f.span) => { s.end++; },
  ]) {
    const span = structuredClone(f.span); mutate(span);
    await assert.rejects(verifyText(span, f.bytes, signal()), failure("invalid_response"));
  }
  const split = structuredClone(f.span); split.start = 1; split.end = 2; split.sha256 = digest(f.bytes.slice(1, 2));
  await assert.rejects(verifyText(split, f.bytes, signal()), failure("invalid_response"));
  const empty = structuredClone(f.span); empty.start = 1; empty.end = 1; empty.sha256 = digest(new Uint8Array());
  assert.equal((await verifyText(empty, f.bytes, signal())).text, "");
  const cancelled = new AbortController(); cancelled.abort();
  await assert.rejects(verifyText(f.span, f.bytes, cancelled.signal), failure("aborted"));
});

test("unreviewed and noncanonical routes never reach fetch", async () => {
  let calls = 0;
  const http = new ScientificHTTP(async () => { calls++; return json({}); });
  for (const path of ["https://example.com/source", "/api/data/v1/artifacts/../secret", "/api/data/v1/artifacts/%2Fsecret", "/api/data/v1/artifacts/%61", "/api/data/v1/artifacts/a?next=b", "/api/data/v1/acquisition/sources/a/b/c"]) {
    await assert.rejects(http.get(path, x => x, signal()), failure("invalid_request"));
  }
  assert.equal(calls, 0);
});

test("source response and current metadata must match every pinned reference field", async () => {
  const f = fixture();
  const source = structuredClone(f.source); source.reference.revision_id = "other";
  await assert.rejects(new DataProvenanceClient(async () => json(source)).source(f.source.reference, signal()), failure("invalid_response"));
  const raw = structuredClone(f.raw); raw.sha256 = "0".repeat(64);
  await assert.rejects(new DataProvenanceClient(async () => json(raw)).artifact(f.span.source.raw, signal()), failure("invalid_response"));
});

test("content media, declared length and streamed length must agree with pinned artifact", async () => {
  for (const [body, headers] of [
    ["abc", { "content-type": "text/html" }],
    ["abc", { "content-type": "text/plain", "content-length": "4" }],
    ["abcd", { "content-type": "text/plain" }],
    ["ab", { "content-type": "text/plain" }],
  ] as const) {
    const http = new ScientificHTTP(async () => new Response(body, { headers }));
    await assert.rejects(http.content("/api/data/v1/artifacts/a/content", 3, "text/plain", signal()), failure("invalid_response"));
  }
});

