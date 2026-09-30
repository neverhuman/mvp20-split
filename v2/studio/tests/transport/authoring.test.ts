import { test } from "node:test";
import assert from "node:assert/strict";
import { Submission } from "../../src/transport/submission.js";
import { AuthoringClient, AuthoringFailure } from "../../src/transport/authoring.js";
import type { CommandIdentity, DraftCommandReceipt } from "../../src/contracts/authoring.js";

const signal = () => new AbortController().signal;
const identity = (): CommandIdentity => ({ actor_id: "researcher", command_family: "definition.validate", command_id: "validate1", scope: { tenant_id: "tenant", project_id: "project" } });
const payload = () => ({ draft_id: "draft1", revision: 1, content_sha256: "a".repeat(64) });
const command = () => new Submission("validate", identity(), payload());
const receipt = (): DraftCommandReceipt => ({ outcome: { status: "pending", binding: { identity: identity(), operation_id: "operation1", request_sha256: "b".repeat(64) } } });
const json = (value: unknown) => new Response(JSON.stringify(value), { headers: { "Content-Type": "application/json" } });

test("submission retains immutable original body and explicit identity, not mutable editor objects", () => {
  const id = identity(), data = payload(), submitted = new Submission("validate", id, data), original = submitted.body;
  id.scope.project_id = "other"; data.revision = 2; submitted.identity.command_id = "other";
  assert.equal(submitted.body, original);
  submitted.verify(receipt());
  assert.throws(() => submitted.verify({ outcome: { ...receipt().outcome, binding: { ...receipt().outcome.binding, identity: { ...identity(), command_id: "other" } } } }));
  assert.throws(() => new Submission("validate", { ...identity(), command_family: "definition.save" }, payload()));
  for (const revision of [NaN, Infinity, 1.5, Number.MAX_SAFE_INTEGER + 1]) assert.throws(() => new Submission("validate", identity(), { ...payload(), revision }));
  assert.throws(() => new Submission("cancel", { ...identity(), command_family: "runtime.cancel" }, { run_id: "run", reason_code: "stop" }));
});

test("lost acknowledgement stays unresolved and original receipt lookup sends no second command", async () => {
  const calls: { path: string; init: RequestInit | undefined }[] = [];
  const fetcher: typeof fetch = async (input, init) => {
    calls.push({ path: String(input), init });
    if (calls.length === 1) throw new Error("private backend detail");
    return json(receipt());
  };
  const client = new AuthoringClient(fetcher), submitted = command();
  await assert.rejects(client.submit(submitted, signal()), (error: unknown) => error instanceof AuthoringFailure && error.kind === "network" && error.commandUnresolved && !error.message.includes("private"));
  assert.equal(calls.length, 1);
  assert.equal((await client.receipt(submitted, signal())).outcome.status, "pending");
  assert.equal(calls[0]?.init?.body, submitted.body);
  assert.equal(calls[0]?.init?.credentials, "same-origin");
  assert.equal(calls[0]?.init?.redirect, "error");
  assert.equal(new Headers(calls[0]?.init?.headers).has("Authorization"), false);
  assert.equal(calls[1]?.path, "/api/runtime/v1/definition-commands/definition.validate/validate1");
  assert.equal(calls[1]?.init?.method, "GET");
});

test("mismatched receipts never become an acknowledgement; invalid bodies remain unresolved", async () => {
  const wrong = receipt(); wrong.outcome.binding.identity.scope.project_id = "other";
  for (const response of [json(wrong), new Response("private", { status: 403 }), new Response("[]", { headers: { "Content-Type": "text/html" } }), json({ ...receipt(), extra: true })]) {
    const client = new AuthoringClient(async () => response);
    await assert.rejects(client.submit(command(), signal()), (error: unknown) => error instanceof AuthoringFailure && error.commandUnresolved);
  }
});

test("pre-dispatch abort is distinct from an unknown submitted outcome; timeout performs no retry", async () => {
  let calls = 0;
  const client = new AuthoringClient(async (_input, init) => {
    calls++;
    return new Promise((_resolve, reject) => init?.signal?.addEventListener("abort", () => reject(new Error("abort")), { once: true }));
  }, "/api/runtime", "/api/registry", 5);
  const controller = new AbortController(); controller.abort();
  await assert.rejects(client.submit(command(), controller.signal), (error: unknown) => error instanceof AuthoringFailure && error.kind === "aborted" && !error.commandUnresolved);
  assert.equal(calls, 0);
  await assert.rejects(client.submit(command(), signal()), (error: unknown) => error instanceof AuthoringFailure && error.kind === "timeout" && error.commandUnresolved);
  assert.equal(calls, 1);
});

test("metadata reads preserve full schema identity and use separate same-origin Registry routing", async () => {
  const urls: string[] = [];
  const client = new AuthoringClient(async input => { urls.push(String(input)); return new Response(null, { status: 404 }); });
  const reference = { schema_id: "example", version: "1" as const, sha256: "a".repeat(64) };
  await assert.rejects(client.schema(reference, "b".repeat(64), signal()));
  const url = new URL(urls[0]!, "http://localhost");
  assert.equal(url.searchParams.get("schema_id"), "example");
  assert.equal(url.searchParams.get("universe_sha256"), "b".repeat(64));
  await assert.rejects(client.releases(undefined, signal()));
  assert.equal(urls[1], "/api/registry/v1/releases?limit=50");
  for (const base of ["https://other", "//other", "/\\other", "/api?redirect=other"]) assert.throws(() => new AuthoringClient(fetch, base));
});

test("missing receipt keeps original command unresolved; streamed body limits apply to writes", async () => {
  const missing = new AuthoringClient(async () => new Response(null, { status: 404 }));
  await assert.rejects(missing.receipt(command(), signal()), (error: unknown) => error instanceof AuthoringFailure && error.kind === "unavailable" && error.commandUnresolved);
  const oversized = new AuthoringClient(async () => json(receipt()), "/api/runtime", "/api/registry", 1000, 32);
  await assert.rejects(oversized.submit(command(), signal()), (error: unknown) => error instanceof AuthoringFailure && error.kind === "invalid_response" && error.commandUnresolved);
});
