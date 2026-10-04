import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import fixture from "../fixtures/scientific/feedback.json" with { type: "json" };
import { FeedbackClient } from "../../src/transport/feedback/client.js";
import { decodeFeedback } from "../../src/contracts/scientific/feedback.js";
import { ScientificReadFailure } from "../../src/transport/scientific/failure.js";
import { canonical } from "../../src/transport/scientific/identity.js";
import { allowedRoute } from "../../src/transport/scientific/routes.js";

const signal = () => new AbortController().signal;
const json = (v: unknown) => new Response(JSON.stringify(v), { headers: { "content-type": "application/json" } });
const failure = (kind: string) => (e: unknown) => e instanceof ScientificReadFailure && e.kind === kind;
const assessment = () => decodeFeedback("assessment", structuredClone(fixture.assessment));
const root = () => decodeFeedback("correction", structuredClone(fixture.root));
function signed(record: unknown) {
  const r = record as typeof fixture.successor;
  const ascii = canonical(record).replace(/[\u007f-\uffff]/g, c => "\\u" + c.charCodeAt(0).toString(16).padStart(4, "0"));
  return decodeFeedback("correction", { schema_version: "1", reference: { schema_version: "1", chain: r.chain, ordinal: r.ordinal, record_sha256: createHash("sha256").update(ascii).digest("hex") }, record });
}
function selection(view = root()) { return { wire_version: "1" as const, chain: view.reference.chain, revision: view.reference }; }

test("assessment reads retain weak outcomes, exact request and synthetic authority", async () => {
  const reply = assessment();
  let count = 0;
  const client = new FeedbackClient(async (path, options) => {
    count++; assert.equal(path, "/api/research/v1/assessments/read");
    assert.equal(options?.credentials, "same-origin"); assert.equal(options?.method, "POST");
    assert.deepEqual(JSON.parse(String(options?.body)), reply.request);
    return json(reply);
  });
  assert.deepEqual(await client.assessment(reply.request, signal()), reply);
  assert.equal(count, 1);
  if (reply.outcome.status !== "assessed") throw new Error("fixture");
  assert.equal(reply.outcome.assessment.sufficient, false);
  assert.equal(reply.outcome.assessment.scientifically_established, false);
  reply.outcome.assessment.request.assessment_id = "wrong";
  await assert.rejects(client.assessment(assessment().request, signal()), failure("invalid_response"));
});

test("assessment pending and failed remain records, never invented completed answers", async () => {
  for (const outcome of [{ status: "pending" }, { status: "failed", code: "peer_missing" }]) {
    const reply = { ...assessment(), outcome };
    const client = new FeedbackClient(async () => json(reply));
    assert.deepEqual((await client.assessment(reply.request, signal())).outcome, outcome);
  }
});

test("assessment request/reply scope, actor and strict false are checked", async () => {
  for (const mutate of [
    (r: ReturnType<typeof assessment>) => { r.request.profile.scope.project_id = "foreign"; },
    (r: ReturnType<typeof assessment>) => { r.actor_id = "another"; },
    (r: ReturnType<typeof assessment>) => { if (r.outcome.status === "assessed") Object.assign(r.outcome.assessment, { scientifically_established: true }); },
  ]) {
    const reply = assessment(); mutate(reply);
    await assert.rejects(new FeedbackClient(async () => json(reply)).assessment(assessment().request, signal()), failure("invalid_response"));
  }
});

test("publication checks exact selection and scoped synthetic purpose", async () => {
  const receipt = root().record.source_receipt;
  const raw = receipt.subject;
  const reply = decodeFeedback("publication", { ...structuredClone(fixture.publication), request: { ...fixture.publication.request, scope: receipt.scope },
    outcome: { status: "published", receipt, derivation: { artifact: raw, schema_version: "1", upload_id: "upload", request_sha256: "c".repeat(64),
      origin: { schema_version: "1", scope: raw.scope, actor_id: "fixture", command_family: "derive", command_id: "command" },
      declaration: { schema_version: "1", transformation: { transformation_id: "copy", version: "1", sha256: "b".repeat(64) }, inputs: [raw] } } } });
  const client = new FeedbackClient(async () => json(reply));
  assert.deepEqual(await client.publication(reply.request, signal()), reply);
  if (reply.outcome.status !== "published") throw new Error("fixture");
  reply.outcome.receipt.purpose = "scientific_truth";
  await assert.rejects(client.publication(reply.request, signal()), failure("invalid_response"));
});

test("historical correction uses pinned revision and validates published golden hash", async () => {
  const reply = root();
  let calls = 0;
  const client = new FeedbackClient(async (path, options) => {
    calls++; assert.equal(path, "/api/research/v1/assessment-receipts/select");
    assert.deepEqual(JSON.parse(String(options?.body)), selection(reply)); return json(reply);
  });
  assert.deepEqual(await client.correction("research", selection(reply), signal()), reply);
  await assert.rejects(client.correction("research", { ...selection(reply), revision: null }, signal()), failure("invalid_request"));
  const foreign = selection(); foreign.chain = { ...foreign.chain, chain_id: "foreign" };
  await assert.rejects(client.correction("research", foreign, signal()), failure("invalid_request"));
  assert.equal(calls, 1);
});

test("successor preserves supersession context and supports qualified abstention", async () => {
  const reply = signed(structuredClone(fixture.successor));
  const client = new FeedbackClient(async () => json(reply));
  assert.deepEqual(await client.correction("research", selection(reply), signal()), reply);
  assert.equal(reply.record.notice?.outcome.status, "superseded");
  const record = structuredClone(fixture.successor);
  record.source_receipt.purpose = record.receipt.purpose = "knowledge.synthetic_entailment";
  if (record.notice) record.notice.purpose = "knowledge.synthetic_entailment";
  const knowledge = signed(record);
  assert.deepEqual(await new FeedbackClient(async () => json(knowledge)).correction("knowledge", selection(knowledge), signal()), knowledge);
});

test("correctly hashed records still cannot forge chain, authority or predecessor semantics", async () => {
  for (const mutate of [
    (r: typeof fixture.successor) => { r.receipt.purpose = "wrong"; },
    (r: typeof fixture.successor) => { r.receipt.scope.project_id = "foreign"; },
    (r: typeof fixture.successor) => { if (r.predecessor) r.predecessor.ordinal = r.ordinal; },
    (r: typeof fixture.successor) => { if (r.notice?.outcome.status === "superseded") r.notice.outcome.replacement_revision = "wrong"; },
  ]) {
    const record = structuredClone(fixture.successor); mutate(record);
    const reply = signed(record);
    await assert.rejects(new FeedbackClient(async () => json(reply)).correction("research", selection(reply), signal()), failure("invalid_response"));
  }
  const reply = root(); reply.record.reason_code = "altered";
  await assert.rejects(new FeedbackClient(async () => json(reply)).correction("research", selection(reply), signal()), failure("invalid_response"));
});

test("feedback route surface contains reads and excludes correction/publication mutations", () => {
  assert.equal(allowedRoute("GET", "/api/knowledge/v1/graphs/domain%3A1/proposals/feedback%3A1"), true);
  for (const path of ["/api/research/v1/assessments", "/api/research/v1/assessment-publications", "/api/research/v1/assessment-receipts/correct", "/api/knowledge/v1/graph-proposals"]) assert.equal(allowedRoute("POST", path), false);
  for (const path of ["/api/knowledge/v1/graphs/../proposals/x", "/api/knowledge/v1/graphs/g/proposals/a%2Fb", "https://example.test/api/knowledge/v1/graphs/g/proposals/x"]) assert.equal(allowedRoute("GET", path), false);
});

test("denial and malformed feedback are explicit failures without retrying writes", async () => {
  for (const [response, kind] of [[new Response("", { status: 403 }), "denied"], [json({}), "invalid_response"]] as const) {
    let calls = 0;
    await assert.rejects(new FeedbackClient(async () => { calls++; return response; }).assessment(assessment().request, signal()), failure(kind));
    assert.equal(calls, 1);
  }
});

test("proposal and accepted change read exact committed records with Python golden fingerprints", async () => {
  const proposal = decodeFeedback("proposal", structuredClone(fixture.proposal));
  const change = decodeFeedback("change", structuredClone(fixture.change));
  const client = new FeedbackClient(async (path, options) => {
    if (String(path).endsWith("/graph-changes/read")) {
      assert.deepEqual(JSON.parse(String(options?.body)), change.reference); return json(change);
    }
    assert.equal(options?.method, "GET"); return json(proposal);
  });
  assert.deepEqual(await client.proposal(proposal.proposal.graph, proposal.proposal.change_id, signal()), proposal);
  assert.deepEqual(await client.change(change.reference, signal()), change);
  change.content.proposal.rationale = "tampered";
  await assert.rejects(client.change(change.reference, signal()), failure("invalid_response"));
  proposal.proposal.description = "tampered";
  await assert.rejects(client.proposal(proposal.proposal.graph, proposal.proposal.change_id, signal()), failure("invalid_response"));
});

test("proposal pending/rejected states are preserved; invalid identifiers never fetch", async () => {
  const proposal = decodeFeedback("proposal", structuredClone(fixture.proposal));
  proposal.decision = null;
  let calls = 0;
  const client = new FeedbackClient(async () => { calls++; return json(proposal); });
  assert.equal((await client.proposal(proposal.proposal.graph, proposal.proposal.change_id, signal())).decision, null);
  await assert.rejects(client.proposal(proposal.proposal.graph, "../bad", signal()), failure("invalid_request"));
  assert.equal(calls, 1);
  const original = decodeFeedback("proposal", structuredClone(fixture.proposal));
  assert.ok(original.decision);
  proposal.decision = { ...original.decision, decision: { outcome: "rejected", findings: [{ code: "unresolved", location: "proposal", message: "Unresolved evidence" }] } };
  assert.equal((await client.proposal(proposal.proposal.graph, proposal.proposal.change_id, signal())).decision?.decision.outcome, "rejected");
});
