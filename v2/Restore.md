# Restore

## Current checkpoint

- Last refreshed: 2026-10-04 02:43:09 (America/Chicago).
- Latest pushed8779abb; B2.02 verified ready to commit/push. Child41.67%,Build55.56%,Acceptance0%; parent8.33%,closed gates1/4 and1/20. B1=100%,B2=66.67%. Current B2.03 bounded outcome/dispatch fencing; next B3.01 adversarial proof.
- Planning0.6/dev synced; planning contracts0.2;488 schemas unchanged. planning_0001/0002/0003 immutable.65 scoped source3.89s;134 independent tests,8 processes,2 installs in .test-results/planning-settlements-independent-20261004.18 dev14.54s; scoped dev-config lint passes. No tests running. Settlements.json evidence.
- B2.02 BudgetCharge reserved_floor_v1 never refunds: component max(reserved, observed lower bound); unknown/partial usage still charged. Immutable SettlementJournal records exact hash/counts/time, actor/request checks and duplicate replay; any observed per-call overage blocks new reservation. Next attempt requires prior settlement. Old Planning<=0.5 migrators cannot touch0003.
- B2.03 next: durable once-only issuance before provider call, no lock during call, persisted DB-clock deadline and recovery to unknown; unchanged context/policy/budgets across retries. No public dispatch yet. Need handle late responses without overwriting committed observation or discarding truthful cost evidence. Suggested append-only late evidence plus aggregate max charge adjustment; any late overage stops future admission, cannot undo an already-issued call. Design before implementation. Runtime decision races remain BP-07.04.
- Exact full-row tracker updates only: canonical41.67/55.56/8.33 mirrors asserted. History has previous substring-replacement correction. No live provider/model, egress or spend selection; deterministic work unblocked. PostgreSQL suites serial, no reset/downgrade. PYTHONUTF8=1, short pytest IDs,--tb=short. Continue after commit/push, no subagents.

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
