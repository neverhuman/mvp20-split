import { test } from 'node:test';
import assert from 'node:assert/strict';
import { NavigationModel } from '../../../src/page_models/navigation.js';
import { scopes, topology } from '../../fixtures/navigation.js';
import { snapshot } from '../../fixtures/observations.js';

test('production root policy opens actual topology; per-scope viewport survives refresh but not denial', async () => {
  let reads = 0;
  const model = new NavigationModel({ scopes: async () => scopes(), topology: async () => { reads++; return topology(); } });
  await model.observe(snapshot().snapshot, true, false, true);
  assert.equal(reads, 1); assert.equal(model.snapshot.topology?.page.nodes.length, 2);
  const scope = topology().graph_scope.scope_key;
  assert.equal(model.viewportFor(scope), undefined);
  model.setViewport({ x: 8, y: 12, zoom: 0.05 });
  await model.observe(snapshot().snapshot, false);
  await model.observe(snapshot().snapshot, true, false, true);
  assert.deepEqual(model.viewportFor(scope), { x: 8, y: 12, zoom: 0.05 });
  await model.observe(null, false, true, true);
  assert.equal(model.viewportFor(scope), undefined);
});
