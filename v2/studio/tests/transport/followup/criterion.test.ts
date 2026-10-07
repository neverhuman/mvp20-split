import { test } from "node:test";
import assert from "node:assert/strict";
import records from "../../fixtures/scientific/provenance-question.json" with { type: "json" };
import feedback from "../../fixtures/scientific/feedback.json" with { type: "json" };
import { CriterionClient } from "../../../src/transport/followup/criterion.js";
import type { CriterionRef } from "../../../src/contracts/followup.js";
import { canonical } from "../../../src/transport/scientific/identity.js";
import { digest } from "../../fixtures/followup.js";
const json = (value: unknown) => new Response(JSON.stringify(value), { headers: { "content-type": "application/json" } });
const ref = (): CriterionRef => ({ question: records.question.reference, need: records.need.reference, criterion_id: "c1", assessment: null });
test("unassessed criterion reads exact question and need without inventing assessment", async () => {
  let calls = 0;
  const result = await new CriterionClient(async () => json(++calls === 1 ? records.question : records.need)).load(ref(), new AbortController().signal);
  assert.equal(calls, 2); assert.equal(result.assessment, null);
});
test("criterion membership is required in both owner records", async () => {
  for (const criterion_id of ["absent", "c1"]) {
    let calls = 0; const need = structuredClone(records.need); need.criterion_ids = [];
    await assert.rejects(new CriterionClient(async () => json(++calls === 1 ? records.question : need)).load({ ...ref(), criterion_id }, new AbortController().signal));
  }
});
test("changed assessment status cannot silently replace the pinned digest", async () => {
  const request = { ...feedback.assessment.request, question: records.question.reference, profile: { ...feedback.assessment.request.profile, scope: records.question.reference.scope } };
  const status = { wire_version: "1", request, actor_id: "fixture-reader", outcome: { status: "pending" } };
  const criterion = { ...ref(), assessment: { request, status_sha256: digest(canonical(status)) } } as CriterionRef;
  for (const valid of [true, false]) {
    let calls = 0;
    const client = new CriterionClient(async () => json(++calls === 1 ? records.question : calls === 2 ? records.need : valid ? status : { ...status, actor_id: "different-reader" }));
    if (valid) assert.equal((await client.load(criterion, new AbortController().signal)).assessment?.outcome.status, "pending");
    else await assert.rejects(client.load(criterion, new AbortController().signal));
  }
});
