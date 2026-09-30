import { test } from "node:test";
import assert from "node:assert/strict";
import { AuthoringClient, AuthoringFailure } from "../../../src/transport/authoring.js";
import { DraftCommands } from "../../../src/page_models/design/draft_commands.js";
import type { DraftCommandSource } from "../../../src/page_models/design/draft_commands.js";
import type { DraftCommandReceipt, DraftRevision } from "../../../src/contracts/authoring.js";
import { accepted, local, revision, session } from "../../fixtures/authoring.js";

function source(overrides: Partial<DraftCommandSource>): DraftCommandSource {
  const unexpected = async (): Promise<never> => { throw new Error("unexpected request"); };
  return { submit: unexpected, receipt: unexpected, draft: unexpected, validation: unexpected, ...overrides };
}

test("lost POST acknowledgement reconciles original receipt and exact saved revision without another POST", async () => {
  let posts = 0, reads = 0;
  const state = session(), saved = revision(2), model = new DraftCommands(state, source({
    submit: async () => { posts++; throw new AuthoringFailure("network", true); },
    receipt: async command => { reads++; return accepted(command, saved); },
    draft: async (id, number) => { assert.equal(id, "draft"); assert.equal(number, 2); return saved; },
  }));
  await model.save("save1");
  assert.equal(model.snapshot.phase, "unresolved");
  const original = state.unresolvedCommand;
  await model.reconcile();
  assert.equal(model.snapshot.phase, "settled");
  assert.equal(state.snapshot.base?.head.revision, 2);
  assert.equal(posts, 1); assert.equal(reads, 1);
  assert.equal(original?.identity.command_id, "save1");
});

test("accepted receipt with unavailable follow-up record remains unresolved and retains edits", async () => {
  let fail = true;
  const state = session(), saved = revision(2), model = new DraftCommands(state, source({
    submit: async command => accepted(command, saved), receipt: async command => accepted(command, saved),
    draft: async () => { if (fail) throw new AuthoringFailure("unavailable", false); return saved; },
  }));
  await model.save("save1");
  assert.equal(model.snapshot.phase, "unresolved");
  assert.equal(model.snapshot.error?.commandUnresolved, true);
  state.edit({ ...local(), title: "Newer local title" }); fail = false;
  await model.reconcile();
  assert.equal(state.snapshot.local.title, "Newer local title");
  assert.equal(state.snapshot.base?.head.revision, 2);
});

test("denial fences an uncancellable late record and blocks later requests", async () => {
  let resolveRecord!: (value: DraftRevision) => void;
  let entered!: () => void;
  const started = new Promise<void>(resolve => { entered = resolve; });
  const state = session(), saved = revision(2), model = new DraftCommands(state, source({
    submit: async command => accepted(command, saved),
    draft: async () => { entered(); return new Promise(resolve => { resolveRecord = resolve; }); },
  }));
  const pending = model.save("save1"); await started;
  model.deny(); resolveRecord(saved); await pending;
  assert.equal(model.snapshot.phase, "denied");
  assert.equal(state.snapshot.base, undefined);
  assert.throws(() => model.reconcile(), /session_unavailable/);
});

test("a changed terminal receipt cannot redirect a later follow-up read", async () => {
  let reads = 0;
  const state = session(), saved = revision(2), model = new DraftCommands(state, source({
    submit: async command => accepted(command, saved),
    receipt: async command => {
      const result = accepted(command, saved);
      if (result.outcome.status === "accepted") result.outcome.committed.object_id = "different";
      return result;
    },
    draft: async () => { reads++; throw new AuthoringFailure("network", false); },
  }));
  await model.save("save1"); await model.reconcile();
  assert.equal(reads, 1);
  assert.equal(model.snapshot.phase, "unresolved");
  assert.equal(model.snapshot.error?.kind, "invalid_response");
});

test("pending and rejected owner outcomes remain distinct; denial in a read clears protected state", async () => {
  const state = session();
  let outcome: "pending" | "rejected" = "pending";
  const reply = (command: Parameters<DraftCommandSource["submit"]>[0]): DraftCommandReceipt => ({ outcome: {
    binding: accepted(command, revision(2)).outcome.binding,
    ...(outcome === "pending" ? { status: "pending" as const } : { status: "rejected" as const, reason_code: "draft_revision_conflict" }),
  } });
  const model = new DraftCommands(state, source({ submit: async command => reply(command), receipt: async command => reply(command) }));
  await model.save("save1"); assert.equal(model.snapshot.phase, "unresolved");
  outcome = "rejected"; await model.reconcile();
  assert.equal(model.snapshot.phase, "settled"); assert.equal(state.snapshot.reason, "draft_revision_conflict");
  const denied = new DraftCommands(state, source({ submit: async () => { throw new AuthoringFailure("denied", true); } }));
  await denied.save("save2"); assert.equal(denied.snapshot.phase, "denied"); assert.equal(state.snapshot.base, undefined);
});


test("POST identity collision cannot reconcile an older command as this save or discard local work", async () => {
  const state = session();
  const changed = local(); changed.definition.body.nodes[0]!.node_id = "locally-edited";
  state.edit(changed);
  let reads = 0;
  const client = new AuthoringClient(async (_url, init) => {
    if (init?.method === "POST") return new Response(null, { status: 409 });
    reads++;
    const old = accepted(state.unresolvedCommand!, revision(2));
    return new Response(JSON.stringify(String(_url).includes("definition-commands") ? old : revision(2)),
      { headers: { "Content-Type": "application/json" } });
  });
  const model = new DraftCommands(state, client);
  await model.save("colliding-id");
  try { await model.reconcile(); } catch { /* A known collision must block receipt adoption. */ }
  assert.equal(state.snapshot.local.definition.body.nodes[0]!.node_id, "locally-edited");
  assert.equal(state.snapshot.base?.head.revision, 1);
  assert.equal(model.snapshot.phase, "conflict");
  assert.equal(reads, 0);
  assert.throws(() => model.save("new-id"), /command_identity_conflict/);
});
