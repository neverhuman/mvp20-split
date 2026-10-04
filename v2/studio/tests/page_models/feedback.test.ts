import { test } from "node:test";
import assert from "node:assert/strict";
import fixture from "../fixtures/scientific/feedback.json" with { type: "json" };
import { decodeFeedback } from "../../src/contracts/scientific/feedback.js";
import { decodeProvenance } from "../../src/contracts/scientific/provenance.js";
import { FeedbackContext } from "../../src/page_models/feedback/context.js";
import type { FeedbackPins } from "../../src/page_models/feedback/context.js";
import { FeedbackLineage } from "../../src/page_models/feedback/lineage.js";
import type { FeedbackRecords } from "../../src/page_models/feedback/lineage.js";
import { FeedbackModel } from "../../src/page_models/feedback/model.js";
import type { FeedbackSources } from "../../src/page_models/feedback/model.js";
import { ScientificReadFailure } from "../../src/transport/scientific/failure.js";

function setup() {
  const records: FeedbackRecords = {
    question: decodeProvenance("question", structuredClone(fixture.question)),
    need: decodeProvenance("need", structuredClone(fixture.need)),
    assessment: decodeFeedback("assessment", structuredClone(fixture.assessment)),
    publication: null, proposal: null, change: null, corrections: null,
  };
  const pins: FeedbackPins = { question: records.question.reference, need: records.need.reference, assessment: records.assessment!.request, publication: null, proposal: null, corrections: null };
  const sources: FeedbackSources = { research: { question: async () => records.question, need: async () => records.need },
    feedback: { assessment: async () => records.assessment!, publication: async () => { throw new Error("unrequested publication"); }, proposal: async () => records.proposal!, change: async () => records.change!, correction: async () => { throw new Error("unrequested correction"); } } };
  return { records, pins, sources };
}
const invalid = (kind: string) => (e: unknown) => e instanceof ScientificReadFailure && e.kind === kind;
function deferred<T>() { let resolve!: (v: T) => void; const promise = new Promise<T>(yes => { resolve = yes; }); return { promise, resolve }; }

test("feedback context freezes exact pins and rejects cross-project or head-based correction requests", () => {
  const { pins } = setup();
  const context = new FeedbackContext(pins);
  pins.question.question_id = "mutated";
  assert.equal(context.pins.question.question_id, "q");
  assert.equal(Object.isFrozen(context.pins.question.scope), true);
  const wrong = setup().pins; wrong.need = { ...wrong.need, scope: { ...wrong.need.scope, project_id: "foreign" } };
  assert.throws(() => new FeedbackContext(wrong), invalid("invalid_request"));
  const head = setup().pins;
  head.corrections = { owner: "research", previous: { wire_version: "1", chain: decodeFeedback("correction", fixture.root).reference.chain, revision: null }, next: { wire_version: "1", chain: decodeFeedback("correction", fixture.root).reference.chain, revision: null } };
  assert.throws(() => new FeedbackContext(head), invalid("invalid_request"));
});

test("unmet evidence remains useful readable lineage without a publication", async () => {
  const f = setup(), model = new FeedbackModel(f.sources); model.bind(f.pins); await model.refresh();
  assert.equal(model.snapshot.phase, "ready");
  assert.equal(model.snapshot.lineage?.evidenceState, "gap");
  assert.equal(model.snapshot.lineage?.futureOnly, true);
  assert.deepEqual(model.snapshot.lineage?.records.need.method, f.records.need.method);
  assert.equal(model.snapshot.lineage?.records.publication, null);
  f.records.need.criterion_ids.length = 0;
  assert.equal(model.snapshot.lineage?.records.need.criterion_ids.length, 1);
});

test("unassessed, pending and failed owners are not rendered as scientific answers", () => {
  for (const status of ["unassessed", "pending", "failed"] as const) {
    const f = setup();
    if (status === "unassessed") { f.records.assessment = null; f.pins.assessment = null; }
    else f.records.assessment!.outcome = status === "pending" ? { status } : { status, code: "peer_unavailable" };
    const lineage = new FeedbackLineage(new FeedbackContext(f.pins), f.records);
    assert.equal(lineage.evidenceState, status); assert.equal(lineage.proposalState, "unselected");
  }
});

test("matching text and shared scope cannot substitute for exact need/question identity", () => {
  for (const mutate of [
    (r: FeedbackRecords) => { r.need.question = { ...r.need.question, revision: 2 }; },
    (r: FeedbackRecords) => { r.need.criterion_ids = ["unknown"]; },
    (r: FeedbackRecords) => { if (r.assessment?.outcome.status === "assessed") r.assessment.outcome.assessment.needs[0]!.need.revision = 2; },
  ]) {
    const f = setup(), context = new FeedbackContext(f.pins); mutate(f.records);
    assert.throws(() => new FeedbackLineage(context, f.records), invalid("invalid_response"));
  }
});

test("a proposed graph edit must explicitly reference the chosen question and need", () => {
  const f = setup();
  const proposal = decodeFeedback("proposal", structuredClone(fixture.proposal));
  proposal.proposal.graph.scope = f.pins.question.scope;
  proposal.decision = null;
  f.pins.proposal = { graph: proposal.proposal.graph, change_id: proposal.proposal.change_id };
  f.records.proposal = proposal;
  const context = new FeedbackContext(f.pins);
  assert.throws(() => new FeedbackLineage(context, f.records), invalid("invalid_response"));
  const operation = proposal.proposal.operations.find(op => op.operation === "add_assertion");
  assert.ok(operation?.operation === "add_assertion");
  operation.assertion.research_links = [{ question: f.pins.question, need: f.pins.need, role: "proposed_answer", answer_proposal: null, validation_method: null }];
  assert.equal(new FeedbackLineage(context, f.records).proposalState, "pending");
  proposal.proposal.operations = [{ operation: "correct_assertion", prior: operation.assertion.reference, replacement: operation.assertion }];
  assert.equal(new FeedbackLineage(context, f.records).proposalState, "pending");
});

test("newer selection wins when older peer ignores cancellation", async () => {
  const f = setup(), held = deferred<typeof f.records.question>(); let calls = 0;
  f.sources.research.question = async () => ++calls === 1 ? held.promise : { ...f.records.question, objective: "new context" };
  const model = new FeedbackModel(f.sources); model.bind(f.pins);
  const first = model.refresh(); model.bind(f.pins); await model.refresh();
  held.resolve({ ...f.records.question, objective: "stale context" }); await first;
  assert.equal(model.snapshot.lineage?.records.question.objective, "new context");
});

test("hiding clears protected lineage and stale replies cannot restore it", async () => {
  const f = setup(), held = deferred<typeof f.records.need>(); f.sources.research.need = () => held.promise;
  const model = new FeedbackModel(f.sources); model.bind(f.pins); const pending = model.refresh();
  model.visibility(false); held.resolve(f.records.need); await pending;
  assert.equal(model.snapshot.lineage, null); assert.equal(model.snapshot.phase, "stale");
  model.visibility(true); assert.equal(model.snapshot.lineage, null);
  await model.refresh(); assert.equal(model.snapshot.phase, "ready");
});

test("denial clears the complete lineage and cancels sibling reads", async () => {
  const f = setup(), model = new FeedbackModel(f.sources); model.bind(f.pins); await model.refresh();
  let sibling: AbortSignal | undefined;
  f.sources.research.question = async (_q, signal) => { sibling = signal; return f.records.question; };
  f.sources.research.need = async () => { throw new ScientificReadFailure("denied"); };
  await model.refresh();
  assert.equal(model.snapshot.phase, "denied"); assert.equal(model.snapshot.lineage, null); assert.equal(sibling?.aborted, true);
});

test("reentrant context removal prevents any peer request", async () => {
  const f = setup(); let calls = 0; f.sources.research.question = async () => { calls++; return f.records.question; };
  const model = new FeedbackModel(f.sources); model.bind(f.pins);
  model.subscribe(() => { if (model.snapshot.phase === "loading") model.bind(null); });
  await model.refresh(); assert.equal(calls, 0); assert.equal(model.snapshot.context, null);
});

test("disposed feedback model has no retained lineage, subscriptions or late changes", async () => {
  const f = setup(), held = deferred<typeof f.records.question>(); f.sources.research.question = () => held.promise;
  const model = new FeedbackModel(f.sources); model.bind(f.pins); const work = model.refresh();
  let calls = 0; model.subscribe(() => { calls++; }); model.dispose(); held.resolve(f.records.question); await work;
  model.bind(f.pins); model.visibility(true); await model.refresh();
  assert.equal(calls, 0); assert.equal(model.snapshot.context, null); assert.equal(model.snapshot.lineage, null);
});

test("corrected rejected evidence remains visible with prior receipt and future-only context", async () => {
  const f = setup();
  assert.ok(f.records.assessment?.outcome.status === "assessed");
  const subject = f.records.assessment.outcome.assessment.subject;
  const remap = (raw: unknown) => JSON.parse(JSON.stringify(raw).replaceAll(JSON.stringify(fixture.root.reference.chain.scope), JSON.stringify(f.pins.question.scope)));
  const previous = decodeFeedback("correction", remap(fixture.root));
  const next = decodeFeedback("correction", { schema_version: "1", reference: { ...previous.reference, ordinal: 2, record_sha256: "d".repeat(64) }, record: remap(fixture.successor) });
  for (const item of [previous, next]) {
    item.record.source_receipt.subject = subject; item.record.receipt.subject = subject;
    if (item.record.notice) item.record.notice.subject = subject;
  }
  next.record.predecessor = previous.reference;
  assert.ok(next.record.notice); next.record.notice.revision = previous.record.receipt.revision;
  f.records.corrections = { previous, next };
  f.pins.publication = { wire_version: "1", scope: f.pins.question.scope, assessment_id: f.pins.assessment!.assessment_id };
  f.records.publication = decodeFeedback("publication", { wire_version: "1", request: f.pins.publication, actor_id: "fixture", outcome: { status: "published", receipt: next.record.source_receipt,
    derivation: { schema_version: "1", artifact: subject, upload_id: "upload", request_sha256: "a".repeat(64), origin: { schema_version: "1", scope: subject.scope, actor_id: "fixture", command_id: "publish", command_family: "derive" }, declaration: { schema_version: "1", transformation: { transformation_id: "fixture", version: "1", sha256: "a".repeat(64) }, inputs: [subject] } } } });
  f.pins.corrections = { owner: "research", previous: { wire_version: "1", chain: previous.reference.chain, revision: previous.reference }, next: { wire_version: "1", chain: next.reference.chain, revision: next.reference } };
  f.sources.feedback.publication = async () => f.records.publication!;
  f.sources.feedback.correction = async (_owner, selection) => selection.revision?.ordinal === 1 ? previous : next;
  const model = new FeedbackModel(f.sources); model.bind(f.pins); await model.refresh();
  assert.equal(model.snapshot.phase, "ready");
  assert.equal(model.snapshot.lineage?.records.corrections?.next.record.receipt.outcome.status, "rejected");
  assert.deepEqual(model.snapshot.lineage?.records.corrections?.previous, previous);
  const context = new FeedbackContext(f.pins);
  next.record.predecessor = null;
  assert.throws(() => new FeedbackLineage(context, f.records), invalid("invalid_response"));
  assert.equal(model.snapshot.lineage?.records.corrections?.next.record.predecessor?.ordinal, 1);
});

test("failure states clear prior records and do not collapse into evidence rejection", async () => {
  for (const [kind, phase] of [["query_conflict", "stale"], ["unavailable", "unavailable"], ["invalid_response", "failed"], ["aborted", "stale"]] as const) {
    const f = setup(), model = new FeedbackModel(f.sources); model.bind(f.pins); await model.refresh();
    f.sources.research.need = async () => { throw new ScientificReadFailure(kind); };
    await model.refresh(); assert.equal(model.snapshot.phase, phase); assert.equal(model.snapshot.lineage, null);
  }
});

test("structural acceptance loads its exact change without claiming scientific sufficiency", async () => {
  const f = setup();
  const proposal = decodeFeedback("proposal", structuredClone(fixture.proposal));
  proposal.proposal.graph.scope = f.pins.question.scope;
  const op = proposal.proposal.operations.find(op => op.operation === "add_assertion");
  assert.ok(op?.operation === "add_assertion");
  op.assertion.research_links = [{ question: f.pins.question, need: f.pins.need, role: "proposed_answer", answer_proposal: null, validation_method: null }];
  const change = decodeFeedback("change", structuredClone(fixture.change));
  change.content.proposal = proposal.proposal;
  assert.ok(proposal.decision?.decision.outcome === "accepted");
  change.reference = proposal.decision.decision.head.change;
  f.pins.proposal = { graph: proposal.proposal.graph, change_id: proposal.proposal.change_id };
  f.sources.feedback.proposal = async () => proposal;
  let selected: unknown;
  f.sources.feedback.change = async reference => { selected = reference; return change; };
  const model = new FeedbackModel(f.sources); model.bind(f.pins); await model.refresh();
  assert.equal(model.snapshot.phase, "ready"); assert.deepEqual(selected, change.reference);
  assert.equal(model.snapshot.lineage?.proposalState, "accepted"); assert.equal(model.snapshot.lineage?.evidenceState, "gap");
});
