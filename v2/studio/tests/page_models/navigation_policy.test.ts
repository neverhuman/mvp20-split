import { test } from "node:test";
import assert from "node:assert/strict";
import { NavigationModel } from "../../src/page_models/navigation.js";
import type { NavigationSource } from "../../src/transport/observations.js";
import { scopes, topology } from "../fixtures/navigation.js";
import { snapshot, deferred, id } from "../fixtures/observations.js";

test("hidden navigation fences requests and restores scope, neighborhood and viewport at the new cut", async () => {
  const calls: string[] = [];
  const peer: NavigationSource = {
    scopes: async (_run, pin) => { calls.push("scopes"); return { ...scopes(), cut: snapshot({ revision: Number(pin.slice(-1)) }).snapshot.cut }; },
    topology: async (_run, scope, pin, query) => { calls.push("topology"); return { ...topology(),
      graph_scope: { ...topology().graph_scope, scope_key: scope }, cut: snapshot({ revision: Number(pin.slice(-1)) }).snapshot.cut,
      query: { focus_activation_id: query.focus_activation_id ?? null, radius: query.radius ?? 1 } }; },
  };
  const model = new NavigationModel(peer);
  await model.observe(snapshot().snapshot, true);
  await model.open(id(100), { focus_activation_id: id(1), radius: 1 });
  model.setViewport({ x: 200, y: -100, zoom: 1.2 });
  await model.observe(snapshot({ revision: 2 }).snapshot, false);
  assert.equal(model.snapshot.phase, "stale"); assert.deepEqual(calls, ["scopes", "topology"]);
  await model.observe(snapshot({ revision: 2 }).snapshot, true);
  assert.equal(model.snapshot.topology?.page.cut.revision, 2);
  assert.equal(model.snapshot.topology?.page.query.focus_activation_id, id(1));
  assert.deepEqual(model.snapshot.viewport, { x: 200, y: -100, zoom: 1.2 });
  await model.observe(snapshot({ revision: 2 }).snapshot, true);
  assert.equal(calls.length, 4);
  await model.observe(null, false, true); assert.equal(model.snapshot.phase, "denied");
  await model.observe(snapshot({ revision: 3 }).snapshot, true);
  assert.equal(model.snapshot.topology, null);
});

test("a hidden or replaced context cannot resume an old uncancellable scope fetch", async () => {
  const held = deferred<ReturnType<typeof scopes>>(); let topologyCalls = 0;
  const peer: NavigationSource = { scopes: () => held.promise, topology: async () => { topologyCalls++; return topology(); } };
  const model = new NavigationModel(peer);
  const pending = model.observe(snapshot().snapshot, true);
  await model.observe(snapshot().snapshot, false); held.resolve(scopes()); await pending;
  const hidden = model.snapshot;
  assert.equal(hidden.phase, "stale"); assert.equal(hidden.scopes, null); assert.equal(topologyCalls, 0);
  const foreign = snapshot().snapshot; foreign.cut.scope = { tenant_id: "other", project_id: "other" };
  peer.scopes = async (_run, _pin, parent) => { assert.equal(parent, undefined); return { ...scopes(), cut: foreign.cut }; };
  await model.observe(foreign, true); assert.equal(model.snapshot.scopes?.cut.scope.tenant_id, "other");
  assert.equal(model.snapshot.topology, null);
});
