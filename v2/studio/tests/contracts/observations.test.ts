import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { decodeObservation } from "../../src/contracts/observations.js";
import { snapshot, detail, events, id } from "../fixtures/observations.js";

test("published schemas accept all four observation roots without modifying inputs", () => {
  const page = snapshot(), original = structuredClone(page);
  assert.equal(decodeObservation("snapshot", page), page);
  assert.deepEqual(page, original);
  assert.equal(decodeObservation("detail", detail(1)).node.activation_id, id(1));
  assert.equal(decodeObservation("events", events([2])).entries[0]?.revision, 2);
  const values = decodeObservation("values", { schema_version: "1", cut: page.snapshot.cut, activation_id: id(1), port: "result",
    item_count: 2, items: [{ index: 0, value: { kind: "integer", value: 17, unit: "1" } },
      { index: 1, value: { kind: "missing", member_id: "m1", reason_code: "failed" } }], next_cursor: null });
  assert.equal(values.items[1]?.value.kind, "missing");
});

test("validator rejects coercion, excess nodes, unknown fields and non-invalidation events", () => {
  const bad = snapshot();
  for (const raw of [{ ...bad, nodes: Array(101).fill(bad.nodes[0]) }, { ...bad, injected: "never shown" },
    { ...bad, snapshot: { ...bad.snapshot, node_count: "2" } }]) assert.throws(() => decodeObservation("snapshot", raw));
  assert.throws(() => decodeObservation("events", { ...events([2]), entries: [{ event_id: "e", revision: 2, kind: "execute" }] }));
});

test("generated consumer manifest pins every authoritative schema byte", async () => {
  const manifest = JSON.parse(await readFile("src/contracts/generated/manifest.json", "utf8")) as Record<string, { source: string; sha256: string }>;
  assert.deepEqual(Object.keys(manifest).sort(), ["detail", "events", "snapshot", "values"]);
  for (const entry of Object.values(manifest)) {
    const bytes = await readFile("../" + entry.source);
    assert.equal(createHash("sha256").update(bytes).digest("hex"), entry.sha256);
  }
});
