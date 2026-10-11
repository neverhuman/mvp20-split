import { test } from "node:test";
import assert from "node:assert/strict";
import { CampaignOriginModel } from "../../../src/page_models/campaign_origin/model.js";
import { ScientificReadFailure } from "../../../src/transport/scientific/failure.js";
import { originScenario } from "../../fixtures/campaign_origin.js";

test("independent criterion detail becomes visible and denial clears previous protected data", async () => {
  const { origin, question } = originScenario(); let denied = false;
  const model = new CampaignOriginModel({ read: async () => { if (denied) throw new ScientificReadFailure("denied"); return origin; } },
    { read: async () => ({ question, need: null }) });
  await model.load(origin.origin.draft); await model.inspect(0);
  assert.equal(model.snapshot.detail.phase, "ready"); assert.deepEqual(model.snapshot.detail.value?.question, question);
  denied = true; await model.load(origin.origin.draft);
  assert.equal(model.snapshot.phase, "denied"); assert.equal(model.snapshot.origin, null); assert.equal(model.snapshot.detail.value, null);
  model.dispose();
});

test("a late origin reply cannot restore data after a newer denial", async () => {
  const { origin } = originScenario(); let resolve!: (value: typeof origin) => void, calls = 0;
  const model = new CampaignOriginModel({ read: async () => {
    if (++calls === 1) return new Promise<typeof origin>(done => { resolve = done; });
    throw new ScientificReadFailure("denied");
  } }, { read: async () => { throw Error("unused"); } });
  const pending = model.load(origin.origin.draft); await model.load(origin.origin.draft); resolve(origin); await pending;
  assert.equal(model.snapshot.phase, "denied"); assert.equal(model.snapshot.origin, null); model.dispose();
});

test("missing association and unavailable endpoint stay distinct", async () => {
  const { origin } = originScenario(); let unavailable = false;
  const model = new CampaignOriginModel({ read: async () => {
    if (unavailable) throw new ScientificReadFailure("unavailable"); return null;
  } }, { read: async () => { throw Error("unused"); } });
  await model.load(origin.origin.draft); assert.equal(model.snapshot.phase, "not_recorded");
  unavailable = true; await model.load(origin.origin.draft); assert.equal(model.snapshot.phase, "failed");
  model.dispose();
});

test("late Research detail cannot outlive a replaced origin read", async () => {
  const { origin, question } = originScenario(); let finish!: (value: { question: typeof question; need: null }) => void;
  const model = new CampaignOriginModel({ read: async () => origin }, {
    read: async () => new Promise(done => { finish = done; }),
  });
  await model.load(origin.origin.draft);
  const pending = model.inspect(0); await model.load(origin.origin.draft);
  finish({ question, need: null }); await pending;
  assert.equal(model.snapshot.detail.phase, "idle"); assert.equal(model.snapshot.detail.value, null); model.dispose();
});
