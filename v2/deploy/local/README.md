# Local deployment profile and preflight

Source0.17 begins the owner-approved UI-01.06 [campaign launch module](src/amphora_deployment/campaign_launch/README.md).
Strict public contracts, pinned profile/identity policy and a private transactional
launch journal are implemented and tested. Runtime retains admission/execution;
Deployment composes lifecycle only. Public launch HTTP, dynamic managed binding and
browser Run remain under implementation. No live viewer cutover is claimed here.

Source0.16 adds closed worker and catalog recipes for standalone Hansen solvency
and Arrhenius viscosity tools. Four actual Linux worker calculations were retained
by Runtime in UI-01.03, followed by clean owner/worker drains. Existing release
and immutable image pins remain required; no general arbitrary-process launcher.

Current package0.15.0; BP-09.03 closed. BP-09.04 adds strict offline backup inventory
and a separate reviewed rebuilt-evaluator recipe. Original worker profiles remain
unchanged. Cold restore owner/reference acceptance and rebuilt tool cutover passed.
Independent Deployment0.14 qualification and operational limitations are tracked in BP-09.04.
BP-09.05 adds the offline [acceptance ledger](src/amphora_deployment/acceptance/README.md);
Deployment0.15 passed391 independently installed tests and actual frozen evidence;
[operator smoke](OPERATIONS.md) verifies restored original/corrected/blocked history.
BP-09 is closed; unresolved worker failures remain LR-01 successor scope.

Historical BP-09.03 checkpoint, package amphora-deployment0.9.0. Native worker lifecycle is qualified; [worker boundary](src/amphora_deployment/workers/README.md). Managed TLS and responsive scientific container monitoring/adoption are independently qualified; [container boundary](src/amphora_deployment/scientific_workers/README.md). BP-09.01/.02 remain complete; full autonomous demo remains active BP-09.03 work.
The [tool catalog boundary](src/amphora_deployment/tool_catalog/README.md) adds separate heartbeat credentials and durable replay delivery; managed standby/readiness reporting has actual five-executor evidence; successful managed execution evidence belongs to BP-09.03.
Design: [Runtime topology](../../docs/Architecture/System/Runtime_Topology.md).

This package owns local versioned deployment configuration and subsequent
read-only host compatibility observations. Profile validation does not install software. Separate installation and persistence
modules own verified inventories and explicit local data-store provisioning. The package does not access
private service tables, implement owner migration SQL, provision clusters, spend model credits,
grant tool eligibility or operate campaigns. Module replacement preserves this
boundary and its named rejection reasons.

DeploymentProfile.from_bytes accepts at most65536bytes of strict JSON, rejects
duplicate/unknown keys, and constructs focused Target, Storage, Access, Provider
and ArtifactCompatibility objects. canonical_bytes produces a deterministic
profile; credential_names returns environment variable names only. No credential
values belong in a profile or report. Artifact compatibility compares declared
OS/architecture; matching declarations are not proof of installation or capacity.

Profile version1 contains profile_id, target, storage, access, provider and a
bounded list of immutable release/digest compatibility records. Target fixes
Python3.12 and declares CPU/memory/accelerator requirements. Storage requires an
absolute target-platform path and free-space minimum; unverified durability stays
explicit. Access declares literal bind address and authentication environment
reference. Remote providers require credential-free HTTPS endpoint, model name,
integer micro-dollar budget and synthetic-only/deny policy. Disabled provider
configuration contains no endpoint/model/key or allowance. No remote calls occur.

Parsing establishes shape, not permission or readiness. B1.02 observations and B2
deployment policy are implemented; a parsed LAN address or durability claim cannot
authorize provisioning. Actual host identity/access is owner-supplied. Fixtures
use not-a-selected-host deliberately. Local tests live in tests/preflight and
must run independently of service databases, GPUs and provider keys.

B1.02 verified 2026-10-06 20:03:49: HostObservation.inspect is read-only and binds profileSHA; detects OS/architecture/Python/CPU/memory, existing artifact directory/free space and optional bounded5second NVIDIA query. It does not infer durability, check exposure or contact providers. Foreign-platform paths are skipped; unavailable observations are null/named statuses, never fabricated zero.25tests0.62s and actual developerWindows observation passed. This is not selected-host acceptance. Coverage and platform gaps are in [probe evidence](../../docs/Audits/Evidence/BP-09-Deployment/Read_Only_Probes.json).

B2.01 verified 2026-10-06 20:05:33: assess returns named blockers for profileSHA/host mismatch, stale ornaive observation time, unknown/insufficient capacity, wrong artifact platform, absent storagepolicy, invalid exposure, missing environmentreferences andremoteallowance/egress denial. It never serializes credentialvalues orauthorizesinstallation.42tests0.61s;storage/network physicalverification remains actualtargetgate.

## CLI and replacement order

Run `python -m amphora_deployment validate --profile profile.json` for shape only,
or `preflight --profile profile.json` for actual local read-only observations and
policy. Exit0 means the named validation/preflight passed,2 means rejected input
or unavailable local probe,3 means blockers. No command installs or invokes a
provider. The report declares its limits and contains no credential values.

`replacement-order --admissions-paused --active-campaigns 0 --inflight-attempts 0
--pending-retentions 0` emits a declarative sequence only. Nonzero counts or
unpaused admission block it. These counts are explicitly operator-supplied, not
verified Runtime evidence. Stop workers/coordinators, drain owner deliveries,
then stop APIs and capture consistent backup. Restart storage/schema verification,
owner APIs, consumers, eligible workers and coordinators; admission comes last.
Actual automation, migration/backup and Runtime-cut validation belong to later
BP-09 installation/restore work. No hidden process control is implemented here.

B2 verified 2026-10-06 20:09:20:59profile/probe/policy/CLI/import-boundary checks17.14s,
then47owned malformed-input regressions4.41s. Profile/readiness/order branches are
fully covered. Observation75/82statements15/16branches has OS-failure gaps; CLI
37statements10branches runs in actual isolated subprocesses without parent coverage
attribution. Independent installation and selected-host profile acceptance subsequently passed.
Storage durability and network exposure have not been physically certified.

Verified 2026-10-06 21:39:19: owner selected this local computer and computer-only access. NativeWindowsx86_64/Python3.12 profile, localNTFS artifactroot, loopback127.0.0.1. Clean independent installation passes originalprofile/CLI parity, actual storage/socket/preflight rejection probes and47owned tests. [Closeout audit](../../docs/Audits/BP-09.01_Local_Profile_Closeout.md). Normal storage operation is not powerloss/backup certification; full service install and authenticated demo remain later children.

Current BP-09.02 boundary: [installation inventory](src/amphora_deployment/installation/README.md) adds six independently verified owner closures and explicit launch recipes in0.2. The original0.1profile format and qualified installation are preserved. Inventory is not service readiness; new persistence/credential/lifecycle/gateway work remains.

BP-09.02/B2.01 now invokes explicit installed owner migration CLIs with separate migrator credentials while all hosts are stopped. Six owners and the separate gateway pass actual loopback startup checks with serving credentials. Planning0.99 repairs migrator-role admission without schema changes. The infrastructure profile grants reads only; static health is liveness, not continuous database readiness. Dependency failure and graceful drain remain B2.02.

BP-09.02/B1.02 adds [protected credentials](src/amphora_deployment/credentials/README.md) and [dedicated persistence](src/amphora_deployment/persistence/README.md). Actual local role/authentication/resume checks passed via dev/verify_local_stores.py. Owner API lifecycle and gateway remain B1.03/B1.04.

BP-09.02/B1.03 adds [Windows lifecycle and control](src/amphora_deployment/lifecycle/README.md), authenticated loopback commands, fixed owner credential grants and bounded metadata logs. Actual isolated Registry failure/restart and supervisor shutdown passed;92deployment regressions passed. Gateway/Studio and successful six-owner startup remain B1.04/B2.

B2 complete: 138 deployment/gateway checks pass; coverage1283/1689 statements and156/260branches (combined73.83%). Installed CLI/SQL/Docker evidence is separate and not counted as parent-process coverage. Explicit migration/replacement success passed live; rare OS failures, repair interruption and portions of subprocess error reporting remain gaps for B3/V1. Evidence B2_Coverage.json and Local_Outage_Drain.json. Seven cooperative HTTP drains and original accepted receipt replay after PostgreSQL outage passed. Current package is independently requalified at V1; original0.1 qualification remains historical.

B3 selected-host matrix passed: independent Deployment0.2 wheel reproduced byte-for-byte across fresh installs; current seven-owner/host profile validates and passes actual native CPU preflight. Five owner startup CLIs reject correct migrator credentials (Planning0.99 actual serving rejection separately proven). Installed Data enforces an eight-byte local-storage quota, rejects excess, preserves finalized bytes/receipt, denies invalid auth/non-loopback access and drains. Installed Planning adapter handles actual loopback503/refusal without retry or invented zero usage. This uses test-only transport injection and no model calls. Physical disk failure, accelerator workloads and live-provider behavior are not claimed. B2 supplies actual database outage/recovery and retained receipt proof; V1 replacement/audit remain.

BP-09.03 adds [tool TLS access](src/amphora_deployment/tool_access/README.md): encrypted local
server identity and bounded fixed-owner forwarding for Linux tool SDK connections. Existing
profile/supervisor v1 stays unchanged. Managed TLS/worker configuration is the next integration
unit; transport probes alone do not grant tool eligibility or establish scientific execution.

Deployment0.10 adds bounded TLS admission pressure counters and sets the listener
default to its existing16-connection ceiling, accommodating five tool workers plus
five simultaneous readiness probes. See tool_access/README.md for concurrency, privacy
and replacement semantics. Historical expired tool attempts remain under diagnosis.

Deployment0.11 adds optional create-once Runtime-to-Registry credentials under
registry_access, enabling independently scoped draft eligibility configuration
without sharing Registry operator keys or replacing the original vault. Lifecycle
loads the sidecar only for an explicit reference in Runtime/Registry manifests.
Existing installations/manifests, package dependencies and state schemas are unchanged.

Deployment0.12 adds read-only [offline backup inventory contracts](src/amphora_deployment/backup_restore/README.md). Exact manifest/file digests, owner release/schema compatibility and separate target identity are verified; this is not restored-service readiness. Existing configuration/state formats unchanged. Actual capture/restore remains BP-09.04/B1.2 onward.

Deployment0.20.0 adds the closed planning-curation native recipe and policy-file
pins under UI-01.08j. Source implementation only until installed lifecycle and
actual local/LAN delivery pass; owner budget/dispatch contracts unchanged.
