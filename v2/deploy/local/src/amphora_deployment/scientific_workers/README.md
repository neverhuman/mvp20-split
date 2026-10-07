# Scientific container lifecycle

Owner BP-09.03/B1.3b, Deployment0.6. Closed tool profiles, exact Docker observations,
current-turn intent, background monitoring and restart adoption implemented.
Actual local controller/Runtime/Data/TLS/Linux claim-denial and separate monitor
process-death/adoption probes passed; independent0.6 qualification passed199tests and both integration probes; fresh rebuilt wheel matches.
No successful scientific execution or tool eligibility claim.

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

ScientificSlot runs Docker work in one background monitor per closed binding.
Control status is cached; a blocked Docker observation cannot hold the control lock.
Quiescence stops accepting new turns and waits for the current accepted turn,
including its create/start operations. Only exit0 permits repetition after one
second. Failures latch; explicit recovery observes the original pending turn or
allows the same prepared intent to continue on a later start. It never restarts
an ambiguously started container. Fault recovery and enabling new work are separate.

Startup marks retained starting/started/exited turns active before network calls,
then adopts them inside the supervisor's writer lease. API/TLS shutdown requires
both native and scientific quiescence. Unexpected controller cleanup detaches its
bounded monitors; containers can outlive Windows job closure. Their durable journals
block owner migrations even when controller/API ports are stopped. A composition
cannot omit a pending old binding. Released journals permit between-campaign new
configuration identities; the active directory supports at most256 retained bindings.
Prepared intent/created journals also block migrations until reconciled, even when
no tool has started. No automatic deletion or reinterpretation repairs that state.

Optional `--scientific-manifest` selects local-scientific-workers-v1, a map from
closed names to image_id/configuration/certificate. It requires both managed TLS
routes and the matching public certificate. Existing scoped vault WORKER_RUNTIME_TOKEN
and WORKER_ARTIFACT_TOKEN grants become the two fixed SDK environment references.
POST /scientific-workers/{name}/{start,quiesce,recover}, or the same lifecycle CLI
actions with --scientific-worker, accept no arbitrary commands or payloads. The
scientific group starts no campaign and grants no eligibility. Initial control does
not offer ambiguous Docker force-stop/restart semantics.

Never remove scientific records, data volumes or unrelated containers. Full
controller/TLS death, actual shared-daemon outage and successful eligible work are
distinct remaining scenario gates; do not infer them from monitor-death proof.

Tests are owned by deploy/local/tests/scientific_workers. Journal/profile/transition
tests are pure checks; dev/verify_scientific_container_turns.py separately uses the
actual Linux evolution image and TLS. Its synthetic503 response deliberately yields
tool exit3; it verifies ownership/recovery, not successful science or owner eligibility.

Earlier Deployment0.5 focused coverage:28tests2.43s,328/360statements43/48branches90% across scientific
workers and managed TLS. Journal/profile paths100%; Docker success paths are actual
probe evidence outside that pure coverage run. TLS thread-start/serve-error cleanup
and some alternate states remain coverage gaps. No full-coverage claim.

Deployment0.6 scoped coverage:35tests1.88s,411/444statements59/66branches91%.
Monitor thread-start/selected closing-detach/aggregate-error paths remain gaps;
actual Docker success and process-death adoption are separate installed evidence.
