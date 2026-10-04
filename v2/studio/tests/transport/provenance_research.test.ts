import { test } from "node:test";
import assert from "node:assert/strict";
import { ResearchRecordClient } from "../../src/transport/provenance/research.js";
import { ScientificReadFailure } from "../../src/transport/scientific/failure.js";
import { decodeProvenance } from "../../src/contracts/scientific/provenance.js";
import examples from "../fixtures/scientific/provenance-research.json" with { type: "json" };
import questionExamples from "../fixtures/scientific/provenance-question.json" with { type: "json" };

const signal = () => new AbortController().signal;
const json = (value: unknown) => new Response(JSON.stringify(value), { headers: { "content-type": "application/json" } });
const failure = (kind: string) => (error: unknown) => error instanceof ScientificReadFailure && error.kind === kind;

test("question and evidence need use exact reference reads without asserting an answer", async () => {
  const question = decodeProvenance("question", questionExamples.question), need = decodeProvenance("need", questionExamples.need);
  const client = new ResearchRecordClient(async path => json(String(path).includes("questions") ? question : need));
  assert.deepEqual(await client.question(question.reference, signal()), question);
  assert.deepEqual(await client.need(need.reference, signal()), need);
  await assert.rejects(client.question({ ...question.reference, revision: 2 }, signal()), failure("invalid_response"));
});

test("scientific detail readers preserve exact owner records and requested revisions", async () => {
  const material = decodeProvenance("material", examples["material-state-revision"]);
  const experiment = decodeProvenance("experiment", examples["experiment-definition"]);
  const observation = decodeProvenance("observation", examples["observation-revision"]);
  const replies: Record<string, unknown> = {
    "/api/research/v1/material-states/read": material,
    "/api/research/v1/experiments/read": experiment,
    "/api/research/v1/observations/read": observation,
  };
  const client = new ResearchRecordClient(async (path, options) => {
    assert.equal(options?.method, "POST");
    const reply = replies[String(path)] as { reference: unknown };
    assert.deepEqual(JSON.parse(String(options?.body)), reply.reference);
    return json(reply);
  });
  assert.deepEqual(await client.material(material.reference, signal()), material);
  assert.deepEqual(await client.experiment(experiment.reference, signal()), experiment);
  assert.deepEqual(await client.observation(observation.reference, signal()), observation);
  const changed = structuredClone(observation); changed.reference.revision++;
  await assert.rejects(new ResearchRecordClient(async () => json(changed)).observation(observation.reference, signal()), failure("invalid_response"));
});

test("correction views pin the successor and retain before/after without changing campaign history", async () => {
  const observation = decodeProvenance("observation_correction", examples["observation-correction-view"]);
  const material = decodeProvenance("material_correction", examples["material-state-correction-view"]);
  const client = new ResearchRecordClient(async path => json(String(path).includes("observation") ? observation : material));
  assert.deepEqual(await client.observationCorrection(observation.after.reference, signal()), observation);
  assert.deepEqual(await client.materialCorrection(material.after.reference, signal()), material);
  const changed = structuredClone(observation); changed.before.reference.revision++;
  await assert.rejects(new ResearchRecordClient(async () => json(changed)).observationCorrection(observation.after.reference, signal()), failure("invalid_response"));
  await assert.rejects(client.materialCorrection(material.before.reference, signal()), failure("invalid_response"));
});

test("interpretation pending, exact completion and substituted digest remain distinct", async () => {
  const status = decodeProvenance("interpretation", examples["interpretation-status"]);
  assert.equal(status.outcome.status, "interpreted");
  if (status.outcome.status !== "interpreted") throw new Error("fixture must be complete");
  const reference = status.outcome.projection.reference;
  assert.deepEqual(await new ResearchRecordClient(async () => json(status)).interpretation(reference, signal()), status);
  const pending = { ...status, outcome: { status: "pending" } };
  await assert.rejects(new ResearchRecordClient(async () => json(pending)).interpretation(reference, signal()), failure("unavailable"));
  await assert.rejects(new ResearchRecordClient(async () => json(status)).interpretation({ ...reference, sha256: "0".repeat(64) }, signal()), failure("invalid_response"));
  await assert.rejects(new ResearchRecordClient(async () => json({ ...status, actor_id: "different" })).interpretation(reference, signal()), failure("invalid_response"));
});
