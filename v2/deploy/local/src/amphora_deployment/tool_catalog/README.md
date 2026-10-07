# Tool catalog integration

Deployment0.13 also recognizes the explicit synthetic-objectives-rebuilt worker
recipe for the same public capability. Catalog matching still requires the exact
configured image and deployment; a replacement cannot claim the old image's capacity.

Owner BP-09.03/B1.3b checkpoint3. Separate heartbeat credentials and durable delivery
primitives implemented; managed standby/capacity observations now have actual local
peer proof. Successful eligible execution remains in progress.
Design: [capability tool services](../../../../../docs/Architecture/Capabilities/Tool_Services.md).

Registry owns registration, immutable locks, activation, deployment definitions,
expiring replica observations and resolution. Deployment may report observed local
executor availability; it cannot grant eligibility, reserve graph work, admit a
campaign or turn descriptor registration into scientific validation.

provision_worker_credential explicitly creates tool-catalog.dpapi under the original
installation writer lease after authenticating the original deployment vault. Its
only reference is WORKER_REGISTRY_TOKEN, protected with current-user DPAPI and a
deployment-specific tool-catalog context. Repetition loads the same credential;
partial/corrupt/wrong-identity files fail closed. No silent replacement or rotation.
The original credential vault remains unchanged. Returned metadata contains the
reference name only. Provisioning does not configure a Registry grant or send calls.

The existing local owner binding loader may supply this credential only to Registry
when explicitly named in secret_references. Registry configuration must bind it to
a heartbeat-only worker principal and scoped deployment worker list. The scientific
tool containers continue receiving only Runtime/Artifact credentials. A future
reporter must preserve original heartbeat request/revision after uncertain delivery,
use stable logical replica IDs rather than allocating one for every Docker turn,
and withdraw/expire capacity when observations or authority are unavailable.

ReplicaBinding binds installation, scope, worker, deployment and stable replica.
HeartbeatJournal owns local-heartbeat-v1, a bounded8192byte atomically replaced and
fsynced file. Caller holds the installation writer lease and serializes each replica.
It persists the exact command before delivery, advances only from a validated
accepted Registry snapshot, and retains intent on rejection, malformed responses
or interrupted writes. Only0/1free slots and15second TTL are supported. Registry
owns observed/expiry times; accepting a historical receipt does not renew it.
No SQL or private service imports; Deployment remains standard-library-only.

prepare(ready=False) cannot replay an uncertain positive observation. It returns
None and retains the unresolved request, so callers must expose uncertainty and
allow any existing server lease to expire. Once freshly ready, retry the original
command before issuing another revision. Pending zero observations can always
replay. Never abandon intent, reset revisions or allocate replacement replica IDs
to bypass a lost response. Rejections remain latched until their cause is resolved.
The caller must establish fresh readiness immediately before positive delivery;
this primitive neither observes the worker nor grants dispatch authority.

HeartbeatTransport sends only to127.0.0.1 on a validated port, fixed Registry
heartbeat route, no proxy/redirects,2second socket timeout and bounded4096byte
request/8192byte response. The socket timeout is not an absolute request deadline.
Only the heartbeat credential is supplied; errors never include response content
or credentials. The optional managed reporter below owns periodic delivery.

Replacement must preserve the sidecar and journal identity, uncertain request,
known revision and original server expiry semantics. It must pass owned policy,
DPAPI and actual loopback transport tests plus installed Registry/SQL replay proof.
dev/verify_local_catalog_delivery.py exercises that peer with zero capacity,
the actual Linux seed image descriptor and heartbeat-only worker authentication.
It asserts lost-response replay identity, revision progression and exclusion from
eligible resolution. It does not claim worker availability or scientific execution.

Tests belong to deploy/local/tests/tool_catalog. Current-user DPAPI tests are actual
Windows credential evidence; they are not catalog/eligibility or scientific proof.

Focused verification:27 tests,135/135 statements and12/12 measured branches.
This coverage does not establish physical disk durability, a hard HTTP deadline,
fresh capacity sensing or background lifecycle behavior; those are distinct gates.

## Managed standby and reporting (Deployment0.8)

Scientific standby explicitly offers an idle executor without starting a run_once
container before Runtime admission. It is a separate state from quiescence; owner
shutdown requires quiescing standby first. Starting a tool consumes its idle slot.
Pending intent/created/starting/started/exited journals prevent positive capacity,
including while a controller is adopting a retained turn. Failure, closing and
quiescence withdraw the local offer. This never selects a graph activation.

Optional local-tool-catalog-v1 contains scope, worker_id and replicas for every
configured scientific slot; each entry pins deployment_id, replica_id and the
scientific configuration fingerprint. --catalog-manifest loads it under the same
installation writer lease. Reporters start only after control binds. No registration,
activation, campaign admission, credential creation or tool launch is implicit.

CapacityProbe verifies pinned configuration/certificate bytes, actual immutable
image platform/user/entrypoint and Docker daemon CPU/memory totals. ExecutorBudget
requires enough declared daemon resources for every configured2CPU/1GiB slot,
at mostfive. These totals are not exclusive free physical resources or reservations.
CatalogTarget reads the actual scoped Registry deployment using the controller's
existing operator credential on a fixed read-only route, and checks active state,
Linux/x86_64, worker list, capability and exact image binding. This credential never
enters heartbeat transport or scientific containers. Registry retains final policy
and lifecycle authority; observations may change immediately after inspection.

ToolDependencies verifies both local TLS handshakes with the pinned public CA and
host.docker.internal hostname, then probes /health and /ready on their exact configured
loopback upstreams. The tool proxy still permits only authenticated /v1 routes.
Runtime must report configured execution; this health check is not continuous Runtime
SQL readiness. Data must report readiness. HTTP bounds are socket inactivity timeouts,
not absolute deadlines. Any malformed/failed probe produces unavailable capacity.
The entire positive observation must be no older than5seconds from probe start;
slot/config state is checked again after I/O and immediately before positive delivery.

One background reporter serializes each replica every3seconds using the original
15second Registry lease protocol. Cached control status remains responsive during
Docker/HTTP I/O and exposes original observation/expiry or explicit uncertainty.
An observed historical receipt is not a new live lease. Initial disabled slots send
nothing; previously advertised slots send zero when no longer available. An uncertain
positive cannot replay while unready, including final shutdown: it remains explicit
uncertainty and any existing lease expires. Never claim immediate withdrawal in that
case. Stable replica journals survive profile/controller replacement.

Registry drain/force-stop first requests reporter shutdown and returns a drain guard
until background reporters finish their final withdrawal attempt. Registry restart
resumes the same replica/revision journal; scientific slots remain explicitly disabled.
Final supervisor shutdown also requires stopped reporters. Unexpected teardown joins
every owned reporter before closing worker monitors/TLS/owner jobs; join failure is
reported, never a successful drain. Hung/trickled local HTTP and full daemon/controller
outage remain named B3 scenarios, not covered by ordinary successful-capacity proof.

dev/verify_local_executor_capacity.py proves allfive tools are excluded before standby,
become candidates after actual checks and are excluded after zero-capacity withdrawal,
with zero container turns/admissions/model calls. dev/prepare_local_numeric_demo.py
extracts actual Linux descriptors/schemas and a reviewed synthetic graph; separate
immutable Runtime/Data/Registry configurations preserve the accepted serving baseline.
Runtime assigns run_id at admission; a demo must explicitly bind that returned ID in
new immutable worker configuration before launch, never predict it or mutate loaded
configuration. Full successful managed campaign execution remains the next proof.
