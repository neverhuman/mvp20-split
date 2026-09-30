import { test } from "node:test";
import assert from "node:assert/strict";
import { ObservationClient } from "../../src/transport/observations.js";
import { artifact, completion } from "../fixtures/evidence.js";

test("evidence reads retain separate Runtime and Artifact routes and public validation", async () => {
  const paths: string[] = [];
  const client = new ObservationClient(async (path, options) => {
    paths.push(String(path)); assert.equal(new Headers(options?.headers).has("Authorization"), false);
    return new Response(JSON.stringify(String(path).startsWith("/api/artifacts") ? artifact() : completion()),
      { headers: { "content-type": "application/json" } });
  });
  const signal = new AbortController().signal;
  assert.equal((await client.completion("run/1", "completion/1", signal)).completion_id, "completion-1");
  assert.equal((await client.artifact("artifact/1", signal)).size_bytes, 17);
  assert.deepEqual(paths, ["/api/runtime/v1/runs/run%2F1/completions/completion%2F1?", "/api/artifacts/v1/artifacts/artifact%2F1?"]);
  assert.throws(() => new ObservationClient(fetch, "/\\foreign.invalid"));
  assert.throws(() => new ObservationClient(fetch, "/api/runtime", 1000, 2000, "https://foreign.invalid"));
});
