import { test } from 'node:test';
import assert from 'node:assert/strict';
import { workflowView, workflowLink } from '../../../src/page_models/session/workflow.js';

test('workflow route defaults safely and preserves exact owner selections without credentials', () => {
  assert.equal(workflowView(''), 'question');
  assert.equal(workflowView('view=knowledge'), 'knowledge');
  assert.equal(workflowView('view=domain'), 'domain');
  assert.equal(workflowView('view=design&view=execution'), 'question');
  assert.equal(workflowView('view=unsupported'), 'question');
  const link = workflowLink('launch=secret&feedback=%7B%22q%22%3A1%7D&explore=a&explore=b&quality_output=c&unknown=x', 'execution');
  const query = new URLSearchParams(link);
  assert.equal(query.has('launch'), false);
  assert.equal(query.has('unknown'), false);
  assert.equal(query.get('feedback'), '{"q":1}');
  assert.deepEqual(query.getAll('explore'), ['a','b']);
  assert.equal(query.get('quality_output'), 'c');
  assert.equal(workflowView(link), 'execution');
});

test('domain navigation retains exact graph selection and does not reinterpret historical results links', () => {
  const pins=JSON.stringify({graph:{graph:{scope:{tenant_id:'internal',project_id:'demo'},graph_id:'domain'},revision:1,sha256:'a'.repeat(64)},experiment:null,observations:[]});
  const initial=new URLSearchParams({view:'knowledge',explore:pins,launch:'one-use'}).toString();
  const domain=workflowLink(initial,'domain');
  assert.equal(workflowView(domain),'domain');
  assert.equal(new URLSearchParams(domain).get('explore'),pins);
  assert.equal(new URLSearchParams(domain).has('launch'),false);
  assert.equal(workflowView(workflowLink(domain,'knowledge')),'knowledge');
});
