import test from 'node:test';
import assert from 'node:assert/strict';
import {SuccessorSubmission} from '../../../src/transport/successor_launch/submission.js';
import {successorCommand,successorReceipt} from '../../fixtures/successor_launch.js';

test('original numeric-profile bytes preserve decimal strings without float conversion',()=>{
  for(const value of ['0','1','1.2500','100000000000000000000000','0.'+'0'.repeat(323)+'5','-0.000000000001234']){
    const command=successorCommand('next',value);
    assert.equal(SuccessorSubmission.restore(command.body).body,command.body);
    const input=command.request.payload.admission.payload.inputs[0]!.value;
    assert.equal(input.kind==='number'&&input.value,value);
  }
  assert.throws(()=>successorCommand('next','Infinity'),/invalid_successor_response/);
  assert.throws(()=>SuccessorSubmission.restore(successorCommand().body+' '),/original_bytes/);
});

test('successor request rejects wrong nested identity, duplicate carry and missing predecessor',()=>{
  for(const change of ['identity','carried','predecessor']){
    const request=successorCommand().request;
    if(change==='identity')request.payload.admission.identity.command_id='other';
    if(change==='carried')request.payload.admission.payload.carried.push(request.payload.admission.payload.carried[0]!);
    if(change==='predecessor')delete (request.payload.admission.payload as Partial<typeof request.payload.admission.payload>).predecessor;
    assert.throws(()=>SuccessorSubmission.restore(JSON.stringify(request)));
  }
});

test('receipt binds predecessor and profile and retains original owner hash across revisions',()=>{
  const command=successorCommand(),previous=successorReceipt(command);
  assert.deepEqual(command.query(previous),{identity:command.request.identity,request_sha256:previous.request_sha256});
  for(const field of ['predecessor','hash','revision','run','profile']){
    const next=structuredClone(previous);next.revision=1;
    if(field==='predecessor')next.predecessor.revision++;
    if(field==='hash')next.request_sha256='0'.repeat(64);
    if(field==='revision'){next.revision=0;next.phase='admission_unresolved';}
    if(field==='run')next.run_id='unproven';
    if(field==='profile')next.profile.sha256='0'.repeat(64);
    assert.throws(()=>command.verify(next,previous));
  }
});

test('accepted successor cannot become its predecessor or rewrite terminal admission',()=>{
  const command=successorCommand(),receipt=successorReceipt(command);
  receipt.revision=1;receipt.phase='engaged';receipt.run_id='child';
  receipt.admission={outcome:{status:'accepted',binding:{identity:command.request.payload.admission.identity,operation_id:'operation',request_sha256:'2'.repeat(64)},
    committed:{kind:'run',object_id:'child',revision:0}}};
  command.verify(receipt);
  const wrong=structuredClone(receipt);wrong.run_id='parent';if(wrong.admission!.outcome.status==='accepted')wrong.admission!.outcome.committed.object_id='parent';
  assert.throws(()=>command.verify(wrong),/run_mismatch/);
  const changed=structuredClone(receipt);changed.revision++;changed.admission!.outcome.binding.operation_id='another';
  assert.throws(()=>command.verify(changed,receipt),/admission_changed/);
});
