# Tool Replica Integration Acceptance

- Status: BP-03.04 complete; eight actual public-owner cases and scoped audit passed.
- Owner: cross-owner synthetic tool integration tests, not a production service or scheduler.
- Architecture: [Tool Services](../../../docs/Architecture/Capabilities/Tool_Services.md).

The harness installs Registry, Runtime, Artifacts and tools independently. Only public HTTP and public contract roots cross service boundaries. Test-only response barriers pause the real SDK after actual claim or finalization; owner state is neither synthesized nor edited. Runtime alone admits work and accepts fenced completion. Registry discovery/eligibility/heartbeat observations never grant an attempt.

`worker_process.py` wraps the installed public SDK transport and actual tool adapter. It receives only two worker tokens, no database credentials, private owner implementation or checkout imports. `wire.py` derives the documented canonical lock and is checked against independently preserved contract goldens. Controller setup uses ephemeral scopes and can cancel only its own active run; no database cleanup/reset is hidden here.

Run with the already migrated labeled PostgreSQL fixture and `AMPHORA_TEST_POSTGRES=1`: `dev/verify_tool_workers.py --images <actual-image-manifest> --replicas`. Windows wheel workers establish protocol/process compatibility with the same internal wheel hashes as separately tested Linux images. Registry deployment/resources describe that advertised Linux image profile; this harness does not attest running Linux containers or physical Linux capacity. Target-host/image-to-owner deployment is BP-09. No scientific or Kubernetes claim follows.

Evidence contains scoped immutable identities, receipts, state snapshots, hash-only request traces and image/package digests, never tokens or credentials. Partial failure evidence is retained. Fresh replacement and failure scenarios advance only through the owning canonical plan gates.

`run_tests.py --module tool-replicas` selects the small wire-fixture conformance tier only. Optional Python coverage uses the entire harness directory, so unexecuted process drivers remain visible. Actual independent process cases have named acceptance evidence rather than inferred source coverage. Run those sequentially because the initial Runtime profile admits one active campaign globally.

B1 actual scope f303014dbbc44baa870a8bf5c01095a7 passed on 2026-09-28 17:04:34: registry selection/admission, two distinct simultaneous claims, publication before acceptance and completion acknowledgement loss. Both results match independent goldens; budget reserves/spends each attempt once. [Preserved evidence](../../../docs/Audits/Evidence/BP-03-Replicas/README.md).

Add `--previous-images <prior-manifest>` for death/reclaim and new-release cutover. The driver verifies and installs the prior manifest's adjacent built-wheels bytes into a separate environment; it never rebuilds a prior identity from changed source. Five actual cases passed at 2026-09-28 17:12:18, scope cf1cde5566ec445b97829458da776604. Original receipts, output bytes and run snapshot remain unchanged after replacement; an old-release worker cannot claim the new run.

Final gate: add both `--previous-images <old-manifest>` and `--replacement`. Eight actual cases passed, scope 7f160a8548e2488d821103017b8fbc8d. Checkpoint schema version 1 is rejected by the undeclared checkpoint contract; unsupported version 2 is rejected at wire validation before receipt registration. Exhausted fixture budget prevents extra attempts; explicit controller cleanup does not claim a graph-supervisor terminal transition. [Closeout audit](../../../docs/Audits/BP-03.04_Replica_Closeout.md).

BP-04.02/V1 acceptance maintenance repaired transient Windows marker-file replacement conflicts in the test-only worker barrier. It retries the local marker replacement for at most two seconds without repeating the real owner request; permanent failures still exit. Four owned helper cases pass, and the installed graph gate passes with the repair. BP-03 remains closed; production SDK/tool bytes are unchanged.

BP-04.05/V1 acceptance maintenance handles the corresponding Windows reader-side sharing conflict: stage polling tolerates transient missing/denied marker reads within its existing20-second bound. It never reissues an owner request, hides malformed JSON or converts permanent failure into success. Seven helper cases pass; the complete installed observation acceptance rerun passed. BP-03 remains closed and production SDK/tool bytes are unchanged.
