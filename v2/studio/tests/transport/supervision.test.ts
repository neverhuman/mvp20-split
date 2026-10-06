import { test } from "node:test";
import assert from "node:assert/strict";
import checkpoints from "../fixtures/supervision/checkpoints.json" with { type: "json" };
import requests from "../fixtures/supervision/requests.json" with { type: "json" };
import context from "../fixtures/supervision/context.json" with { type: "json" };
import responses from "../fixtures/supervision/responses.json" with { type: "json" };
import { SupervisionClient } from "../../src/transport/supervision/client.js";
import { ReadFailure } from "../../src/transport/failure.js";
const binding = { run: checkpoints.snapshot.cut.run_id, scope: checkpoints.snapshot.cut.scope };
const signal = () => new AbortController().signal;
const json = (v: unknown) => new Response(JSON.stringify(v), { headers: { "content-type": "application/json" } });
const failure = (kind: string) => (e: unknown) => e instanceof ReadFailure && e.kind === kind;
test("supervisor requests are bounded same-origin reads with no owner credentials", async () => {
  const fixtures = [checkpoints, requests, context, responses]; let call = 0;
  const client = new SupervisionClient(async (path, options) => {
    assert.match(String(path), /^\/api\/runtime\/v1\/supervision\/runs\/supervision-run\/checkpoints/);
    assert.equal(options?.credentials, "same-origin"); assert.equal(options?.redirect, "error");
    assert.deepEqual(options?.headers, { Accept: "application/json" });
    assert.equal(new URL(String(path), "http://local").searchParams.get("limit"), "10");
    return json(fixtures[call++]);
  });
  await client.checkpoints(binding, null, signal());
  await client.requests(binding, "decision-1", checkpoints.snapshot, null, signal());
  await client.context(binding, "decision-1", context.request_sha256, checkpoints.snapshot, null, signal());
  await client.responses(binding, "decision-1", responses.request_sha256, checkpoints.snapshot, null, signal());
  assert.equal(call, 4);
});
for (const [code, kind] of [[401,"denied"],[403,"denied"],[404,"unavailable"],[409,"resnapshot"],[410,"resnapshot"],[503,"network"]] as const) {
  test(`supervisor ${code} is ${kind}`, async () => {
    await assert.rejects(new SupervisionClient(async () => new Response("secret details", { status: code })).checkpoints(binding,null,signal()),failure(kind));
  });
}
test("schema, nested scope, run, decision, request and epoch mismatches fail closed", async () => {
  for (const mutate of [
    (v: typeof checkpoints) => { v.total = -1; },
    (v: typeof checkpoints) => { v.snapshot.cut.run_id = "foreign"; },
    (v: typeof checkpoints) => { v.items[0]!.reference.scope.project_id = "foreign"; },
  ]) { const value = structuredClone(checkpoints); mutate(value); await assert.rejects(new SupervisionClient(async () => json(value)).checkpoints(binding,null,signal()),failure("invalid_response")); }
  const wrong = structuredClone(requests); wrong.reference.decision_id = "foreign";
  await assert.rejects(new SupervisionClient(async () => json(wrong)).requests(binding,"decision-1",checkpoints.snapshot,null,signal()),failure("invalid_response"));
  const epoch = structuredClone(requests); epoch.snapshot.epoch = "f".repeat(64);
  await assert.rejects(new SupervisionClient(async () => json(epoch)).requests(binding,"decision-1",checkpoints.snapshot,null,signal()),failure("resnapshot"));
  await assert.rejects(new SupervisionClient(async () => json(context)).context(binding,"decision-1","f".repeat(64),checkpoints.snapshot,null,signal()),failure("invalid_response"));
});
test("oversize, invalid JSON and abort do not render; timeout remains distinct", async () => {
  for (const reply of [() => new Response("x".repeat(262145)), () => new Response("not JSON")])
    await assert.rejects(new SupervisionClient(async () => reply()).checkpoints(binding,null,signal()),failure("invalid_response"));
  const aborted = new AbortController(); aborted.abort();
  await assert.rejects(new SupervisionClient(async () => json(checkpoints)).checkpoints(binding,null,aborted.signal),failure("aborted"));
  await assert.rejects(new SupervisionClient(async () => { await new Promise(r=>setTimeout(r,15)); return json(checkpoints); },1).checkpoints(binding,null,signal()),failure("timeout"));
  assert.throws(() => new SupervisionClient(fetch, 0));
});

test("exact committed decision is read without an evidence snapshot",async()=>{
  const winner={schema_version:"1",profile:"checkpoint-decision.v1",reference:requests.reference,revision:1,checkpoint_seed_sha256:"a".repeat(64),outcome:{kind:"fallback",action:"continue_unchanged",reason_code:"checkpoint_provider_unconfigured"}};
  const client=new SupervisionClient(async(path)=>{assert.equal(String(path),"/api/runtime/v1/supervision/decisions/supervision-run/decision-1?");return json(winner);});
  assert.equal((await client.decision(binding,"decision-1",signal())).outcome.kind,"fallback");
});
