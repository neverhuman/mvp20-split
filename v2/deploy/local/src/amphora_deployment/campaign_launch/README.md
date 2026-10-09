# Campaign launch lifecycle

UI-01.06 approved2026-10-09. Contract, journal, reconciliation coordinator and public
Runtime transport implemented;54 scoped checks pass. Next gate: managed worker
integration/public preflight, backup and installed recovery, then bounded HTTP/UI.
No live Run endpoint or worker binding replacement is available yet.

LaunchCoordinator performs one bounded step outside journal transactions. Its local
lock prevents overlapping ticks; the installation lifetime lease excludes competing
processes. Persist admission intent before HTTP; reconcile the original receipt before
resubmitting identical bytes. Public run observations must match scope/run/plan.
Partial worker failure retains admission and enters original-binding reconciliation.
Only Runtime terminal plus quiescent workers allows release. Invalid peer identities
latch recovery_required; unavailable peers preserve the phase and request identity.
RuntimePeer uses fixed loopback routes, bounded bodies, no redirects/proxies and no
raw errors. Preflight/Workers ports still need production integration.

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
Quiesced backup/restore of this new owned file must be integrated before live release.

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

The public launcher will use a separate loopback listener and scoped credential,
not expose operator control. Profiles admit only installed adapters and immutable
image/resource pins. UI requests contain no host paths, commands or credentials.
Tests live under deploy/local/tests/campaign_launch by contracts/domain/journal/
transport/acceptance responsibility. Real browser/worker evidence is a separate gate.
