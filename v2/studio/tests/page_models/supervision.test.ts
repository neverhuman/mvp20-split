import { test } from "node:test";
import assert from "node:assert/strict";
import checkpoints from "../fixtures/supervision/checkpoints.json" with { type: "json" };
import requests from "../fixtures/supervision/requests.json" with { type: "json" };
import context from "../fixtures/supervision/context.json" with { type: "json" };
import responses from "../fixtures/supervision/responses.json" with { type: "json" };
import { decodeSupervision } from "../../src/contracts/supervision.js";
import { SupervisionModel } from "../../src/page_models/supervision/model.js";
import type { SupervisionSource } from "../../src/transport/supervision/client.js";
import { ReadFailure } from "../../src/transport/failure.js";
import { FollowupModel } from "../../src/page_models/followup/model.js";
import { CriterionModel } from "../../src/page_models/followup/criterion.js";
import { fixture } from "../fixtures/followup.js";
const binding = { run: checkpoints.snapshot.cut.run_id, scope: checkpoints.snapshot.cut.scope };
const checkpoint = decodeSupervision("checkpoints",checkpoints).items[0]!;
const request = decodeSupervision("requests",requests).items[0]!;
function source(): SupervisionSource { return {
  checkpoints: async () => decodeSupervision("checkpoints", structuredClone(checkpoints)),
  requests: async () => decodeSupervision("requests", structuredClone(requests)),
  context: async () => decodeSupervision("context", structuredClone(context)),
  responses: async () => decodeSupervision("responses", structuredClone(responses)),
  decision: async () => { throw new ReadFailure("unavailable"); },
}; }
test("selection drives coherent context and responses, partial outcome and refresh preserves selection", async () => {
  const model = new SupervisionModel(source()); model.bind(binding); await model.refresh();
  assert.equal(model.snapshot.phase,"ready"); await model.selectCheckpoint(checkpoint);
  assert.equal(model.snapshot.decisionUnavailable,true); await model.selectRequest(request);
  assert.equal(model.snapshot.tab,"context"); await model.tab("responses"); await model.refresh();
  assert.equal(model.snapshot.request?.request_sha256,request.request_sha256);
  assert.equal(model.snapshot.tab,"responses"); assert.equal(model.snapshot.phase,"ready");
  await model.checkpoints(); assert.equal(model.snapshot.request,null);
});
test("uncancellable old selection cannot overwrite new binding", async () => {
  let release!: () => void; const held = new Promise<void>(r=>{release=r;}); const s=source();
  s.requests = async () => { await held; return decodeSupervision("requests",requests); };
  const model=new SupervisionModel(s);model.bind(binding);await model.refresh();
  const old=model.selectCheckpoint(checkpoint);model.bind({...binding,run:"replacement"});release();await old;
  assert.equal(model.snapshot.phase,"idle");assert.equal(model.snapshot.page,null);
});
test("denial clears evidence, stale clears snapshot and empty remains empty", async () => {
  for (const [kind,phase] of [["denied","denied"],["resnapshot","stale"],["network","failed"],["unavailable","unavailable"]] as const) {
    const s=source();const model=new SupervisionModel(s);model.bind(binding);await model.refresh();
    s.requests=async()=>{throw new ReadFailure(kind);}; await model.selectCheckpoint(checkpoint);
    assert.equal(model.snapshot.phase,phase);assert.equal(model.snapshot.page,null);
    if(kind==="denied") assert.equal(model.snapshot.checkpoint,null);
  }
  const s=source();s.checkpoints=async()=>({...decodeSupervision("checkpoints",checkpoints),items:[],total:0});
  const model=new SupervisionModel(s);model.bind(binding);await model.refresh();assert.equal(model.snapshot.phase,"empty");
  model.dispose();await model.refresh();assert.equal(model.snapshot.phase,"idle");
});
test("bounded next page replaces rows and mismatched epoch invalidates", async () => {
  const s=source();let calls=0;
  s.checkpoints=async(_b,c)=>{calls++;return {...decodeSupervision("checkpoints",checkpoints),next_cursor:c?null:"next"};};
  const model=new SupervisionModel(s);model.bind(binding);await model.refresh();await model.next();
  assert.equal(calls,2);assert.equal(model.snapshot.page?.items.length,1);
  s.requests=async()=>({...decodeSupervision("requests",requests),snapshot:{...requests.snapshot,epoch:"f".repeat(64)}});
  await model.selectCheckpoint(checkpoint);assert.equal(model.snapshot.phase,"stale");assert.equal(model.snapshot.page,null);
});

test("exact outcome and denied outcome are distinct; requests/back, invalidate and unsubscribe are owned", async () => {
  const s=source();s.decision=async()=>decodeSupervision("decision",{schema_version:"1",profile:"checkpoint-decision.v1",reference:requests.reference,revision:1,checkpoint_seed_sha256:"a".repeat(64),outcome:{kind:"fallback",action:"continue_unchanged",reason_code:"checkpoint_provider_unconfigured"}});
  const model=new SupervisionModel(s);let updates=0;const unsubscribe=model.subscribe(()=>{updates++;});model.bind(binding);await model.refresh();
  await model.selectCheckpoint(checkpoint);assert.equal(model.snapshot.decision?.outcome.kind,"fallback");
  await model.selectRequest(request);await model.requests();assert.equal(model.snapshot.tab,"requests");assert.equal(model.snapshot.request,null);
  model.invalidate();assert.equal(model.snapshot.phase,"stale");assert.equal(model.snapshot.page,null);
  await model.refresh();s.decision=async()=>{throw new ReadFailure("denied");};await model.selectCheckpoint(checkpoint);
  assert.equal(model.snapshot.phase,"denied");assert.equal(model.snapshot.checkpoint,null);
  unsubscribe();const count=updates;model.dispose();await model.next();assert.equal(updates,count);
});

test("proposal selection is restricted to current response page and cleared with supervisor lifecycle", async () => {
  const f = fixture(); let calls = 0;
  const followup = new FollowupModel({ async load(selection) { calls++; return { selection, record: f.record, document: { kind: "followup", draft: f.document } }; } });
  const criterion = new CriterionModel({ async load() { throw Error("unused"); } });
  const model = new SupervisionModel(source(), followup, criterion); model.bind(binding);
  await model.inspectResponse(f.record.response_id); assert.equal(calls, 0);
  await model.refresh(); await model.selectCheckpoint(checkpoint); await model.selectRequest(request); await model.tab("responses");
  await model.inspectResponse("foreign"); assert.equal(calls, 0);
  await model.inspectResponse(f.record.response_id); assert.equal(followup.snapshot.phase, "ready");
  await model.tab("context"); assert.equal(followup.snapshot.phase, "idle");
  await model.tab("responses"); await model.inspectResponse(f.record.response_id);
  model.invalidate(); assert.equal(followup.snapshot.page, null); assert.equal(criterion.snapshot.records, null);
  model.dispose(); await followup.select(f.selection); assert.equal(followup.snapshot.phase, "idle");
});
