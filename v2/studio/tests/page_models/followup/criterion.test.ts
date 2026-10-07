import { test } from "node:test";
import assert from "node:assert/strict";
import { CriterionModel } from "../../../src/page_models/followup/criterion.js";
import type { CriterionRecords } from "../../../src/transport/followup/criterion.js";
import { draft } from "../../fixtures/followup.js";
test("disposed criterion read cannot restore protected content", async () => {
  let reject!: (error: Error) => void;
  const model = new CriterionModel({ load: () => new Promise<CriterionRecords>((_, failure) => { reject = failure; }) });
  const pending = model.select(draft().unresolved[0]!.criterion); model.dispose(); reject(Error("late")); await pending;
  assert.equal(model.snapshot.phase, "idle"); assert.equal(model.snapshot.records, null);
});
