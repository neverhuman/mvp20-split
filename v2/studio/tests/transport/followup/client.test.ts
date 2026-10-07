import { test } from "node:test";
import assert from "node:assert/strict";
import { FollowupClient } from "../../../src/transport/followup/client.js";
import { ScientificReadFailure } from "../../../src/transport/scientific/failure.js";
import { fixture, digest } from "../../fixtures/followup.js";
import { canonical } from "../../../src/transport/scientific/identity.js";
const json = (value: unknown) => new Response(JSON.stringify(value), { headers: { "content-type": "application/json" } });
const signal = () => new AbortController().signal;
const fails = (kind: string) => (error: unknown) => error instanceof ScientificReadFailure && error.kind === kind;
test("exact retained proposal requires independent content permission and matching bytes", async () => {
  const f = fixture(), paths: string[] = [];
  const client = new FollowupClient(async (path, options) => {
    paths.push(String(path)); assert.equal(options?.credentials, "same-origin");
    return paths.length === 1 ? json(f.record) : paths.length === 2 ? json(f.record.capture) : json(f.document);
  });
  const result = await client.load(f.selection, signal());
  assert.equal(result.document?.kind, "followup"); assert.equal(paths.length, 3);
  assert.match(paths[0]!, /runtime\/v1\/supervision\/responses\//); assert.match(paths[2]!, /\/content$/);
});
test("content denial clears access even when Runtime exposes the proposal", async () => {
  const f = fixture(); let calls = 0;
  const client = new FollowupClient(async () => ++calls === 1 ? json(f.record) : calls === 2 ? json(f.record.capture) : new Response(null, { status: 403 }));
  await assert.rejects(client.load(f.selection, signal()), fails("denied")); assert.equal(calls, 3);
});
test("response digest and selected request binding reject before Data reads", async () => {
  for (const rehash of [false, true]) {
    const f = fixture(); f.record.request_sha256 = "f".repeat(64);
    if (rehash) f.selection.response.response_sha256 = digest(canonical(f.record));
    let calls = 0;
    await assert.rejects(new FollowupClient(async () => { calls++; return json(f.record); }).load(f.selection, signal()), fails("invalid_response"));
    assert.equal(calls, 1);
  }
});
test("changed content cannot borrow a valid retained proposal", async () => {
  const f = fixture(); let calls = 0;
  await assert.rejects(new FollowupClient(async () => ++calls === 1 ? json(f.record) : calls === 2 ? json(f.record.capture) : json({ ...f.document, rationale: "tampered" })).load(f.selection, signal()), fails("invalid_response"));
});
test("unknown exact profile remains unsupported after permission checks", async () => {
  const f = fixture(); f.record.observation.proposal!.output_schema.sha256 = "e".repeat(64);
  f.selection.response.response_sha256 = digest(canonical(f.record)); let calls = 0;
  const result = await new FollowupClient(async () => ++calls === 1 ? json(f.record) : calls === 2 ? json(f.record.capture) : json(f.document)).load(f.selection, signal());
  assert.equal(result.document, null); assert.equal(calls, 3);
});
test("individually valid capture and interpretation must agree", async () => {
  const f = fixture(), proposal = f.record.observation.proposal!;
  proposal.payload_json = JSON.stringify({ ...f.document, rationale: "Different interpretation" }); proposal.payload_sha256 = digest(proposal.payload_json);
  f.selection.response.response_sha256 = digest(canonical(f.record)); let calls = 0;
  await assert.rejects(new FollowupClient(async () => ++calls === 1 ? json(f.record) : calls === 2 ? json(f.record.capture) : json(f.document)).load(f.selection, signal()), fails("invalid_response"));
});
test("aborted selection does not read protected content", async () => {
  const controller = new AbortController(); controller.abort(); let calls = 0;
  await assert.rejects(new FollowupClient(async () => { calls++; return json(fixture().record); }).load(fixture().selection, controller.signal), fails("aborted"));
  assert.equal(calls, 0);
});
