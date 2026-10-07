import { test } from 'node:test';
import assert from 'node:assert/strict';
import { WorkspaceSelection } from '../../src/page_models/session/selection.js';

const scope = { tenant_id:'internal', project_id:'project' };
const pins = { graph:{ graph:{scope, graph_id:'domain'}, revision:1, sha256:'a'.repeat(64) }, experiment:null, observations:[] };
const link = (value: unknown) => '?explore=' + encodeURIComponent(JSON.stringify(value));

test('explicit immutable graph selection is separate from session authority', () => {
  const selection = new WorkspaceSelection(link(pins), scope);
  assert.equal(selection.phase, 'ready');
  assert.deepEqual(selection.pins, pins);
  assert.ok(Object.isFrozen(selection.pins?.graph?.graph.scope));
  assert.equal(new WorkspaceSelection('',scope).phase,'missing');
});

test('cross-scope, malformed, ambiguous and oversized selections never supply pins', () => {
  for (const search of [link({...pins,graph:{...pins.graph,graph:{...pins.graph.graph,scope:{...scope,project_id:'other'}}}}),
    link({...pins,graph:{...pins.graph,sha256:'bad'}}),link({...pins,extra:true}),link(null),
    '?explore=%7B',link(pins)+'&explore='+encodeURIComponent(JSON.stringify(pins)), '?explore='+'x'.repeat(8192),
    link({...pins,graph:null}),link({...pins,observations:[{}]}),link({...pins,observations:{}})]) {
    const selection = new WorkspaceSelection(search,scope);
    assert.equal(selection.phase,'invalid'); assert.equal(selection.pins,null);
  }
});
