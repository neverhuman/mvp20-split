# Scientific container lifecycle

Owner BP-09.03/B1.3b, Deployment0.5. Closed tool profiles, exact Docker observations,
current-turn intent and lost-reply reconciliation implemented. Actual Linux image
probes pass for lost create/start replies through managed TLS and a synthetic
unavailable upstream. Independent c Deployment0.5 qualification passed189tests and both actual-container cases; fresh d rebuilt wheel matches c. No scientific eligibility
or responsive supervisor/container integration claim.

Deployment owns the reviewed container's lifetime. Runtime owns claims, eligibility,
leases, fences, completion and recovery of scientific execution; Artifact owns
durable output. Deployment must not choose graph nodes, rewrite tool applicability,
accept scientific results or infer successful work from a container exit code.

The current-turn journal is a metadata-only atomic replace with file flush/fsync,
under the existing installation writer lease. It binds deployment, worker, immutable
configuration fingerprint, unique turn, sequence and exact full Docker ID. States
are intent -> created -> starting -> started -> exited -> released. Starting is
durable before the sole start request. Starting/started recovery observes the
original container and never invokes start again: Docker start on an exited
container would repeat the tool. Unknown observations cannot authorize a new turn.
Only an observed exit, identity-checked ephemeral container removal and released
record permit the next intent. A lost create response reuses the original name;
it must not allocate a different turn/container identity.

No raw inspect, environments, private keys, scientific payloads or stored PIDs
belong in this journal. It keeps the most recent turn only; authoritative execution
history remains in Runtime/Artifact. A changed binding requires explicit stopped
composition replacement, not reinterpretation of an outstanding turn.

Closed evolution seed/requests/collect/vary and synthetic-objective recipes pin
image, SDK configuration and public certificate bytes. SDK tokens are fixed environment
references; command arguments contain no resolved credentials. Containers use exact
image IDs, Linux/amd64/nonroot reviewed entrypoints, read-only root/mounts, no restart,
no capabilities, no new privileges, 2CPU/1GiB/128PID limits and disabled raw logs.
This bridge profile enables owner control calls; it is not an egress sandbox.
Five-second Docker calls read only allowlisted image/container metadata. Daemon errors
cannot be mistaken for an absent container. ContainerTurn reuses the original named
created container after lost create replies and never repeats a starting/started
request. Removal requires the exact observed exited identity/code, without force or
volumes. The synchronous primitive must not be called on the live control thread.

Remaining implementation: responsive control while Docker is
unavailable; startup adoption of existing work before permitting API/TLS drain;
actual-engine interruption/recovery probes. Containers can outlive a controller;
Windows job closure is not a claim that a Docker workload stopped. Never remove
scientific records, data volumes or unrelated containers during lifecycle cleanup.

Tests are owned by deploy/local/tests/scientific_workers. Journal/profile/transition
tests are pure checks; dev/verify_scientific_container_turns.py separately uses the
actual Linux evolution image and TLS. Its synthetic503 response deliberately yields
tool exit3; it verifies ownership/recovery, not successful science or owner eligibility.

Final focused coverage:28tests2.43s,328/360statements43/48branches90% across scientific
workers and managed TLS. Journal/profile paths100%; Docker success paths are actual
probe evidence outside that pure coverage run. TLS thread-start/serve-error cleanup
and some alternate states remain coverage gaps. No full-coverage claim.
