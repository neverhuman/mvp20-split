# Independent Tool Evidence

Reviewed: `2026-09-28 16:47:03` (America/Chicago). B3 passed; V1 replacement remains pending.

- [Image manifest](images.json): actual Linux/amd64 manifest/config digests, offline wheel hashes, non-root network-disabled golden outputs and isolation.
- [Worker observations](workers-b3.json): nine actual independently installed Windows tool/SDK-to-owner scenarios, public HTTP receipts, exact artifact/run identities and interruption traces. Internal tool/SDK wheel bytes match the separately tested Linux images. Companion SHA-256 files protect exact evidence bytes.

No tokens, database credentials or private table reads are included. These are synthetic results, not scientific validity or target-host/Kubernetes proof. The initial live harness failed after interrupted upload because captured server stderr was never drained. Server logs now use files; repeating the same nine-case ladder passed. The focused driver avoids unrelated owner-suite reruns while debugging this harness.
