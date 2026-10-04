# Restore

## Current checkpoint

- Last refreshed: 2026-10-04 03:01:54 (America/Chicago).
- Latest pushed15ff22b; B3.01/.02 source/tests/docs verified ready to commit/push. Child66.67%,Build88.89%,Acceptance0%; parent13.33%,closed gates2/4 and2/20. B1/B2=100%,B3=66.67%,V1=0%. Current B3.03 abrupt process-death proof; next V1.01 independent final verification.
- Planning0.7 source unchanged/dev synced, contracts planning0.2,488 schemas. planning_0001..0004 immutable; <=0.6 migrators prohibited. Last independent .test-results/planning-orchestration-independent-20261004:156 tests,11 processes/two installs. B3 new tests have not yet been copied into those installations; final V1 does this.
- B3.01:13 added full-runner adversarial cases;24 orchestration tests5.11s, error propagation branches now covered; evidence Adversarial.json. B3.02:4 full-runner race cases;15 dispatch/race tests9.89s, evidence Races.json. No tests running. Source production unchanged. PostgreSQL actual; provider synthetic.
- B3.03 next create reusable installed process-crash harness/probe. Abrupt os._exit at five boundaries: after reservation before issuance; after issuance before provider; after provider mock call before observation; after observation before settlement; after settlement before return. Fresh installed replacement must never repeat same physical attempt and must retain conservative unknown charge. Use harmless per-attempt marker files for synthetic provider calls (exclusive create + explicit duplicate marker), not actual remote effects. Return exact request/output hashes, call ordinals and charges; no URL secrets. Graceful process exit proof already exists but is not abrupt-exit proof.
- Fixture secrets: .test-results/postgres-fixture.json only read via owned_state/planning_owner; URLs env-only, do not dump. Reuse .test-results/planning-orchestration-independent-20261004/initial or replacement/Scripts/python.exe. Package already at0004; no mutation/reset of fixtures. Source tests/conftest.py owns PG fixtures shared by persistence/orchestration.
- Persistence DispatchJournal issues once-only token and DB deadline, complete/recover lock same request, late output separate, max charge holds and overage gate. PlanningRunner retries immutable context until bounded stop; no SQL lock over calls. Provider deadline is not remote cancellation; no live provider, server or Runtime acceptance yet.
- Keep exact full tracker rows; mirrors66.67/88.89/13.33 asserted. Use PYTHONUTF8=1,COVERAGE_FILE under .test-results,short IDs,--tb=short. PostgreSQL suites serial. Continue after significant commit/push. No subagents; live model/egress/spend decisions only before real calls.

## Retained installations and fixtures

- Source/dev Data0.28.0, public representations0.3.0,466schemas (452 unchanged predecessors), artifact_0012. Data<=0.25 migrators must never touch0012. No reset/downgrade.
- Latest independent Data: .test-results/data-retrieval-closeout-20261003/environment/Scripts/python.exe. Manifest/constraints/build.log/results.xml/binding-gaps.xml/coverage-final.json alongside. pytest/httpx/pytest-cov installed.
- Actual suites: AMPHORA_TEST_POSTGRES=1, AMPHORA_TEST_QDRANT=1. Set AMPHORA_TEST_DATA_REPLACEMENT_PYTHON, AMPHORA_TEST_REPRESENTATION_PYTHON, AMPHORA_TEST_QDRANT_PYTHON, AMPHORA_TEST_QUERY_PYTHON, AMPHORA_TEST_RETRIEVAL_HTTP_PYTHON, AMPHORA_TEST_RETRIEVAL_PROCESS_PYTHON to latest isolated Data.
- Research child .test-results/research-views-http-20261003/environment/Scripts/python.exe, Research0.33/research0012; set AMPHORA_TEST_RESEARCH_PYTHON and AMPHORA_TEST_RESEARCH_REPLACEMENT_PYTHON. Knowledge source0.17.0; find latest independent install from owning closeout evidence before reuse.
- Previous independent Data0.28 .test-results/data-profile-migration-20261003 remains. Older0.27 used only for legacy descriptor comparison; do not use incompatible old migrators.
- Actual Qdrant1.19.1 primary/replacement running, separately owned retained volumes. .test-results/qdrant-fixture.json and qdrant-replacement-fixture.json contain keys: never dump. Read selected safe endpoint/container fields, never assume old ports. dev/qdrant_fixture.py validates labels/image/auth; no deletion/reset.
- Pinned image qdrant/qdrant@sha256:12364fe851b9f17356fc88189fc06d1b521262e04659ec7345975b00c9246a10. Backend SHA bbd62cf269057b3280ef7e29e8ca06dbdbf6e81f42bb69652e63fb1973327f83 endpoint/key independent. OpenAPI .test-results/qdrant-v1.19.1-openapi.json SHA eb3e5d71ba74e1d99124ca1a77d563bbfa47084f04a13ef9b197e339f5a4ce0a,520632bytes.

## Operating rules

- Workspace Z:\mvp20-split; active v2, v1 read-only. Git safe.directory=//DesktopNAS/Code/mvp20-split; main remote github.com/neverhumanbot/mvp20-split.git. User authorized significant commit/push and persistent work. No subagents unless explicitly requested; none active. No goal/skill active.
- PYTHONUTF8=1; dev/.venv/Scripts/python.exe; .venv/Scripts/uv.exe. pytest -c dev/pyproject.toml; --tb=short prevents environment-argument disclosure on process failures. Coverage under .test-results; separate dev file. Never overlap PG suites or restart Qdrant during another suite. Use .absolute(), not .resolve(), on mapped drive.
- Use rg --files, not recursive pathlib walks across ignored environments. Archival broad Markdown walk traversed ignored trees unnecessarily; now complete. Target unignored/tracked paths instead.
- Single user/single autonomous campaign, internal/demo, general engine with likely bio-available polymers. Human scientific edits and receipt corrections apply between campaigns; active pins/history immutable. Current rights remain operational gates. Weak/contradictory/unknown science stays useful; no global quality veto or scientific-validity claim.
- Canonical numeric trackers, histories/Restore, focused module rebuild contracts and scoped audits remain required. No routine milestone permission gate. Existing authorization covers bounded implementation/compatibility repair.
