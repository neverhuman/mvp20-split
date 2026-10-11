import { test } from "node:test";
import assert from "node:assert/strict";
import { OriginReader } from "../../../src/page_models/campaign_origin/reader.js";
import { OriginResearchReader } from "../../../src/page_models/campaign_origin/research.js";
import { ScientificReadFailure } from "../../../src/transport/scientific/failure.js";
import { originScenario } from "../../fixtures/campaign_origin.js";

const signal = () => new AbortController().signal;
const invalid = (error: unknown) => error instanceof ScientificReadFailure && error.kind === "invalid_response";

test("Planning proposal is independently checked against original Runtime save and draft", async () => {
  const { origin, draft } = originScenario(); let reads = 0;
  const reader = new OriginReader({ read: async () => origin }, {
    draft: async (id, revision) => { assert.equal(id, draft.head.draft_id); assert.equal(revision, 1); reads++; return draft; },
    receipt: async command => { assert.equal(command.action, "save"); reads++; return origin.origin.save.receipt; },
  });
  assert.deepEqual(await reader.read(origin.origin.draft, signal()), origin); assert.equal(reads, 2);
});

test("different Runtime receipt or draft cannot support the provenance", async () => {
  for (const change of ["receipt", "draft"] as const) {
    const { origin, draft } = originScenario(), receipt = structuredClone(origin.origin.save.receipt);
    if (change === "receipt") receipt.outcome.binding.operation_id = "different";
    else draft.head.content_sha256 = "f".repeat(64);
    const reader = new OriginReader({ read: async () => origin }, { draft: async () => draft, receipt: async () => receipt });
    await assert.rejects(reader.read(origin.origin.draft, signal()), invalid);
  }
});

test("Research criteria and need membership use exact independently read records", async () => {
  const { origin, question, need } = originScenario();
  const reader = new OriginResearchReader({ question: async () => question, need: async () => need });
  const records = origin.origin.research.records;
  const first = await reader.read(origin.origin, records.findIndex(row => row.kind === "question"), signal());
  assert.deepEqual(first.question, question); assert.equal(first.need, null);
  const second = await reader.read(origin.origin, records.findIndex(row => row.kind === "need"), signal());
  assert.deepEqual(second.need, need);
  question.criteria[0]!.description = "Changed after the model's context was retained";
  await assert.rejects(reader.read(origin.origin, 0, signal()), invalid);
});

test("missing Planning association does not trigger unrelated Runtime reads", async () => {
  const { origin } = originScenario();
  const reader = new OriginReader({ read: async () => null }, {
    draft: async () => { throw Error("must not read"); }, receipt: async () => { throw Error("must not read"); },
  });
  assert.equal(await reader.read(origin.origin.draft, signal()), null);
});
