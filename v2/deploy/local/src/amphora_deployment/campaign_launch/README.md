# Campaign launch lifecycle

UI-01.06 approved2026-10-09. Contract/profile foundation and transactional journal
implemented;25 scoped contract/domain/journal tests pass. No live Run endpoint or
worker binding replacement is available yet. Next gate: public-peer coordinator,
managed local worker adapter and complete fault/recovery matrix, then bounded HTTP.

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
