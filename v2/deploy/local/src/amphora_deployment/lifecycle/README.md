# Local process lifecycle

Deployment0.17/UI-01.06 adds optional --launch-manifest composition under this same
lifetime writer lease. LaunchInstallation restores original admitted run bindings
before pending-container validation; operator templates alone cannot omit them.
The manifest owns scientific/catalog paths and cannot be combined with their older
CLI flags. LaunchHost runs bounded reconciliation off the control thread; status
reports only host running/draining/failed. Normal shutdown waits for reconciliation
to stop; forced teardown closes acceptance before original handle cleanup. No public
launch listener is enabled unless --launch-port is explicitly supplied. That port
uses a distinct DPAPI launch credential granted only to Gateway, never operator
control. The listener remains readable after coordinator failure and drains before
lease release. API/Gateway fixture checks pass; live activation remains L4.

BP-09.03 adds optional [native worker turns](../workers/README.md) under the same
supervisor writer lease. Worker quiescence gates owner drain/restart/force-stop
and normal shutdown. Existing manifests without workers preserve their status
shape. Optional managed TLS and [scientific monitors](../scientific_workers/README.md)
extend the same lifetime writer lease. Scientific adoption begins only after control
bind, blocks drain immediately on retained pending state, and performs Docker I/O off
the control thread. Normal stop order is both worker groups, TLS, then owner APIs.
Unexpected monitor detach leaves durable container state for recovery; it does not
claim Windows job closure killed a Linux container. Migration guards retain that
distinction after controller exit.

Owner BP-09.02/B1.03. ProcessJob owns an unnamed, noninherited
Windows job handle with kill-on-close. Only a live Popen handle can be attached;
stored process IDs are diagnostic metadata and are never termination authority.
Closing a job is a forced stop, not a graceful application drain. The
launcher gates application entry until job attachment succeeds. OwnerProcess
verifies inventory interpreter/manifest/wheel hashes before starting a reviewed
owner CLI. Only explicit AMPHORA_ environment entries and minimal Windows system
variables reach the child. It starts hidden with no shell and discards raw output.
An EOF at the entry gate exits before importing the owner. A running process is
not readiness; an exited CLI retains its actual exit code. Normal CLI failure
and job-forced termination are separate event types. No restart attachment by PID
is implemented. Supervisor holds fixed owner bindings and serializes commands.
Repeated start returns existing process state, including failure; it never retries
silently. Restart requires a stopped owner. Normal supervisor shutdown requires
every launched process to have exited. Explicit force-stop and supervisor death
do not claim graceful drain.

LifecycleEvents accepts only fixed event/owner names and numeric process results.
Raw child output, exception text, credentials and scientific payloads are not
accepted. One active and one previous JSONL file are retained, each bounded by
the configured limit. The owning supervisor must serialize writers across
processes; the class serializes threads. These diagnostic events are not durable
campaign history. Log failure must be surfaced by the caller, never silently
treated as successful deployment.

Tests belong to deploy/local/tests/lifecycle. Actual Windows tests verify job
closure and supervisor death terminate assigned children; application drain and
durable-work recovery remain B2. This is process ownership, not a sandbox against
malicious same-user code or administrators.

Windows ABI references: [job assignment](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject),
[extended limits](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information),
[job lifetime](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).

Routes persists eight distinct loopback endpoints after stores readiness, under the deployment operation lock. Probing reserves them only during allocation; any later port collision must fail startup and must never silently select a new route. Allocation is not service readiness. Read-only control discovery reads atomically replaced state without the writer lock, repairing a reproduced startup/status contention race.

## Commands and authority

`python -I -m amphora_deployment.lifecycle serve --root <installation> --manifest <bindings.json>`
hosts authenticated control on the persisted supervisor loopback route. It starts
no owner automatically. Launch this long-lived command hidden on Windows. The
same module provides `status`, `start --owner`, `restart --owner`, `force-stop --owner`
and `shutdown`, all with `--root`. Operators use these commands, not raw bearer keys.
Owner migrations belong to persistence/migrations; campaign admission is not owned here.
`drain --owner` requests cooperative HTTP shutdown through the private child pipe.
Exactly one interrupt is delivered; repeating drain does not send another. The owner
server finishes accepted requests and its own cleanup. Status separately reports
draining, drained, failed or timed_out after45seconds. Timeout leaves the process
alive; only explicit force-stop or supervisor death forces termination. This is the
deployed HTTP boundary, not autonomous worker/campaign drain; BP-09.03 must quiesce
its later workers before closing transports.

`readiness --root ... --manifest ...` makes bounded public HTTP and installed-owner
check-CLI observations. Static health alone cannot establish database readiness.
Checks run concurrently with selected serving credentials, suppressed raw output and
45second child deadlines. Results are point-in-time owner availability, distinct from
process status and scientific eligibility. Atomic journal snapshots allow reads while
the supervisor holds its writer lease. Serving URLs include connect_timeout=5,
including owners whose default engine omitted it.

The `local-supervisor-v1` manifest names a nonempty subset of reviewed owners. Each
entry has absolute installation, source_lock and configuration paths plus a list
of secret_references. Inventory hashes are checked again on launch. Only the
owner's service database role is assembled; migrator/admin credentials are never
granted. Additional token grants must name that owner or a peer edge involving it.
Data may receive Qdrant credentials; Runtime may receive the cursor key. Planning
configuration converts token_env principals to its existing environment-only
supervision credentials format. No configuration file contains resolved secrets.
Missing owners are not evidence of a complete six-service deployment.

Control uses a separate create-once current-user DPAPI sidecar, supervisor.dpapi,
bound to the installation identity. The original credential vault is unchanged.
The HTTP API accepts GET /status, POST /owners/{owner}/{start,restart,force-stop}
and POST /shutdown. Every request requires a bearer credential, accepts no body,
and cannot supply commands or configuration paths. Raw HTTP diagnostics are muted.

Verification: 29 focused lifecycle tests; actual installed Registry CLI failure,
repeat-start identity, explicit restart, force-stop and clean control shutdown via
dev/verify_supervisor_commands.py. Missing Registry configuration is intentional:
this is lifecycle/failure evidence, not six-owner serving readiness. Successful
owner startup/migrations and drain belong to B2; full demo remains later children.

B2.01 serving holds the deployment operation lease for the supervisor lifetime, excluding simultaneous provisioning/migrations. Read-only control still uses atomic snapshots. Actual supervisor command regression passed with this lease.

Deployment0.11 accepts the optional RUNTIME_REGISTRY_TOKEN reference only for its
two endpoint owners and resolves it from the deployment-bound registry_access
sidecar. No arbitrary extra credential file or cross-owner operator key is accepted.
Manifests lacking that reference never require the new sidecar.
