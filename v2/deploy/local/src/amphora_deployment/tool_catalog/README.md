# Tool catalog integration

Owner BP-09.03/B1.3b checkpoint3. Separate heartbeat credentials and durable delivery
primitives implemented; managed capacity observations and successful eligible
execution remain in progress. Design: [capability tool services](../../../../../docs/Architecture/Capabilities/Tool_Services.md).

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
or credentials. No periodic/background reporter or supervisor control is enabled.

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
