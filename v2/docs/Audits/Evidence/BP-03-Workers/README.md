# Independent Tool Evidence

Reviewed: `2026-09-28 16:50:53` (America/Chicago). B3/V1 passed.

- [Image manifest](images.json): actual Linux/amd64 manifest/config digests, offline wheel hashes, non-root network-disabled golden outputs and isolation.
- [Worker observations](workers-b3.json): nine actual independently installed Windows tool/SDK-to-owner scenarios, public HTTP receipts, exact artifact/run identities and interruption traces. Internal tool/SDK wheel bytes match the separately tested Linux images. Companion SHA-256 files protect exact evidence bytes.

No tokens, database credentials or private table reads are included. These are synthetic results, not scientific validity or target-host/Kubernetes proof. The initial live harness failed after interrupted upload because captured server stderr was never drained. Server logs now use files; repeating the same nine-case ladder passed. The focused driver avoids unrelated owner-suite reruns while debugging this harness.

- [Replacement observations](workers-v1.json): all nine recovery cases plus fresh numeric and sequence worker/SDK installations. Earlier owner receipts, completion records and result bytes remain equal before/after a new campaign through each replacement. Scope 34f1a759a9bc4af18b0f3e99b21d4a37. Same-release reinstall is .03 acceptance; new-release registry/replica cutover remains .04.
