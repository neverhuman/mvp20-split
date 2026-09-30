import { test } from "node:test";
import assert from "node:assert/strict";
import { NamedViewsModel } from "../../src/page_models/named_views.js";
import type { NamedViewSource } from "../../src/transport/observations.js";
import { ReadFailure } from "../../src/transport/failure.js";
import { catalog, lineage } from "../fixtures/navigation.js";
import { snapshot, deferred } from "../fixtures/observations.js";

const source = (): NamedViewSource => ({ catalog: async () => catalog(), lineage: async () => lineage() });
test("named views load actual public lineage only under their accepted catalog cut", async () => {
  const model = new NamedViewsModel(source());
  await model.lineage(); assert.equal(model.snapshot.phase, "idle");
  await model.load(snapshot().snapshot); await model.lineage();
  assert.equal(model.snapshot.lineage?.predecessor.revision, 8);
  await model.load(null); assert.equal(model.snapshot.catalog, null); assert.equal(model.snapshot.lineage, null);
});
test("rebound and disposed named-view regions ignore late lineage and catalog responses", async () => {
  const peer = source(), model = new NamedViewsModel(peer);
  const held = deferred<ReturnType<typeof lineage>>(); peer.lineage = () => held.promise;
  await model.load(snapshot().snapshot); const pending = model.lineage();
  await model.load(null); held.resolve(lineage()); await pending; assert.equal(model.snapshot.lineage, null);
  const heldCatalog = deferred<ReturnType<typeof catalog>>(); peer.catalog = () => heldCatalog.promise;
  const loading = model.load(snapshot().snapshot); model.dispose(); heldCatalog.resolve(catalog()); await loading;
  assert.equal(model.snapshot.catalog, null);
});
test("missing lineage remains unavailable; denied access removes its capability receipt", async () => {
  const peer = source(), model = new NamedViewsModel(peer); await model.load(snapshot().snapshot);
  peer.lineage = async () => { throw new ReadFailure("unavailable"); }; await model.lineage();
  assert.equal(model.snapshot.lineagePhase, "failed"); assert.equal(model.snapshot.error?.kind, "unavailable");
  assert.equal(model.snapshot.catalog?.available("execution_topology"), true);
  peer.lineage = async () => { throw new ReadFailure("denied"); }; await model.lineage();
  assert.equal(model.snapshot.phase, "denied"); assert.equal(model.snapshot.catalog, null);
});
