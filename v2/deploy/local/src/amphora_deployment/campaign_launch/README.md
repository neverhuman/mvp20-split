# Campaign launch lifecycle

UI-01.06 approved2026-10-09. L1/L2 complete; next bounded HTTP/Gateway/Studio delivery.
Verified2026-10-09 08:40:56:170 focused source checks;468 tests in an independent
Deployment0.17 wheel installation, plus actual coordinator process-death/receipt
recovery and three Docker monitor-death/adoption probes (intent/created/started).
Receipt authority in that probe is an HTTP fixture; actual campaign/browser proof
remains L4. No live Run endpoint or demo worker replacement enabled yet.

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
--launch-manifest; installed module/fault qualification passed, serving demo unchanged.

LaunchCoordinator performs one bounded step outside journal transactions. Its local
lock prevents overlapping ticks; the installation lifetime lease excludes competing
processes. Persist admission intent before HTTP; reconcile the original receipt before
resubmitting identical bytes. Public run observations must match scope/run/plan.
Partial worker failure retains admission and enters original-binding reconciliation.
Only Runtime terminal plus quiescent workers allows release. Invalid peer identities
latch recovery_required; unavailable peers preserve the phase and request identity.
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

LaunchJournal owns launches.sqlite3 under an operator-selected local Deployment
directory. BEGIN IMMEDIATE and a unique active-slot constraint serialize competing
requests; FULL synchronous commits precede external work. Read/transition callbacks
never perform peer I/O inside the transaction. Canonical request/receipt records
survive reopening and compare expected revisions. This is not a Runtime database.
Cold capture now checks every journal record is terminal before copying installation
state. A copied journal preserves request/receipt identity on reopen. Startup also checks
SQL index identity/revision/active-slot metadata against canonical receipts. Actual
installed backup/restore and retained binding configuration composition remain gates.

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
123 combined launch/Gateway/integration tests passed2026-10-09 08:54:00. Browser Run
integration and real campaign qualification remain L3/L4; serving demo is unchanged.
Profiles admit only installed adapters and immutable
image/resource pins. UI requests contain no host paths, commands or credentials.
Tests live under deploy/local/tests/campaign_launch by contracts/domain/journal/
transport/acceptance responsibility. Real browser/worker evidence is a separate gate.
