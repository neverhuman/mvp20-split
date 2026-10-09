import { test } from "node:test";
import assert from "node:assert/strict";
import { LaunchClient, LaunchFailure } from "../../../src/transport/launch/client.js";
import { command, receipt } from "../../fixtures/launch.js";
const signal = () => new AbortController().signal;
test("only same-origin launch route receives exact bytes and browser cookies", async () => {
  const client = new LaunchClient((async (url, options) => {
    assert.equal(url, "/api/deployment/v1/campaign-launches"); assert.equal(options?.body, command().body);
    assert.equal(options?.credentials, "same-origin"); assert.equal(options?.redirect, "error");
    assert.equal(new Headers(options?.headers).has("Authorization"), false);
    return Response.json(receipt());
  }) as typeof fetch);
  assert.deepEqual(await client.submit(command(), signal()), receipt());
});
test("safe launch errors distinguish busy from identity collision without exposing raw text", async () => {
  for (const [status, code, kind] of [[409,"launch_slot_busy","busy"], [409,"launch_request_conflict","conflict"],
    [403,"anything","denied"], [404,"anything","missing"], [500,"private-path","unavailable"], [422,"anything","invalid_request"]] as const) {
    const client = new LaunchClient((async () => Response.json({ reason_code: code }, { status })) as typeof fetch);
    await assert.rejects(client.submit(command(), signal()), error => error instanceof LaunchFailure && error.kind === kind && !error.message.includes("private"));
  }
});
