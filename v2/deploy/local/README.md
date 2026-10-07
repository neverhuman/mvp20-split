# Local deployment profile and preflight

Owner: BP-09.01, package amphora-deployment0.1.0. B1.01 profile parsing passed33profile/boundary checks13.95s; no deployment readiness or target-host acceptance yet.
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
deployment policy remain pending; a parsed LAN address or durability claim cannot
authorize provisioning. Actual host identity/access is owner-supplied. Fixtures
use not-a-selected-host deliberately. Local tests live in tests/preflight and
must run independently of service databases, GPUs and provider keys.
