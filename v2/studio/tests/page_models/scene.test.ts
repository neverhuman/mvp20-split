import { test } from "node:test";
import assert from "node:assert/strict";
import { SceneWindow, type ScenePage } from "../../src/page_models/scene.js";

const page = (offset = 0): ScenePage => ({ total: 10000, offset,
  nodes: Array.from({ length: 200 }, (_, i) => ({ id: `n${offset+i}`, label: `Node ${offset+i}`, status: "waiting", x: i*20, y: 0 })),
  edges: [{ id: `e${offset}`, source: `n${offset}`, target: `n${offset+1}` }] });

test("scene holds only 200 records and preserves selected context and viewport across windows", () => {
  const scene = new SceneWindow(); scene.replace(page()); scene.select("n2");
  scene.setViewport({ x: -500, y: 30, zoom: 0.5 }); scene.replace(page(200));
  assert.equal(scene.nodes.length, 200); assert.equal(scene.omitted, 9800);
  assert.equal(scene.selected?.id, "n2"); assert.equal(scene.selectionOutsideWindow, true);
  assert.deepEqual(scene.viewport, { x: -500, y: 30, zoom: 0.5 });
  scene.replace(page()); assert.equal(scene.selectionOutsideWindow, false);
  assert.throws(() => scene.select("n9999"));
});

test("scene validates atomically and cannot invent missing graph connections", () => {
  const scene = new SceneWindow(); scene.replace(page()); const before = scene.nodes;
  const invalid = [
    { ...page(), total: 199 }, { ...page(), offset: -1 }, { ...page(), total: NaN },
    { ...page(), nodes: [...page().nodes, page().nodes[0]!] },
    { ...page(), nodes: [page().nodes[0]!, page().nodes[0]!] },
    { ...page(), edges: [{ id: "e", source: "n0", target: "unloaded" }] },
    { ...page(), edges: [page().edges[0]!, page().edges[0]!] },
  ];
  for (const value of invalid) { assert.throws(() => scene.replace(value)); assert.equal(scene.nodes, before); }
  for (const zoom of [0, 3, NaN]) assert.throws(() => scene.setViewport({ x: 0, y: 0, zoom }));
});
