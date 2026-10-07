# Restore

Refreshed 2026-10-07 02:45:50 (America/Chicago). Read FIRST after compression.

## Active task

BP-09.03/B1.3b checkpoint3: actual catalog/tool eligibility and successful managed
execution. Native lifecycle and managed TLS/scientific adoption checkpoints complete.
B1.3b66.67%; child15.97%, Build21.30%, Acceptance0%; parent43.19%, (8+23/36)/20
verified delivery weight/eight closed gates. BP-09.01/.02 and BP-08 stay closed100%.
No owner decision blocker. Continue until genuinely needed, commit/push significant
verified updates. Local Windows x86_64/Python3.12, browser/owner listeners127.0.0.1 only.

All tests/builds/probes exited. No supervisor/owner/gateway/tool processes remain.
Dedicated local PostgreSQL/Qdrant and older dev fixtures remain running; never reset.
Latest pushed checkpoint:11634722 Deployment0.6. Deployment0.7 catalog delivery is
verified and awaiting commit/push if not yet in git log. Continue managed readiness.

## Latest verified Deployment0.7

Tool catalog module: separate create-once heartbeat credential tool-catalog.dpapi,
WORKER_REGISTRY_TOKEN explicitly available only to Registry owner. Original vault
unchanged. Actual installation sidecar IS NOW provisioned. Scoped heartbeat journals
under installation/tool-catalog/; all settled at revision2/free_slots0. No campaigns.
HeartbeatJournal local-heartbeat-v1 persists original request before send; original
revision/command/expiry retained after uncertain delivery. Positive pending request
cannot replay while unready (returns None/uncertain); pending zero may replay.
Transport fixed127.0.0.1 Registry route, no redirects/proxies, bounded response and
2sec SOCKET timeout (not absolute request deadline). No background reporter yet.

Independent .test-results/local-catalog-install-20261007b/owner:230copiedtests plus
actual installed Registry0.1/SQL replay, zero-capacity exclusion and public-wire
validation in separate Registry interpreter. Fresh c rebuild identical wheel.
Catalog_Delivery.json durable evidence. Focused27tests135/135statements12/12branches;
26credential/TLS checks,25Planninginput checks,four ownership checks. Named test
runner repaired: removed duplicate nested Planning scopes; use --module agent-planning
--area checkpoint_input|checkpoint_openai|checkpoint_budget. Deployment included in
ownership scan. Source/dev pins/locks/generated package inventory0.7 updated.
Source probe a had wrong /ready route; bpassed via authenticated/v1/releases. Initial
independent a TLSnegative test warned on Windowsconnectionreset; final bclean after
fixing expected test-side reset handling. No productionTLS weakening.

Next: explicit managed standby (no run_once before campaign admission), fresh pinned
image/config/daemon/resource/owner/TLS checks, stable replica reporting under writer
lease, withdrawal/expiry on quiesce/failure. Registry capacity is observation, NOT
reservation. Then actual successful eligible execution to close third B1.3b checkpoint.
Drivers verify_local_catalog_delivery.py, catalog_contract_probe.py (public contracts
in separate Registry interpreter), verify_catalog_installation.py. All completed,
no processes remain. Original stores/owner configurations untouched.

## Latest verified Deployment0.6

ScientificSlot background monitor keeps Docker I/O off control thread. Fixed five
synthetic tool recipes; one accepted turn per slot, repeat only exit0; fault latch,
explicit recover; quiesce stops new turns and waits current accepted create/start/work.
Startup marks original starting/started/exited journal active BEFORE observations,
then adopts inside the supervisor writer lease. No repeated ambiguous Docker start.
Unexpected controller cleanup detaches monitor; Docker can outlive Windows job death.
Pending journals block migrations even after control/API ports stop. A replacement
configuration cannot omit pending old bindings. Prepared intent/created also blocks
migration until reconciled. No ambiguous scientific force-stop/restart control.

Optional local-native-workers-v1, local-tool-access-v1, local-scientific-workers-v1
sidecars preserve original local-supervisor-v1. CLI --workers-manifest,
--tool-access-manifest, --scientific-manifest; commands use --worker, --tool-access,
--scientific-worker. Shutdown guard: both worker groups -> TLS -> owner APIs.
Source modules under deploy/local/src/amphora_deployment/{workers,tool_access,
scientific_workers}; README owns exact behavior and limitations. Source/locks/dev
pins/inventory0.6 updated. No migrations or accepted serving-manifest replacement.

Container journals: installation/scientific-workers/{profile}-{fullfingerprint}.json.
intent -> created -> starting (saved BEFORE sole Docker start) -> started -> exited
-> released. Exact full container ID + deployment/worker/binding/turn labels.
Lost create reuses same name; lost start observes original, never restarts it.
Only exact exited container is removed, without force/volumes. Configuration and
public certificate mounted read-only; no private key mount/raw Docker logs/env inspect.

Proof: .test-results/local-scientific-controller-20261007a/owner independently passed
199 copied Deployment tests plus actual Runtime0.65/Data0.30/TLS/Linux denied-claim
lifecycle and separate monitor-job-death/adoption. Fresh b rebuilt wheel matches a.
Scientific_Controller.json retains evidence. Final35 scoped tests1.88s,
411/444statements59/66branches91%. Docker success paths are separate actual evidence;
monitor thread-start/selected detach/aggregate-error paths remain coverage gaps.
Status latency <predeclared0.5s; rounded zero is below clock resolution, not zero time.

Actual controller probe uses nonexistent campaign: expected Linux tool exit3, API
drain409 before reconciliation, explicit fault recovery, TLS/API drain/exit0.
Monitor-death probe keeps parent TLS fixture available: kills ONLY owned Windows
monitor job, actual Linux container survives, replacement adopts SAME turn/container,
one upstream request, expected exit3, exact removal/released journal. This is not full
controller/TLS death or actual Docker-daemon outage; those remain distinct B3 cases.
No successful science, tool eligibility, admitted campaigns, keys or paid model calls.

Drivers: verify_managed_scientific_workers.py, verify_scientific_monitor_recovery.py,
verify_scientific_controller_installation.py. Physical NTFS bundles under local-v2/
scientific-controller-20261007a/{managed,recovery}; managed/tls identity bound to actual
deployment. Accepted installation now has TWO released scientific binding journals;
stores.json and original credentials.dpapi unchanged. Probe-private root journals are
separate. All test containers removed without volumes and all threads/processes exited.

Earlier immutable proof: Deployment0.5 c189tests + actual lost-create/lost-start cases,
fresh d wheel match (.test-results/local-scientific-install-20261007{c,d}/owner);
Scientific_Turns.json. Deployment0.4 a/b164tests + actual Runtime/Planning empty sweeps;
Native_Workers.json. TLS0.3 b126tests + actual Linux SDK trust/untrusted/plain-HTTP cases;
Tool_TLS.json. Earlier source/regression histories are in BP-09.03 History.md.

## Eligibility boundary findings

Registry0.1 owns exact scoped releases, activation, deployments, worker-authenticated
replica heartbeat and resolve. Read HOSTING.md and catalog/README.md, then targeted
hosting.py/catalog/replicas.py. Registry resource profile describes selected execution
environment; actual scientific images are Linux/amd64, not native Windows. Do not
relabel descriptors or relax SDK HTTPS restrictions. Existing accepted Registry profile
is Windows/read-only (one dormant fixture); use a new explicit scientific configuration.

Registry heartbeat worker must be in deployment.workers and heartbeat-only. Separate
sidecar is now provisioned/qualified above; original vault is preserved. No periodic
reporter or managed availability grant yet. Explicit synthetic Registry configuration
used only in proof, baseline read-only serving manifest unchanged.

Replica IDs must be stable logical worker slots, not new Docker IDs every turn:
Registry caps64 retained replicas/deployment and64 deployments/release. Derive any
capacity heartbeat from actual verified image/config/daemon/slot availability; do
not manufacture readiness from a successful registration or source test. Resolve is
an expiring candidate, not reservation/execution authority. Runtime owns claims.

Watch bootstrap ordering: starting run_once worker before Runtime admission attempts
unknown run and correctly exits3. Eligibility needs honest verified standby capacity
before admission, then start configured workers. Work out this composition explicitly;
no new scheduling authority in Deployment. Heartbeat delivery primitive implemented; managed readiness/reporting next.
After B1.3b successful eligible managed work, B1.3c actual Research/Data/Knowledge records;
then B1.4 live-model/browser/API trace. B2/B3/V1 still required. Studio Monitor default;
Design/Explore integration and actual trace remain. See child tracker/activation audit.

## Planning/model checkpoint

Planning0.101 independently qualified (.test-results/local-planning-checkpoint-20261007b/owner).
Exact checkpoint envelope and fitv2; fixture/evaluation profiles unchanged. Model
 gpt-5.4-mini-2026-03-17, pinned checkpoint profile SHA
3a80e73a4be13c0681f1f87e56c672b7ac0ce623a8456b1b1f92c892b640d9d5.
Provider openai_checkpoint_v1 requires explicit AMPHORA_OPENAI_API_KEY + synthetic-only
egress; default disabled. Dedicated project scope <=6 reservations/USD0.50 using existing
journals/schema0020, <=65536 conservative input units/2048 output/one attempt; full six
reservations=$0.350208. Original deadline/fresh Data authorization/history-first replay.
No key read/copied and no paid calls in this continuation. User authorized OpenAI keys
from Z:/ssos/.env later; never print them. Model/pricing official docs verified earlier;
openai-docs skill already read/applied. Do not change model casually or restart evaluation
profiles. Actual accepted serving manifest still Planning0.99 (0.101 used in scoped proof).

## Installation and immutable baselines

Logical root LOCALAPPDATA/Amphora/local-v2/installation. StorePython redirects physically:
C:/Users/alb_p/AppData/Local/Packages/PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0/
LocalCache/Local/Amphora/local-v2/installation. PowerShell/Docker need physical path;
selected Python logical path works. Identity7be3465bdf1e4fa6b9189637e51e6f96.
PG127.0.0.1:60687,Qdrant127.0.0.1:60688. DBamphora_local,12roles,six owner schemas.
Old Docker -dynamic-baseline containers STOPPED; NEVER start alongside replacements
on same volumes. No data resets, no global Docker settings/trust changes.

Original owner installs .test-results/local-owner-inventory-20261006a/owners:
Runtime0.65,Data0.30,Registry0.1,Research0.40,Knowledge0.18,Planning0.98 migrator baseline.
Serving Planning0.99 .test-results/local-planning-role-20261006a;
gateway0.2 .test-results/local-gateway-drain-20261006a; Studio0.9 dist/local.
Original migrations accepted; heads Runtime0028,Planning0020,Data0012,Research0016.
Migration wrapper rejects changed installation manifests without forward plan; don't
casually rerun migrations/new wheels. Baseline configs installation/configurations/
readonly-drain-20261006a/manifest.json; outage-receipt-20261006a preserves dormant Registry
receipt; capacity fixture retained. New probes create separate immutable configs.

Exact scientific images, Linux/amd64,user65532:65532:
evolution0.5 sha256:7538bece7dceb2f6c395890abbc632fe58e188ba5120ef2d6ef070267809e878
objectives0.3 sha256:b6d73b31058d358a5a2a13e44979e8b6e3a6acd06260670226a1b2570f1135e3
Old TLS proof identity local-v2/tls-proof-20261007b uses encrypted key/DPAPI; public cert
only may be container mounted. Certificates30days; no silent regeneration/rotation.

## Operating rules

Read v2/AGENTS.md. Continue until genuinely needed; milestones/push/context aren't stops.
v1 read-only; no JARVIS/subagents/goals. PYTHONUTF8=1 each exec. Python v2/dev/.venv/
Scripts/python.exe; uv v2/.venv/Scripts/uv.exe; PYTHONPATH Z:/mvp20-split/v2/dev.
pytest -c v2/dev/pyproject.toml --import-mode=importlib. Actual dev SQL opt-in
AMPHORA_TEST_POSTGRES=1; never reset fixtures. Keep tests/module READMEs/scopes aligned.
NO source/test/dev/README edits while ANY verification/build/probe runs; wait actual exit.
Docs trackers/Restore may update during checks. .absolute(), not .resolve(); no broad
NAS venv scans or tests/__init__.py. rg directories + --glob '*.py'; list before guessing
filenames. Large pytest input cases need explicit short IDs. Use Get-Date/local timestamps.
Git -c safe.directory=//DesktopNAS/Code/mvp20-split; add/diff core.safecrlf=false; main.
Preserve unrelated KAP processes (historically18720/2912); never blanket-kill Python/Docker.
UI guidelines read earlier; reconsult before UI edits. Keep frequent concise commentary.
