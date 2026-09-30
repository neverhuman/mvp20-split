import { test } from "node:test";
import assert from "node:assert/strict";
import { NamedViewsModel } from "../../src/page_models/named_views.js";
import { catalog, lineage } from "../fixtures/navigation.js";
import { snapshot } from "../fixtures/observations.js";

for (const region of ["catalog", "lineage"] as const) test(`subscriber rebinding during ${region} loading cannot restore the old context`, async () => {
  const model = new NamedViewsModel({ catalog: async () => catalog(), lineage: async () => lineage() });
  if (region === "lineage") await model.load(snapshot().snapshot);
  let rebound = false;
  model.subscribe(() => {
    if (!rebound && (region === "catalog" ? model.snapshot.phase : model.snapshot.lineagePhase) === "loading") {
      rebound = true; void model.load(null);
    }
  });
  if (region === "catalog") await model.load(snapshot().snapshot); else await model.lineage();
  assert.equal(rebound, true);
  assert.equal(model.snapshot.phase, "idle");
  assert.equal(model.snapshot.catalog, null); assert.equal(model.snapshot.lineage, null);
});
