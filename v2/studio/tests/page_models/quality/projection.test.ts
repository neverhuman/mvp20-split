import { test } from "node:test";
import assert from "node:assert/strict";
import fixture from "../../fixtures/scientific/feedback.json" with { type: "json" };
import { decodeFeedback } from "../../../src/contracts/scientific/feedback.js";
import { decodeProvenance } from "../../../src/contracts/scientific/provenance.js";
import { FeedbackContext } from "../../../src/page_models/feedback/context.js";
import type { FeedbackPins } from "../../../src/page_models/feedback/context.js";
import { FeedbackLineage } from "../../../src/page_models/feedback/lineage.js";
import type { FeedbackRecords } from "../../../src/page_models/feedback/lineage.js";
import { FeedbackModel } from "../../../src/page_models/feedback/model.js";
import type { FeedbackSources } from "../../../src/page_models/feedback/model.js";
import { QualityProjection } from "../../../src/page_models/quality/projection.js";
import { QualityAttachment } from "../../../src/page_models/quality/attachment.js";
import { QualityModel } from "../../../src/page_models/quality/model.js";
import { QualityFocus } from "../../../src/page_models/quality/focus.js";
import { ScientificReadFailure } from "../../../src/transport/scientific/failure.js";
import { artifact, evidenceDetail, values } from "../../fixtures/evidence.js";
import { snapshot, deferred } from "../../fixtures/observations.js";

function setup() {
  const records: FeedbackRecords = { question: decodeProvenance("question", structuredClone(fixture.question)),
    need: decodeProvenance("need", structuredClone(fixture.need)),
    assessment: decodeFeedback("assessment", structuredClone(fixture.assessment)),
    publication: null, proposal: null, change: null, corrections: null };
  const pins: FeedbackPins = { question: records.question.reference, need: records.need.reference,
    assessment: records.assessment!.request, publication: null, proposal: null, corrections: null };
  const sources: FeedbackSources = { research: { question: async () => records.question, need: async () => records.need },
    feedback: { assessment: async () => records.assessment!, publication: async () => { throw new Error("unexpected"); },
      proposal: async () => { throw new Error("unexpected"); }, change: async () => { throw new Error("unexpected"); },
      correction: async () => { throw new Error("unexpected"); } } };
  return { records, pins, sources, lineage: () => new FeedbackLineage(new FeedbackContext(pins), records) };
}

test("focus export keeps exact pins, qualitative intent and every unresolved point", () => {
  const f = setup();
  f.records.question.criteria.push({ criterion_id: "second", description: "Unassessed second criterion" });
  f.records.need.criterion_ids.push("second");
  const projection = new QualityProjection(f.lineage()), key = projection.points[0]!.key;
  const draft = new QualityFocus().set(projection, key, "Resolve disagreement", "Learn which evidence applies");
  const document = draft.document(projection);
  assert.equal(document.selected.length, 1); assert.equal(document.unresolved.length, 2);
  assert.equal(document.authority, "unsubmitted_human_draft");
  assert.equal(document.expected_information_gain.numerical_estimate, null);
  assert.deepEqual(document.assessment, f.records.assessment!.request);
  assert.equal(document.execution, null); assert.equal(Object.isFrozen(document.selected[0]!.point), true);
  assert.equal(draft.set(projection, key, "Updated", "Another question").items.length, 1);
  assert.equal(draft.remove(key).items.length, 0); assert.equal(draft.items.length, 1);
  for (const text of ["", "   ", "x".repeat(2049)]) assert.throws(() => draft.set(projection, key, text, "Learn"));
  assert.throws(() => draft.set(projection, "foreign", "Improve", "Learn"));
  assert.throws(() => new QualityFocus([...draft.items, ...draft.items]));
  assert.throws(() => new QualityFocus(Array.from({ length: 33 }, () => draft.items[0]!)));
  f.records.assessment = null; f.pins.assessment = null;
  assert.equal(draft.retain(new QualityProjection(f.lineage())).items.length, 0);
});

test("focus survives same-context refresh but clears on denial, rebind, hide and disposal", async () => {
  const f = setup(), feedback = new FeedbackModel(f.sources), model = new QualityModel(feedback);
  assert.throws(() => model.exportFocus());
  feedback.bind(f.pins); await feedback.refresh();
  const key = model.snapshot.projection!.points[0]!.key;
  model.focusPoint(key, "Improve", "Learn"); model.filter("supported");
  assert.equal(model.snapshot.focus.items.length, 1);
  await feedback.refresh(); assert.equal(model.snapshot.focus.items.length, 1);
  assert.equal(model.exportFocus().selected.length, 1);
  model.unfocus(key); assert.equal(model.snapshot.focus.items.length, 0);
  model.focusPoint(key, "Improve", "Learn"); feedback.visibility(false);
  assert.equal(model.snapshot.focus.items.length, 0); assert.throws(() => model.exportFocus());
  feedback.visibility(true); await feedback.refresh(); assert.equal(model.snapshot.focus.items.length, 0);
  model.focusPoint(key, "Improve", "Learn"); feedback.bind(f.pins); await feedback.refresh();
  assert.equal(model.snapshot.focus.items.length, 0);
  model.focusPoint(key, "Improve", "Learn");
  f.sources.feedback.assessment = async () => { throw new ScientificReadFailure("denied"); };
  await feedback.refresh(); assert.equal(model.snapshot.focus.items.length, 0);
  model.dispose(); model.focusPoint(key, "Improve", "Learn"); model.unfocus(key);
  assert.throws(() => model.exportFocus()); feedback.dispose();
});

test("gap presentation preserves reasons and never manufactures accuracy or demonstrated error", () => {
  for (const [reason, category] of [["missing_answer", "unknown"], ["answer_unknown", "unknown"],
    ["evidence_conflict", "contradictory"], ["answer_contradicted", "contradictory"],
    ["evidence_contradicted", "contradictory"], ["no_matching_evidence", "insufficient"]] as const) {
    const f = setup(); assert.equal(f.records.assessment!.outcome.status, "assessed");
    if (f.records.assessment!.outcome.status !== "assessed") throw new Error("fixture");
    f.records.assessment!.outcome.assessment.needs[0]!.gap!.reason = reason;
    const view = new QualityProjection(f.lineage()), point = view.points[0]!;
    assert.equal(point.category, category); assert.equal(point.reason, reason);
    assert.deepEqual(point.need, f.records.need.reference);
    assert.equal(view.calibratedAccuracy, null); assert.equal(view.demonstratedError, null);
    assert.equal(view.scientificEstablishment, false); assert.equal(view.futureCampaignsOnly, true);
    assert.equal(Object.isFrozen(point.supporting), true);
  }
});

test("pending and failed assessments are records, not scientific errors or network failures", () => {
  for (const kind of ["unselected", "pending", "failed"] as const) {
    const f = setup();
    if (kind === "unselected") { f.records.assessment = null; f.pins.assessment = null; }
    else f.records.assessment!.outcome = kind === "pending" ? { status: kind } : { status: kind, code: "peer_unavailable" };
    const view = new QualityProjection(f.lineage());
    assert.equal(view.points[0]!.category, "unassessed");
    assert.equal(view.points[0]!.reason, "assessment_" + kind);
    assert.equal(view.attachment, null);
  }
});

test("bounded pages preserve multiple weak points and expose omitted owner decisions", () => {
  const f = setup();
  f.records.question.criteria = Array.from({ length: 25 }, (_, i) => ({ criterion_id: i ? "c" + i : "c", description: "Criterion " + i }));
  f.records.need.criterion_ids = f.records.question.criteria.map(c => c.criterion_id);
  const view = new QualityProjection(f.lineage());
  assert.equal(view.missingDecisions, 24);
  assert.equal(view.page().items.length, 20); assert.equal(view.page().nextOffset, 20);
  assert.equal(view.page("all", 20).items.length, 5); assert.equal(view.page("all", 20).nextOffset, null);
  assert.equal(view.page("unassessed").selectedTotal, 24);
  assert.equal(view.page("supported").total, 25); assert.equal(view.page("supported").items.length, 0);
  for (const offset of [-1, 1.5, 26, NaN]) assert.throws(() => view.page("all", offset));
});

test("duplicate owner decisions cannot create competing verdicts for the same point", () => {
  const f = setup(); if (f.records.assessment!.outcome.status !== "assessed") throw new Error("fixture");
  f.records.assessment!.outcome.assessment.needs.push(structuredClone(f.records.assessment!.outcome.assessment.needs[0]!));
  assert.throws(() => new QualityProjection(f.lineage()));
});

test("exact output identity proves a pinned attachment; changed metadata or revision does not", () => {
  const detail = evidenceDetail(); detail.node.status = "succeeded";
  const attachment = new QualityAttachment(snapshot().snapshot, detail, "result", [values()]);
  assert.equal(attachment.contains(artifact()), true); assert.equal(attachment.complete, true);
  assert.equal(attachment.operationalState, "succeeded");
  assert.equal(attachment.contains({ ...artifact(), size_bytes: 18 }), false);
  assert.equal(attachment.contains({ ...artifact(), artifact_id: "different-same-bytes" }), false);
  assert.throws(() => new QualityAttachment(snapshot({ revision: 2 }).snapshot, detail, "result", [values()]));
  assert.throws(() => new QualityAttachment(snapshot().snapshot, detail, "result", []));
  assert.throws(() => new QualityAttachment(snapshot().snapshot, detail, "result", [values(), values()]));
  const f = setup(); assert.equal(new QualityProjection(f.lineage(), attachment).attachment, null);
});

test("quality region shares reads, filters locally and clears denied/hidden state", async () => {
  const f = setup(), feedback = new FeedbackModel(f.sources), model = new QualityModel(feedback);
  feedback.bind(f.pins); await feedback.refresh();
  assert.equal(model.snapshot.phase, "ready"); assert.equal(model.snapshot.page!.items.length, 1);
  model.select(model.snapshot.page!.items[0]!.key); assert.notEqual(model.snapshot.selected, null);
  assert.throws(() => model.select("not-a-point"));
  model.filter("supported"); assert.equal(model.snapshot.page!.items.length, 0); assert.equal(model.snapshot.selected, null);
  model.filter("unknown"); model.page(0); assert.equal(model.snapshot.page!.selectedTotal, 1);
  feedback.visibility(false); assert.equal(model.snapshot.projection, null);
  feedback.visibility(true); await feedback.refresh(); assert.notEqual(model.snapshot.projection, null);
  f.sources.feedback.assessment = async () => { throw new ScientificReadFailure("denied"); };
  await feedback.refresh(); assert.equal(model.snapshot.phase, "denied"); assert.equal(model.snapshot.page, null);
  model.dispose(); assert.equal(model.snapshot.projection, null); feedback.dispose();
});

test("late responses and reentrant rebinding cannot publish an earlier quality context", async () => {
  const f = setup(), pending = deferred<FeedbackRecords["question"]>();
  f.sources.research.question = async () => pending.promise;
  const feedback = new FeedbackModel(f.sources), model = new QualityModel(feedback);
  feedback.bind(f.pins); const first = feedback.refresh(); feedback.bind(null);
  pending.resolve(f.records.question); await first;
  assert.equal(model.snapshot.projection, null);
  model.subscribe(() => { if (model.snapshot.phase === "loading") feedback.bind(null); });
  feedback.bind(f.pins); await feedback.refresh(); assert.equal(model.snapshot.projection, null);
  model.dispose(); feedback.dispose();
});

test("several simultaneous owner verdicts coexist beside successful operational output", () => {
  const f = setup(); if (f.records.assessment!.outcome.status !== "assessed") throw new Error("fixture");
  const result = f.records.assessment!.outcome.assessment;
  const base = structuredClone(result.needs[0]!);
  const reasons = ["answer_unknown", "evidence_conflict", "no_matching_evidence", null] as const;
  f.records.question.criteria = reasons.map((_, i) => ({ criterion_id: "c" + i, description: "Criterion " + i }));
  f.records.need.criterion_ids = f.records.question.criteria.map(c => c.criterion_id);
  result.needs = reasons.map((reason, i) => ({ ...structuredClone(base), criterion_id: "c" + i,
    gap: reason ? { criterion_id: "c" + i, need: base.need, reason } : null }));
  const selected = result.subject, anchor = snapshot().snapshot, detail = evidenceDetail(), page = values();
  anchor.cut.scope = selected.scope; detail.cut = structuredClone(anchor.cut); page.cut = structuredClone(anchor.cut);
  detail.node.status = "succeeded";
  page.items[0]!.value = { kind: "artifact", artifact: selected, representation: "fixture", unit: "1" };
  const attachment = new QualityAttachment(anchor, detail, "result", [page]);
  const view = new QualityProjection(f.lineage(), attachment);
  assert.deepEqual(view.points.map(p => p.category), ["unknown", "contradictory", "insufficient", "supported"]);
  assert.equal(view.attachment!.operationalState, "succeeded");
  assert.equal(view.attachment!.cut.revision, anchor.cut.revision);
  assert.equal(view.scientificEstablishment, false);
  const focused = new QualityFocus().set(view, view.points[1]!.key, "Reconcile conflicting evidence", "Test applicability").document(view);
  assert.deepEqual(focused.execution, { cut: anchor.cut, activation_id: detail.node.activation_id, port: "result" });
  assert.equal(focused.unresolved.length, 3);
  page.items.length = 0; assert.equal(attachment.contains(selected), true);
});

test("selection survives same-context refresh but not a rebound context or denial", async () => {
  const f = setup(), feedback = new FeedbackModel(f.sources), model = new QualityModel(feedback);
  feedback.bind(f.pins); await feedback.refresh();
  const key = model.snapshot.projection!.points[0]!.key; model.select(key);
  await feedback.refresh(); assert.equal(model.snapshot.selected, key);
  model.attach(null); assert.equal(model.snapshot.selected, key);
  feedback.bind(f.pins); await feedback.refresh(); assert.equal(model.snapshot.selected, null);
  model.select(key); f.sources.feedback.assessment = async () => { throw new ScientificReadFailure("denied"); };
  await feedback.refresh(); assert.equal(model.snapshot.selected, null);
  model.dispose(); model.attach(null); model.select(key); model.page(0); model.filter("all");
  assert.equal(model.snapshot.projection, null); feedback.dispose();
});

test("invalid owner projection clears the entire quality region", async () => {
  const f = setup(), feedback = new FeedbackModel(f.sources), model = new QualityModel(feedback);
  feedback.bind(f.pins); await feedback.refresh();
  if (f.records.assessment!.outcome.status !== "assessed") throw new Error("fixture");
  f.records.assessment!.outcome.assessment.needs.push(structuredClone(f.records.assessment!.outcome.assessment.needs[0]!));
  await feedback.refresh(); assert.equal(model.snapshot.phase, "failed"); assert.equal(model.snapshot.projection, null);
  assert.equal(model.snapshot.error!.kind, "invalid_response"); model.dispose(); feedback.dispose();
});
