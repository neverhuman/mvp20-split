# POP-01.07 retained node input inspection

Verified: 2026-10-15 13:19:44 America/Chicago. Owner-approved POP-01.07 exact boundary implemented in
Runtime0.70 with separate node_inputs0.1 contract. No migration or execution change.

GET /v1/graph-observations/{run}/nodes/{activation}/inputs requires scoped read AND
inspect_receipts. Original containing-scope values are summarized; prepared invocation
inputs/tool/checkpoint are exact when materialized. Unknown/scoped-away404, missing
grants403, malformed owner records503; no-store includes authorization/error responses.
One read-only repeatable-read owner transaction; no Data calls, writes or new ledger.
No live snapshot token; observed revision is correlation only. Null invocation is not
failure evidence. Successful-only producer proof remains unchanged.

-55 actual PostgreSQL graph inspection/navigation/producer checks pass, including
 9 new input cases for queued, successful, retryable/terminal failed, expired/revoked
 and skipped nodes, grants/scopes, exact producer agreement and read-only statements.
 Evidence: .test-results/pop01-closure-sql-b2b88360/pytest.log.
-55 combined contract/publication/boundary checks pass.750 published schemas retain
 every one of748 predecessor bytes. Nine contract tests also pass against independent
 installed wheels, outside source paths. Dependency guard passes.
-Independent Runtime wheel install: .test-results/pop01-input-runtime-install-20261015a.
 Forbidden Data/Planning/Search implementations absent.
-Actual HTTP seed/slice run, owner stop/replacement and identical retained observations
 pass: .test-results/pop01-input-runtime-http-20261015b/node-inputs-evidence.json.
 Fixture a completed eight numerical methods and input reads but its restart helper
 used the parent environment incorrectly; helper fixed, bounded restart rerun b passes.
 No production semantic repair. All fixture processes/containers removed; volumes retained.

Bounded drift audit: implementation matches approved observation boundary. No new
authority, mutable projection, input truncation, predecessor schema change or private
peer access. Collector must still combine graph terminal-state cuts with retained
inputs and existing accepted-producer evidence. Full collection, authored composition
and batch/cap matrix remain E2 gates; E2 stays25%.
