import { test } from "node:test";
import assert from "node:assert/strict";
import { NavigationModel } from "../../src/page_models/navigation.js";
import type { NavigationSource } from "../../src/transport/observations.js";
import { ReadFailure } from "../../src/transport/failure.js";
import { scopes, topology } from "../fixtures/navigation.js";
import { deferred, id, snapshot } from "../fixtures/observations.js";

const source = (): NavigationSource => ({ scopes: async () => scopes(), topology: async () => topology() });
test("navigation owns scopes and topology under the Monitor anchor only", async () => {
  let calls = 0;
  const peer = source(); const original = peer.scopes;
  peer.scopes = async (...args) => { calls++; assert.equal(args[1], "snapshot-1"); return original(...args); };
  const model = new NavigationModel(peer);
  await model.scopes(); assert.equal(calls, 0);
  model.bind(snapshot().snapshot); await model.scopes(); await model.open(id(100));
  assert.equal(model.snapshot.scopes?.scope_count, 1);
  assert.equal(model.snapshot.topology?.visibleEdges.length, 1);
  model.bind(snapshot().snapshot); assert.equal(model.snapshot.topologyPhase, "ready");
  model.bind(snapshot({ revision: 2 }).snapshot); assert.equal(model.snapshot.topology, null);
  model.dispose(); await model.scopes(); assert.equal(calls, 1);
});

test("late uncancellable navigation cannot replace a newer anchor or scope", async () => {
  const held = deferred<ReturnType<typeof topology>>(); const peer = source();
  peer.topology = () => held.promise;
  const model = new NavigationModel(peer); model.bind(snapshot().snapshot);
  const pending = model.open(id(100));
  model.bind(snapshot({ revision: 2 }).snapshot); held.resolve(topology()); await pending;
  assert.equal(model.snapshot.topology, null);
  const scopeHeld = deferred<ReturnType<typeof scopes>>(); peer.scopes = () => scopeHeld.promise;
  const load = model.scopes(); model.bind(null); scopeHeld.resolve(scopes()); await load;
  assert.equal(model.snapshot.scopes, null);
});

test("denial fences simultaneous topology and clears both protected regions", async () => {
  const held = deferred<ReturnType<typeof topology>>(); const peer = source();
  peer.scopes = async () => { throw new ReadFailure("denied"); }; peer.topology = () => held.promise;
  const model = new NavigationModel(peer); model.bind(snapshot().snapshot);
  const group = model.scopes(), graph = model.open(id(100)); await group; held.resolve(topology()); await graph;
  assert.equal(model.snapshot.phase, "denied"); assert.equal(model.snapshot.topology, null);
});

test("navigation rejects foreign parent/revision and exposes unavailable projections", async () => {
  const peer = source(), model = new NavigationModel(peer); model.bind(snapshot().snapshot);
  await model.scopes(id(3)); assert.equal(model.snapshot.error?.kind, "invalid_response");
  peer.scopes = async () => ({ ...scopes(), cut: snapshot({ revision: 2 }).snapshot.cut });
  await model.scopes(); assert.equal(model.snapshot.phase, "stale");
  model.bind(snapshot().snapshot); peer.topology = async () => { throw new ReadFailure("unavailable"); };
  await model.open(id(100)); assert.equal(model.snapshot.topologyPhase, "failed");
  assert.equal(model.snapshot.error?.kind, "unavailable");
});

test("progressive topology pages retain authored links and reject revision drift", async () => {
  const peer = source(), page = topology();
  peer.topology = async (_run, _scope, _snapshot, _query, cursor) => cursor
    ? { ...page, nodes: page.nodes.slice(1), edges: [] }
    : { ...page, nodes: page.nodes.slice(0, 1), next_cursor: "next" };
  const model = new NavigationModel(peer); model.bind(snapshot().snapshot); await model.open(id(100));
  assert.equal(model.snapshot.topology?.unresolvedEdges, 1); await model.more();
  assert.equal(model.snapshot.topology?.visibleEdges.length, 1);
  await model.open(id(100)); peer.topology = async () => ({ ...page, cut: snapshot({ revision: 2 }).snapshot.cut });
  await model.more(); assert.equal(model.snapshot.phase, "stale"); assert.equal(model.snapshot.topology, null);
});
