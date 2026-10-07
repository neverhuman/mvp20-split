import { test } from "node:test";
import assert from "node:assert/strict";
import { ProposalProjection } from "../../../src/page_models/followup/projection.js";
import { draft, scope } from "../../fixtures/followup.js";
test("bounded immutable intent pages retain uncertainty without adoption claims", () => {
  const input = draft(41), projection = new ProposalProjection({ kind: "followup", draft: input }, scope);
  input.unresolved[0]!.description = "changed";
  assert.equal(projection.page().rows.length, 20); assert.equal(projection.page(20).rows.length, 20);
  assert.equal(projection.page(40).rows.length, 1); assert.equal(projection.page(40).hasNext, false);
  assert.equal(projection.adoption, "Not verified");
  const row = projection.page().rows[0]!; assert.equal(row.kind, "unresolved");
  assert.ok(Object.isFrozen(row)); assert.throws(() => projection.page(1)); assert.throws(() => projection.page(60));
  if (row.kind === "unresolved") assert.equal(row.description, "The available evidence is incomplete");
});
test("duplicate or foreign criterion pins fail closed", () => {
  const duplicate = draft(); duplicate.unresolved.push(structuredClone(duplicate.unresolved[0]!));
  assert.throws(() => new ProposalProjection({ kind: "followup", draft: duplicate }, scope));
  const foreign = structuredClone(draft()); foreign.unresolved[0]!.criterion.need.scope.project_id = "foreign";
  assert.throws(() => new ProposalProjection({ kind: "followup", draft: foreign }, scope));
});
