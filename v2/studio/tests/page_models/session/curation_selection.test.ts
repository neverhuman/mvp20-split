import test from 'node:test';
import assert from 'node:assert/strict';
import { WorkspaceCurationSelection } from '../../../src/page_models/session/curation_selection.js';
import { workflowLink, workflowView } from '../../../src/page_models/session/workflow.js';
const context = { actor_id:'owner', scope:{tenant_id:'tenant',project_id:'project'},run_id:'run',synthetic:true };
const id = 'curation-'+'a'.repeat(64);
test('curation navigation uses authenticated scope and preserves ambiguous hints for rejection',()=>{
  const source='curation='+id+'&actor=other&ticket=secret&view=curation';
  const link=workflowLink(source,'design');
  assert.equal(link.includes('secret'),false); assert.equal(link.includes('actor'),false);
  const chosen=new WorkspaceCurationSelection(link,context);
  assert.equal(chosen.phase,'ready'); assert.deepEqual(chosen.selection,{reference:{scope:context.scope,curation_id:id},actor:'owner',predecessor:'run'});
  assert.equal(workflowView(source),'curation');
  assert.equal(new WorkspaceCurationSelection(workflowLink(source+'&curation='+id,'curation'),context).phase,'invalid');
});
test('missing malformed and oversized selections never select a record',()=>{
  assert.equal(new WorkspaceCurationSelection('',context).phase,'missing');
  for(const value of ['curation=', 'curation=../other','curation='+id+'x','x'.repeat(16385)]) {
    const selected=new WorkspaceCurationSelection(value,context);
    assert.equal(selected.phase,'invalid'); assert.equal(selected.selection,null);
  }
});
