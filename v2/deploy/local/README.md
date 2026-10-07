# Local deployment profile and preflight

Owner: BP-09.01, package amphora-deployment0.2.0. B1.01 profile parsing passed33profile/boundary checks13.95s; BP-09.01 local-profile acceptance is complete.
Design: [Runtime topology](../../docs/Architecture/System/Runtime_Topology.md).

This package owns local versioned deployment configuration and subsequent
read-only host compatibility observations. It does not install software, access
private service state, run migrations, provision clusters, spend model credits,
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
