# Scientific container lifecycle

Owner BP-09.03/B1.3b, Deployment0.6. Closed tool profiles, exact Docker observations,
current-turn intent, background monitoring and restart adoption implemented.
Actual local controller/Runtime/Data/TLS/Linux claim-denial and separate monitor
process-death/adoption probes passed; independent0.6 qualification passed199tests and both integration probes; fresh rebuilt wheel matches.
No successful scientific execution or tool eligibility claim.

Deployment0.8 adds explicit standby and resource observations for the
[catalog reporter](../tool_catalog/README.md). Standby starts no container and must
quiesce before owner drain. offers_capacity is local intent only; actual pinned image,
daemon, catalog target and dependency checks belong to that reporter. Both running
work and faulted/pending turns exclude capacity. Docker resources exposes only
Linux/x86_64 CPU/memory totals, not free/exclusive capacity. Original start-once
container journal and recovery semantics are unchanged.

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
POST /scientific-workers/{name}/{start,standby,quiesce,recover}, or the same lifecycle CLI
actions with --scientific-worker, accept no arbitrary commands or payloads. The
scientific group starts no campaign and grants no eligibility. Initial control does
not offer ambiguous Docker force-stop/restart semantics.

Never remove scientific records, data volumes or unrelated containers. Actual controller/API/TLS job death and original-turn adoption are now separately
qualified in BP-09.03/B3; managed eligible scientific execution is qualified in B1.
Shared-daemon outage is separately qualified by the owner-approved BP-09.03/B3 drill. Do not infer
continued campaign success from process recovery: the fault probe preserved a blocked
run after an unclaimed seed exceeded its original deadline. No automatic deadline
extension, turn replacement or campaign reset is performed.

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

BP-09.03/B3 verification:65 scoped scientific-worker/TLS tests pass19.74s. Actual
installed Deployment0.11 supervisor job death removes seven control/owner listeners
and both TLS listeners; same started Linux turn/container/sequence is adopted and
released in48.265s, exact original admission receipt retained. The scientific baseline
oracle did not pass after that interruption; public readback shows seed tool_failed,
zero attempts/completions/spend. This is process recovery and truthful failure evidence,
not resumed scientific success. Shared daemon, full-load peak resources and historical
expiry causality are not established by this probe. See Controller_Recovery.json.

Shared_Daemon.json qualifies actual Docker unavailability, retained intent, same-turn single-container recovery through installed Deployment0.11 and synthetic503 TLS owner, and exact original baseline restoration. Post-outage actual campaign/receipt/artifact and corrected-successor browser reads pass. No active campaign ran during the daemon outage; no resumed-science, HA or power-loss guarantee follows.
