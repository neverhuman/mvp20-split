import { test } from "node:test";
import assert from "node:assert/strict";
import { ExploreModel } from "../../src/page_models/explore/model.js";
import type { ExploreSources } from "../../src/page_models/explore/model.js";
import { ExploreContext } from "../../src/page_models/explore/context.js";
import { ScientificReadFailure } from "../../src/transport/scientific/failure.js";
import { decodeKnowledge as knowledgeDecoder } from "../../src/contracts/scientific/knowledge.js";
import { decodeResearch as researchDecoder } from "../../src/contracts/scientific/research.js";
import knowledge from "../fixtures/scientific/knowledge.json" with { type: "json" };
import research from "../fixtures/scientific/research.json" with { type: "json" };
import { deferred } from "../fixtures/observations.js";
import trace from "../fixtures/scientific/provenance-trace.json" with { type: "json" };
import { decodeProvenance } from "../../src/contracts/scientific/provenance.js";
import exploreFixture from "../fixtures/scientific/explore.json" with { type: "json" };

const decodeKnowledge: typeof knowledgeDecoder = (name, value) => knowledgeDecoder(name, structuredClone(value));
const decodeResearch: typeof researchDecoder = (name, value) => researchDecoder(name, structuredClone(value));
const search = () => decodeKnowledge("search_request", knowledge.search_request);
const page = () => decodeKnowledge("search_page", knowledge.search_page);
const property = () => decodeResearch("property_request", research.property_request);
const graphPins = () => ({ graph: search().revision, experiment: null, observations: [] });
const researchPins = () => ({ graph: null, experiment: property().experiment, observations: property().observations });
const peers = (): ExploreSources => ({
  knowledge: { search: async () => page(), neighborhood: async () => decodeKnowledge("neighborhood_page", knowledge.neighborhood_page), detail: async () => decodeKnowledge("object_detail", knowledge.object_detail) },
  research: { specimens: async () => decodeResearch("specimen_page", research.specimen_page), properties: async () => decodeResearch("property_page", research.property_page), series: async () => decodeResearch("series_page", research.series_page) },
  data: { span: async span => ({ span, text: "synthetic", artifact_sha256: span.source.raw.sha256, span_sha256: span.sha256 }),
    artifact: async reference => reference, trace: async () => { throw new ScientificReadFailure("unavailable"); }, derivation: async () => { throw new ScientificReadFailure("unavailable"); } },
});

test("prepared-state inspection uses exact owner references and cancels older selection", async () => {
  const first = decodeProvenance("material", structuredClone(exploreFixture.material_records[0]));
  const second = decodeProvenance("material", structuredClone(exploreFixture.material_records[1]));
  const held = deferred<typeof first>(), source = peers();
  source.records = { material: async ref => ref.material_state_id === first.reference.material_state_id ? held.promise : second };
  const model = new ExploreModel(source);
  model.bind({ graph: null, experiment: exploreFixture.research.property_request.experiment, observations: exploreFixture.research.property_request.observations });
  const old = model.material(first.reference); await model.material(second.reference);
  held.resolve(first); await old;
  assert.deepEqual(model.snapshot.regions.material.value, second);
  assert.equal(model.snapshot.regions.material.value?.preparation[0]?.context.conditions[0]?.quantity.value, "120.0");
  model.clearInspection(); assert.equal(model.snapshot.regions.material.phase, "idle"); assert.equal(model.snapshot.regions.material.value, null);
});

test("missing material loader and foreign state have explicit failures", async () => {
  const material = decodeProvenance("material", structuredClone(exploreFixture.material_records[0]));
  const model = new ExploreModel(peers());
  model.bind({ graph: null, experiment: exploreFixture.research.property_request.experiment, observations: exploreFixture.research.property_request.observations });
  await model.material(material.reference); assert.equal(model.snapshot.regions.material.phase, "unavailable");
  await model.material({ ...material.reference, scope: { ...material.reference.scope, project_id: "foreign" } });
  assert.equal(model.snapshot.regions.material.error?.kind, "invalid_request");
});

test("Explore supports graph-only and laboratory-only pins and rejects cross-scope or duplicate context", () => {
  assert.equal(new ExploreContext(graphPins()).pins.experiment, null);
  assert.equal(new ExploreContext(researchPins()).pins.graph, null);
  const pins = researchPins(); pins.observations.push(structuredClone(pins.observations[0]!));
  assert.throws(() => new ExploreContext(pins), /selection is invalid/);
  const foreign = researchPins(); foreign.observations[0]!.scope.project_id = "foreign";
  assert.throws(() => new ExploreContext(foreign), /selection is invalid/);
  assert.throws(() => new ExploreContext({ graph: null, experiment: null, observations: [] }));
  const snapshot = new ExploreContext(graphPins());
  assert.throws(() => { snapshot.pins.graph!.revision++; });
});

test("search pages replace bounded state and retain partial versus empty distinction", async () => {
  const source = peers(), model = new ExploreModel(source); model.bind(graphPins());
  const partial = page(); partial.next_position = { entity_offset: 1, assertion_offset: 0, query_sha256: partial.query_sha256 };
  source.knowledge.search = async () => partial;
  await model.search(search()); assert.equal(model.snapshot.regions.search.phase, "partial");
  const empty = page(); empty.entities = []; empty.next_position = null;
  source.knowledge.search = async () => empty;
  await model.search(search()); assert.equal(model.snapshot.regions.search.phase, "empty");
  assert.equal(model.snapshot.regions.search.value?.entities.length, 0);
  const full = page(); full.next_position = null; source.knowledge.search = async () => full;
  await model.search(search()); assert.equal(model.snapshot.regions.search.phase, "ready");
  full.entities[0]!.label = "changed caller";
  assert.notEqual(model.snapshot.regions.search.value?.entities[0]!.label, "changed caller");
  assert.throws(() => { model.snapshot.regions.search.value!.entities[0]!.label = "mutation"; });
});

test("late responses after rebind cannot replace the newer selected graph", async () => {
  const source = peers(), held = deferred<ReturnType<typeof page>>(); source.knowledge.search = () => held.promise;
  const model = new ExploreModel(source); model.bind(graphPins()); const pending = model.search(search());
  const next = graphPins(); next.graph.revision++;
  model.bind(next); held.resolve(page()); await pending;
  assert.equal(model.snapshot.context?.graph?.revision, next.graph.revision);
  assert.equal(model.snapshot.regions.search.value, null);
});

test("a newer request wins even when an older peer ignores cancellation", async () => {
  const source = peers(), held = deferred<ReturnType<typeof page>>(); source.knowledge.search = () => held.promise;
  const model = new ExploreModel(source); model.bind(graphPins()); const old = model.search(search());
  const newer = page(); newer.entities[0]!.label = "new selection"; source.knowledge.search = async () => newer;
  await model.search(search()); held.resolve(page()); await old;
  assert.equal(model.snapshot.regions.search.value?.entities[0]!.label, "new selection");
});

test("synchronous subscriber rebind prevents the superseded request from being sent", async () => {
  const source = peers(); let calls = 0; source.knowledge.search = async () => { calls++; return page(); };
  const model = new ExploreModel(source); model.bind(graphPins());
  const unsubscribe = model.subscribe(() => { if (model.snapshot.regions.search.phase === "loading") model.bind(null); });
  await model.search(search()); assert.equal(calls, 0); assert.equal(model.snapshot.context, null); unsubscribe();
});

test("hiding and disposal cancel reads, clear protected values and prohibit hidden work", async () => {
  const source = peers(), model = new ExploreModel(source); model.bind(graphPins()); await model.search(search());
  model.visibility(false); assert.equal(model.snapshot.regions.search.phase, "stale"); assert.equal(model.snapshot.regions.search.value, null);
  let calls = 0; source.knowledge.search = async () => { calls++; return page(); };
  await model.search(search()); assert.equal(calls, 0);
  model.visibility(true); await model.search(search()); assert.equal(calls, 1);
  const held = deferred<ReturnType<typeof page>>(); source.knowledge.search = () => held.promise;
  const pending = model.search(search()); model.dispose(); held.resolve(page()); await pending;
  model.bind(graphPins()); model.visibility(true); await model.search(search()); assert.equal(model.snapshot.context, null);
});

test("unrequested Explore lanes remain idle across hide, reveal and mode suspension", () => {
  const model = new ExploreModel(peers()); model.bind(graphPins());
  model.visibility(false); model.suspend(["neighborhood", "properties", "series"]); model.visibility(true);
  for (const region of Object.values(model.snapshot.regions)) {
    assert.equal(region.phase, "idle"); assert.equal(region.value, null);
  }
  model.dispose();
});

test("only previously requested lanes need a fresh read after visibility changes", async () => {
  const model = new ExploreModel(peers()); model.bind(graphPins()); await model.search(search());
  model.visibility(false); model.visibility(true);
  assert.equal(model.snapshot.regions.search.phase, "stale"); assert.equal(model.snapshot.regions.search.value, null);
  for (const [name, region] of Object.entries(model.snapshot.regions)) {
    if (name !== "search") assert.equal(region.phase, "idle");
  }
  model.dispose();
});

for (const kind of ["denied", "query_conflict"] as const) test(`${kind} clears every region and prevents a late peer restoring data`, async () => {
  const source = peers(), model = new ExploreModel(source); model.bind(graphPins()); await model.search(search());
  const held = deferred<ReturnType<typeof decodeKnowledge<"neighborhood_page">>>(); source.knowledge.neighborhood = () => held.promise;
  const pending = model.neighborhood(decodeKnowledge("neighborhood_request", knowledge.neighborhood_request));
  source.knowledge.detail = async () => { throw new ScientificReadFailure(kind); };
  await model.detail(decodeKnowledge("object_request", knowledge.object_request));
  held.resolve(decodeKnowledge("neighborhood_page", knowledge.neighborhood_page)); await pending;
  for (const region of Object.values(model.snapshot.regions)) { assert.equal(region.value, null); assert.equal(region.phase, kind === "denied" ? "denied" : "stale"); }
});

test("unavailable, timeout and arbitrary errors expose sanitized distinct states", async () => {
  const source = peers(), model = new ExploreModel(source); model.bind(graphPins());
  for (const [error, phase, kind] of [[new ScientificReadFailure("unavailable"), "unavailable", "unavailable"], [new ScientificReadFailure("timeout"), "failed", "timeout"], [new Error("private credential"), "failed", "network"]] as const) {
    source.knowledge.search = async () => { throw error; }; await model.search(search());
    assert.equal(model.snapshot.regions.search.phase, phase); assert.equal(model.snapshot.regions.search.error?.kind, kind);
    assert.ok(!model.snapshot.regions.search.error?.message.includes("private credential"));
  }
});

test("requests outside exact selected graph, experiment or observation set never reach peers", async () => {
  const source = peers(), model = new ExploreModel(source); let calls = 0;
  source.knowledge.search = async () => { calls++; return page(); };
  model.bind(graphPins()); const wrong = search(); wrong.revision.revision++; await model.search(wrong);
  assert.equal(calls, 0); assert.equal(model.snapshot.regions.search.error?.kind, "invalid_request");
  source.research.properties = async () => { calls++; return decodeResearch("property_page", research.property_page); };
  model.bind(researchPins()); const query = property(); query.observations[0]!.revision++; await model.properties(query);
  assert.equal(calls, 0);
  const series = decodeResearch("series_request", research.series_request); series.observation.revision++;
  await model.series(series); assert.equal(model.snapshot.regions.series.error?.kind, "invalid_request");
});

test("scientific pages preserve measurement/context claims and original series ordering", async () => {
  const model = new ExploreModel(peers()); model.bind(researchPins());
  await model.specimens(decodeResearch("specimen_request", research.specimen_request));
  await model.properties(property()); await model.series(decodeResearch("series_request", research.series_request));
  assert.deepEqual(model.snapshot.regions.properties.value, research.property_page);
  assert.deepEqual(model.snapshot.regions.series.value?.points, research.series_page.points);
  assert.equal(model.snapshot.regions.properties.phase, "ready");
});

test("selected source is exact immutable provenance and a new object clears the previous source", async () => {
  const source = peers(), model = new ExploreModel(source); model.bind(graphPins());
  const span = decodeProvenance("span", structuredClone(trace.trace.fields[0]!.spans[0]));
  span.source.scope = graphPins().graph.graph.scope; span.source.raw.scope = span.source.scope;
  await model.source(span);
  assert.equal(model.snapshot.regions.source.phase, "ready");
  assert.deepEqual(model.snapshot.regions.source.value?.span, span);
  span.start++; assert.notEqual(model.snapshot.regions.source.value?.span.start, span.start);
  await model.detail(decodeKnowledge("object_request", knowledge.object_request));
  assert.equal(model.snapshot.regions.source.value, null); assert.equal(model.snapshot.regions.detail.phase, "ready");
  span.source.scope = { tenant_id: "foreign", project_id: "foreign" }; await model.source(span);
  assert.equal(model.snapshot.regions.source.error?.kind, "invalid_request");
});

test("neighborhood remains partial when it exposes unresolved endpoints", async () => {
  const source = peers(), model = new ExploreModel(source); model.bind(graphPins());
  const neighborhood = decodeKnowledge("neighborhood_page", knowledge.neighborhood_page);
  neighborhood.next_position = null; neighborhood.unresolved_entities = [neighborhood.request.focus];
  source.knowledge.neighborhood = async () => neighborhood;
  await model.neighborhood(decodeKnowledge("neighborhood_request", knowledge.neighborhood_request));
  assert.equal(model.snapshot.regions.neighborhood.phase, "partial");
  neighborhood.unresolved_entities = []; await model.neighborhood(decodeKnowledge("neighborhood_request", knowledge.neighborhood_request));
  assert.equal(model.snapshot.regions.neighborhood.phase, "ready");
});

test("loading receives copied selection and clearing context prevents further work", async () => {
  const source = peers(), model = new ExploreModel(source); model.bind(graphPins());
  const held = deferred<ReturnType<typeof page>>(); let received: ReturnType<typeof search> | undefined;
  source.knowledge.search = (request) => { received = request; return held.promise; };
  const query = search(), old = structuredClone(query); const pending = model.search(query); query.revision.revision++;
  assert.deepEqual(received, old); model.bind(null); held.resolve(page()); await pending;
  assert.equal(model.snapshot.regions.search.value, null);
  await model.search(search()); assert.equal(model.snapshot.regions.search.phase, "idle");
});

test("suspending hidden regions cancels their late reads without clearing a visible region", async () => {
  const source = peers(), model = new ExploreModel(source); model.bind(graphPins());
  await model.detail(decodeKnowledge("object_request", knowledge.object_request));
  const held = deferred<ReturnType<typeof page>>(); source.knowledge.search = () => held.promise;
  const pending = model.search(search()); model.suspend(["search"]); held.resolve(page()); await pending;
  assert.equal(model.snapshot.regions.search.phase, "stale"); assert.equal(model.snapshot.regions.detail.phase, "ready");
  model.dispose(); model.suspend(["search"]); assert.equal(model.snapshot.context, null);
});

test("selecting an unrelated artifact clears old claim provenance and fences scope", async () => {
  const source = peers(), model = new ExploreModel(source); model.bind(graphPins());
  await model.detail(decodeKnowledge("object_request", knowledge.object_request));
  const ref = decodeProvenance("artifact", structuredClone(trace.trace.source.raw)); ref.scope = graphPins().graph.graph.scope;
  await model.artifact(ref, true);
  assert.equal(model.snapshot.regions.detail.value, null); assert.deepEqual(model.snapshot.regions.artifact.value, ref);
  await model.derivation(ref); assert.equal(model.snapshot.regions.derivation.phase, "unavailable");
  const traceRef = decodeProvenance("trace_ref", structuredClone(trace.reference)); traceRef.scope = ref.scope;
  await model.trace(traceRef); assert.equal(model.snapshot.regions.trace.phase, "unavailable");
  traceRef.scope = { tenant_id: "foreign", project_id: "foreign" }; await model.trace(traceRef);
  assert.equal(model.snapshot.regions.trace.error?.kind, "invalid_request");
});
