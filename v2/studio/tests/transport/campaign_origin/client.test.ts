import { test } from "node:test";
import assert from "node:assert/strict";
import { CampaignOriginClient } from "../../../src/transport/campaign_origin/client.js";
import { ScientificReadFailure } from "../../../src/transport/scientific/failure.js";
import { originScenario } from "../../fixtures/campaign_origin.js";

const signal = () => new AbortController().signal;
const failure = (kind: string) => (error: unknown) => error instanceof ScientificReadFailure && error.kind === kind;

test("exact scoped GET verifies Python-generated canonical origin bytes", async () => {
  const { origin } = originScenario(), expected = origin.origin.draft;
  const client = new CampaignOriginClient(async (url, options) => {
    assert.equal(url, `/api/planning/v1/campaign-origins/${encodeURIComponent(expected.draft_id)}?revision=1&content_sha256=${expected.content_sha256}`);
    assert.equal(options?.method, "GET"); assert.equal(options?.body, undefined);
    assert.equal(options?.credentials, "same-origin"); assert.equal(options?.redirect, "error");
    assert.equal(new Headers(options?.headers).has("Authorization"), false);
    return Response.json(origin);
  });
  assert.deepEqual(await client.read(expected, signal()), origin);
});

test("only a named missing-origin reply establishes no recorded association", async () => {
  const expected = originScenario().origin.origin.draft;
  const missing = new CampaignOriginClient(async () => Response.json({ reason_code: "campaign_origin_not_recorded" }, { status: 404 }));
  assert.equal(await missing.read(expected, signal()), null);
  for (const [status, reason, kind] of [[404, "not_found", "unavailable"], [403, "private", "denied"],
    [422, "campaign_origin_response_limit", "limit"], [409, "campaign_origin_inconsistent", "invalid_response"],
    [503, "private", "unavailable"]] as const) {
    const client = new CampaignOriginClient(async () => Response.json({ reason_code: reason }, { status }));
    await assert.rejects(client.read(expected, signal()), failure(kind));
  }
});

test("changed pins, content and extra provider fields are rejected", async () => {
  for (const change of [(value: ReturnType<typeof originScenario>["origin"]) => { value.origin.proposal.rationale = "changed"; },
    (value: ReturnType<typeof originScenario>["origin"]) => { Object.assign(value.origin.proposal, { raw_prompt: "private" }); }]) {
    const { origin } = originScenario(), expected = structuredClone(origin.origin.draft);
    change(origin);
    const client = new CampaignOriginClient(async () => Response.json(origin));
    await assert.rejects(client.read(expected, signal()), failure("invalid_response"));
  }
  const { origin } = originScenario(), client = new CampaignOriginClient(async () => Response.json(origin));
  await assert.rejects(client.read({ ...origin.origin.draft, revision: 2 }, signal()), failure("invalid_response"));
});

test("response limit and cancellation cannot return retained provenance", async () => {
  const { origin } = originScenario(), expected = origin.origin.draft;
  const oversized = new CampaignOriginClient(async () => new Response("x".repeat(262145), { headers: { "content-type": "application/json" } }));
  await assert.rejects(oversized.read(expected, signal()), failure("invalid_response"));
  const controller = new AbortController(); controller.abort(); let calls = 0;
  const client = new CampaignOriginClient(async () => { calls++; return Response.json(origin); });
  await assert.rejects(client.read(expected, controller.signal), failure("aborted")); assert.equal(calls, 0);
});
