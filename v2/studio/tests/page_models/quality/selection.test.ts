import { test } from "node:test";
import assert from "node:assert/strict";
import fixture from "../../fixtures/scientific/feedback-browser.json" with { type: "json" };
import { WorkspaceFeedbackSelection } from "../../../src/page_models/session/feedback_selection.js";

const pins = { ...fixture.pins, corrections: null, publication: null, proposal: null };
const scope = pins.question.scope;
const search = (value: unknown) => new URLSearchParams({ feedback: JSON.stringify(value) }).toString();
test("launcher feedback pins are explicit, immutable and scoped by the session", () => {
  const selected = new WorkspaceFeedbackSelection(search(pins), scope);
  assert.equal(selected.phase, "ready"); assert.deepEqual(selected.pins, pins);
  assert.equal(Object.isFrozen(selected.pins!.question), true);
  assert.equal(new WorkspaceFeedbackSelection("", scope).phase, "missing");
});
test("foreign, ambiguous, oversized and malformed links grant no feedback selection", () => {
  const variants = [search(pins) + "&" + search(pins), "feedback=%7B", "x".repeat(8193),
    search({ ...pins, extra: true }), search({ ...pins, question: { ...pins.question, scope: { ...scope, project_id: "foreign" } } })];
  for (const value of variants) {
    const selected = new WorkspaceFeedbackSelection(value, scope);
    assert.equal(selected.phase, "invalid"); assert.equal(selected.pins, null);
  }
  assert.equal(new WorkspaceFeedbackSelection(search(pins), { ...scope, tenant_id: "foreign" }).phase, "invalid");
});
