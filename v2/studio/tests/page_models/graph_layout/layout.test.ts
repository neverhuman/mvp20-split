import { test } from 'node:test';
import assert from 'node:assert/strict';
import { layoutGraph, NODE_WIDTH as W, NODE_HEIGHT as H, type GraphGeometry } from '../../../src/page_models/graph_layout/layout.js';
import type { SceneNode, SceneEdge } from '../../../src/page_models/scene.js';

const node = (id: string): SceneNode => ({ id, label: id.repeat(30), status: 'succeeded', x: 0, y: 0 });
const edge = (source: string, target: string): SceneEdge => ({ id: source + '-' + target, source, target });
function verifyGeometry(graph: GraphGeometry) {
  for (const a of graph.nodes) for (const b of graph.nodes) {
    if (a.id === b.id) continue;
    assert.ok(a.x + W <= b.x || b.x + W <= a.x || a.y + H <= b.y || b.y + H <= a.y, 'node overlap');
  }
  for (const e of graph.edges) {
    const source = graph.nodes.find(n => n.id === e.source)!, target = graph.nodes.find(n => n.id === e.target)!;
    assert.deepEqual(e.points[0], { x: source.x + W / 2, y: source.y + H });
    assert.deepEqual(e.points.at(-1), { x: target.x + W / 2, y: target.y });
    for (let index = 1; index < e.points.length; index++) {
      const a = e.points[index - 1]!, b = e.points[index]!;
      assert.ok(a.x === b.x || a.y === b.y);
      for (const n of graph.nodes) {
        if (n.id === e.source || n.id === e.target) continue;
        const intersects = a.x === b.x
          ? a.x > n.x && a.x < n.x + W && Math.max(a.y, b.y) > n.y && Math.min(a.y, b.y) < n.y + H
          : a.y > n.y && a.y < n.y + H && Math.max(a.x, b.x) > n.x && Math.min(a.x, b.x) < n.x + W;
        assert.equal(intersects, false, 'edge crosses unrelated node');
      }
    }
  }
}
test('branches, joins and skip edges use actual dependencies and avoid node rectangles', async () => {
  const nodes = ['finish', 'right', 'start', 'left', 'join'].map(node);
  const edges = [edge('start', 'right'), edge('start', 'left'), edge('right', 'join'), edge('left', 'join'), edge('join', 'finish'), edge('start', 'finish')];
  const original = structuredClone({ nodes, edges });
  const graph = await layoutGraph(nodes, edges);
  verifyGeometry(graph);
  for (const e of edges) assert.ok(graph.nodes.find(n => n.id === e.source)!.y < graph.nodes.find(n => n.id === e.target)!.y);
  const reordered = await layoutGraph([...nodes].reverse(), [...edges].reverse());
  assert.deepEqual([...graph.nodes].sort((a,b) => a.id.localeCompare(b.id)), [...reordered.nodes].sort((a,b) => a.id.localeCompare(b.id)));
  assert.deepEqual({ nodes, edges }, original);
});
test('cycles and disconnected components preserve all links without a grid fallback', async () => {
  const graph = await layoutGraph(['a','b','c','isolated'].map(node), [edge('a','b'),edge('b','c'),edge('c','a')]);
  verifyGeometry(graph); assert.equal(graph.edges.length, 3);
});
test('owner IDs cannot collide with layout internal graph and port identities', async () => {
  const graph = await layoutGraph(['scene','scene:in','node-0'].map(node), [edge('scene','scene:in'),edge('scene:in','node-0')]);
  verifyGeometry(graph);
  assert.deepEqual(graph.nodes.map(n => n.id), ['scene','scene:in','node-0']);
});
test('bounded large graph and empty or invalid input', async () => {
  const nodes = Array.from({ length: 200 }, (_, i) => node('node' + i));
  const graph = await layoutGraph(nodes, nodes.slice(1).map((n,i) => edge(nodes[i]!.id,n.id)));
  verifyGeometry(graph); assert.equal(graph.nodes.length, 200);
  assert.deepEqual(await layoutGraph([], []), { nodes: [], edges: [] });
  await assert.rejects(layoutGraph([node('a')], [edge('a','missing')]));
  await assert.rejects(layoutGraph([node('a'),node('a')], []));
  await assert.rejects(layoutGraph([...nodes,node('extra')], []));
});
