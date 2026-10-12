import test from 'node:test';
import assert from 'node:assert/strict';
import {SuccessorClient} from '../../../src/transport/successor_launch/client.js';
import {LaunchFailure} from '../../../src/transport/launch/client.js';
import {successorCommand,successorReceipt} from '../../fixtures/successor_launch.js';
const signal=()=>new AbortController().signal;

test('only explicit intake posts original bytes; unknown receipt uses identity then known owner hash',async()=>{
  const command=successorCommand(),receipt=successorReceipt(command),calls:{url:string;options:RequestInit|undefined}[]=[];
  const client=new SuccessorClient((async(url,options)=>{calls.push({url:String(url),options});return Response.json(receipt);}) as typeof fetch);
  await client.submit(command,signal());await client.receipt(command,signal());await client.receipt(command,signal(),receipt);
  assert.deepEqual(calls.map(call=>[call.url,call.options?.method]),[
    ['/api/deployment/v1/campaign-successor-launches','POST'],['/api/deployment/v1/campaign-successor-launches/next','GET'],
    ['/api/deployment/v1/campaign-successor-launches/receipts/query','POST']]);
  assert.equal(calls[0]!.options?.body,command.body);assert.equal(calls[1]!.options?.body,undefined);
  assert.deepEqual(JSON.parse(calls[2]!.options?.body as string),command.query(receipt));
  for(const call of calls){assert.equal(call.options?.credentials,'same-origin');assert.equal(call.options?.redirect,'error');assert.equal(new Headers(call.options?.headers).has('Authorization'),false);}
});

test('denial, missing, conflicts and slot contention are closed without automatic retries',async()=>{
  for(const [status,reason,kind] of [[403,'private','denied'],[404,'private','missing'],[409,'launch_slot_busy','busy'],[409,'launch_request_conflict','conflict'],[500,'private','unavailable']] as const){
    let calls=0;const client=new SuccessorClient((async()=>{calls++;return Response.json({reason_code:reason},{status});}) as typeof fetch);
    await assert.rejects(client.receipt(successorCommand(),signal()),error=>error instanceof LaunchFailure&&error.kind===kind);
    assert.equal(calls,1);
  }
});

test('aborted and oversized replies cannot establish launch authority',async()=>{
  const controller=new AbortController();let calls=0;
  const client=new SuccessorClient((async()=>{calls++;controller.abort();return Response.json(successorReceipt());}) as typeof fetch);
  await assert.rejects(client.submit(successorCommand(),controller.signal));assert.equal(calls,1);
  await assert.rejects(new SuccessorClient((async()=>new Response(' '.repeat(262145))) as typeof fetch).receipt(successorCommand(),signal()));
});
