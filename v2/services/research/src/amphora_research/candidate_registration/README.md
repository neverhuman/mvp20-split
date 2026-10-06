# Synthetic candidate registration

- Owner: Research0.35.0; BP-08.03/B1.03b.i, owned SQL/API verification passed.
- Design: [Candidate ingress](../../../../../docs/Architecture/Research/Candidates.md#synthetic-candidate-declaration-ingress).

This module registers the existing CandidateRevision as an authenticated synthetic declaration. It does not prove scientific validity, operator legality, synthesis feasibility, fitness or Runtime acceptance. It never imports scientific tool implementations. Reviewed CandidateProfile configurations pin exact published candidate-space schema bytes, kind and semantic profile; private domain objects validate complete encoding, source integrity and scope. Different tool profiles remain explicit configuration.

CandidateRegistrar authorizes declare_candidate and validates identity/scope/schema/media/size before peer I/O. A fresh public Data reader resolves exact metadata and bytes with current access for every write/retry, outside SQL. CandidateProfiles checks hash/length, duplicate-free bounded JSON, the correct model, synthetic authority and inner scope/kind/profile. A proposed-change Artifact is a representation wrapper; its source hash and move remain declared provenance, not independently proven execution.

IdentityLedger publishes immutable candidate bytes and immediate predecessor/head changes under the existing identity lock. New append-only candidate_registrations records original public actor/digest/preexisting flag/time in the same transaction. A failed metadata write rolls back identity/head; exact retry preserves first registration, changed bytes conflict. Public-origin metadata cannot retroactively identify the creator of a privately seeded record. research_0014 is forward-only and grants service SELECT/INSERT, never UPDATE/DELETE. Use Research0.35+ migrators once applied.

Read_candidate authorizes exact historical identity reads without fetching source contents. Later rights loss may deny a registration retry or Artifact read but cannot erase/change prior candidate history. Current Data access is observed before commit, not a distributed transaction or new retention guarantee. Correction adoption remains future-campaign-only.

Optional host candidates config contains data(endpoint,token_env) and profiles(schema,kind,semantic_profile). It enables POST /v1/candidates with declare_candidate. POST /v1/candidates/read uses CandidateRevisionRef and a separate read_candidate grant. No candidates config means write route absent; declare_candidate grant without configuration fails startup. Existing questions/needs and scientific routes remain separate. API uses existing JSON256KiB/5s/no-store/auth rules; safe conflict, policy, peer and SQL errors do not echo payloads/credentials.

Tests belong under tests/candidate_registration. Unit/schema policy, actual PostgreSQL/API, public Data/worker process handoff and independent replacement are separate tiers. Actual Data/worker process handoff and independent replacement are still pending. Rebuilds preserve exact history, first actor, read/write grants, current source-access checks and no-scientific-authority boundary.

Verified 2026-10-06 13:19:41:70 candidate/declaration-regression/boundary checks18.74s;141statements/36branches100% in the new module. PostgreSQL race/rollback/append-only grants, exact history, current denial, explicit hosting and separate access pass. Scripted Data peer proves owner behavior only; actual public Data/worker handoff remains B1.03b.ii. Existing schema bytes unchanged.
