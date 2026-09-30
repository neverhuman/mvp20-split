import { test } from "node:test";
import assert from "node:assert/strict";
import { TopologyWindow } from "../../src/page_models/topology_window.js";
import { topology } from "../fixtures/navigation.js";
import { id } from "../fixtures/observations.js";

test("authored links remain unresolved until their target page arrives", () => {
  const page = topology();
  const first = { ...page, nodes: page.nodes.slice(0, 1), next_cursor: "next" };
  const window = TopologyWindow.open(page.cut, id(100), page.query, first);
  assert.equal(window.omittedNodes, 1);
  assert.equal(window.unresolvedEdges, 1);
  assert.deepEqual(window.visibleEdges, []);
  const full = window.append({ ...page, nodes: page.nodes.slice(1), edges: [] });
  assert.equal(full.omittedNodes, 0);
  assert.deepEqual(full.visibleEdges, page.edges);
  assert.equal(window.omittedNodes, 1);
  const reordered = Object.fromEntries(Object.entries(page.graph_scope).reverse()) as typeof page.graph_scope;
  assert.equal(window.append({ ...page, graph_scope: reordered, nodes: page.nodes.slice(1), edges: [] }).omittedNodes, 0);
});

test("scope, query, revision and false completeness cannot mix in topology", () => {
  const page = topology();
  const open = (raw = page) => TopologyWindow.open(page.cut, id(100), page.query, raw);
  for (const bad of [
    { ...page, graph_scope: { ...page.graph_scope, scope_key: id(200) } },
    { ...page, cut: { ...page.cut, revision: 2 } },
    { ...page, query: { ...page.query, radius: 2 } },
    { ...page, nodes: page.nodes.slice(0, 1) },
    { ...page, edges: [] },
    { ...page, edges: [{ ...page.edges[0]!, target: id(9) }] },
    { ...page, nodes: [page.nodes[0]!, page.nodes[0]!] },
  ]) assert.throws(() => open(bad));
  const partial = open({ ...page, nodes: page.nodes.slice(0, 1), next_cursor: "next" });
  assert.throws(() => partial.append(page));
  assert.throws(() => partial.append({ ...page, nodes: page.nodes.slice(1), edges: [], next_cursor: "next" }));
  assert.throws(() => partial.append({ ...page, nodes: page.nodes.slice(1), edges: [], cut: { ...page.cut, revision: 2 } }));
  assert.throws(() => partial.append({ ...page, nodes: page.nodes.slice(1) }));
});
