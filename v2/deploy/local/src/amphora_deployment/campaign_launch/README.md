# Campaign launch lifecycle

UI-01.06 approved and qualified2026-10-09 10:19:00. Deployment0.18.3:502 independent
installed tests, four process/container probes, actual local/LAN browser launches,
same-request/run/container recovery with completed results and graceful drain pass.
See docs/Audits/UI-01.06_Launch_Integration.md for exact evidence and failed trials.
AdmissionCapacity offers healthy idle standby without turns/containers; reporters
must acknowledge fresh capacity before Runtime independently checks eligibility.
Rebinding withdraws standby and waits for reporter drain. RuntimePeer consumes
existing public graph-observation metadata for authored campaigns.
Unresolved admission rechecks readiness after restart before original-byte submission.
A verified pending operation is durably bound before resume; changed/disappearing
previously observed receipts latch recovery rather than risk another owner operation.
Installed process-death receipt probes use an HTTP fixture. The separate actual
campaign drill retains the original admission/container and verifies all five real
Runtime nodes succeeded after recovery. Synthetic science is not validated accuracy.

LaunchInstallation composes a closed local-campaign-launch-v1 operator manifest:
actor_id, launch_profile, scientific_manifest and catalog_manifest (absolute paths).
It checks profile tool coverage, original template fingerprints, worker scope and
catalog replicas. Per-request installation pins precede admission; resumed unresolved
admission requires those original pins. Startup restores generated run bindings before
checking outstanding scientific journals. Catalog reconstruction changes only worker
binding fingerprints, preserving logical deployment/replica identity.
LaunchHost uses the existing owner's operator peers and lifetime lease; local readiness
checks owner/TLS health, drained journals, native scope/config, images and resources.
No credentials enter manifests/receipts. This composition is opt-in via supervisor
--launch-manifest; --launch-port exposes the separately authenticated bounded API.

LaunchCoordinator performs one bounded step outside journal transactions. Its local
lock prevents overlapping ticks; the installation lifetime lease excludes competing
processes. Persist admission intent before HTTP; reconcile the original receipt before
resubmitting identical bytes. Public run observations must match scope/run/plan.
Partial worker failure retains admission and enters original-binding reconciliation.
Only Runtime terminal plus quiescent workers allows release. Invalid peer identities
latch recovery_required; unavailable peers preserve the phase and request identity.
An authenticated identical launch POST can explicitly request recovery of a known
accepted run. The coordinator requires the original admission receipt and matching
public scope/run/plan before resuming existing worker-binding checks on a later tick.
This step performs no admission POST or worker start; mismatches remain latched.
RuntimePeer uses fixed loopback routes, bounded bodies, no redirects/proxies and no
raw errors. LaunchPreflight reads exact Runtime draft/validation, Registry deployment/
release and Data artifact pins; local capacity checks remain installation composition.
Missing records reject preflight; authentication/malformed responses never imply absence.

ManagedLaunchWorkers composes existing Supervisor slots under its lock. Replacement
waits for native/scientific quiescence, stopped capacity reporters and reconciliation
of old journals; it never joins reporter network work under the control lock. Restart
adopts exact bindings; partial failure recovers original slots, and drain also waits for
catalog withdrawal and retained journal release. The catalog factory and lifetime lease
are supplied by installation composition; no separate root supervisor is created.

RunBindingStore derives immutable per-run configurations from installed templates,
preserving actor/scope/image/TLS and recording request/profile/run pins before worker
engagement. Reopening verifies exact retained bytes; it never starts containers or
edits templates. The installation lease owns file writes. Scientific journals remain
owned by scientific_workers; binding files contain no credentials.

Actual pending-container interruption exposed an owner-start race. Launch-owned
startup now retains pending turns without adoption; ManagedLaunchWorkers.prepare
waits for Runtime/Artifact/Registry processes and tool TLS before catalog changes
or adoption. This prevents recovery from starting tools against closed endpoints
or interrupting Registry startup with a catalog withdrawal still in flight.

LaunchJournal owns launches.sqlite3 under an operator-selected local Deployment
directory. BEGIN IMMEDIATE and a unique active-slot constraint serialize competing
requests; FULL synchronous commits precede external work. Read/transition callbacks
never perform peer I/O inside the transaction. Canonical request/receipt records
survive reopening and compare expected revisions. This is not a Runtime database.
Cold capture now checks every journal record is terminal before copying installation
state. A copied journal preserves request/receipt identity on reopen. Startup also checks
SQL index identity/revision/active-slot metadata against canonical receipts. Retained
binding composition and isolated journal copy/reopen checks pass. Full installation
backup/restore remains the existing Deployment runbook; this UI integration does not
claim a new full-root backup drill.

This module owns one local launch workflow and its private Deployment journal.
Runtime remains the sole admission/execution authority; Registry owns eligibility,
Data owns inputs/retentions, and Knowledge owns domain revisions. Public DTOs live
in amphora-contracts-campaign-launch. No peer SQL, private imports or browser shell.

LaunchIntent owns the canonical outer request and exact existing Runtime admission
bytes, fingerprint, profile selection and authenticated actor/scope comparison.
The same request ID must be used for both command families. Canonical replay cannot
change profile/input/draft identities. Receipt projection must distinguish unknown
admission, admitted-but-not-engaged, worker readiness, execution and drained release.
Never construct a success DTO at the call site to hide an unresolved operation.

One active slot spans the entire installation. Journal transitions must commit
before corresponding peer side effects and preserve the original admission identity
through retry/restart. A launch that was admitted keeps its run on worker failure.
Pending old scientific journals block replacement; no force deletion or new campaign
is allowed as recovery. Only rejected or safely released launches free the slot.

The public launcher uses --launch-port with --launch-manifest, a separate loopback
listener and DPAPI-protected LAUNCH_GATEWAY_TOKEN granted only to Gateway. It exposes
profile GET, launch POST and original-receipt GET, never operator control. Bodies are
bounded to262144bytes; actor/scope/profile are installation-fixed. Failures expose
only allowlisted reason codes. Coordinator failure stops new POST acceptance while
receipt GET remains available; shutdown drains both threads before lease release.
Gateway/launch integration checks and actual browser Run/reload/results are qualified
on localhost and the configured LAN listener. General input binding, multiple installed
profile selection and cluster deployment are outside this first UI boundary.
Profiles admit only installed adapters and immutable
image/resource pins. UI requests contain no host paths, commands or credentials.
Tests live under deploy/local/tests/campaign_launch by contracts/domain/journal/
transport/acceptance responsibility. Real browser/worker evidence is a separate gate.
