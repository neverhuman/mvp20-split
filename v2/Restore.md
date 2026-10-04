# Restore

## Resume here

- Refreshed 2026-10-04 09:45:34 (America/Chicago). **Read this file first after compression**, as the owner explicitly requested. This was done at the previous compression.
- Continue authorized work across milestones, commits, pushes and compression. Do not stop merely to report completion of a checkpoint. No subagents, no JARVIS access, and no v1 edits.
- **BP-07.02/B2.02c.ii is verified complete. Current task: B2.03a.ii Research declaration registration.** Next: B2.03b Planning publication and owner handoff.
- Verified B2.02 checkpoint committed/pushed as **6ee28ddc**. New verified work is B2.03a.i Knowledge processing authorization, ready for commit/push; no Research declaration implementation yet. Continue without another permission request.
- Canonical child, parent, MBT and history are updated. Child43.06%, Build57.41%, Acceptance0%,1/4 deliveries closed. B1=100%, B2=72.22% (.01/.02=100%, .03=16.67%), B3/V1=0%. Parent28.61%,5/20 closed; P1=100%, P2=43.06%, remaining phases0%. MBT has25 recent rows.

## Latest verified Knowledge checkpoint

- B2.03a.i complete: Knowledge0.18 now uses `/processing-content` for all new validation, reasoning and publication review, with no ordinary-read fallback. Terminal decisions and accepted-log rebuild remain historical. No public schema or migration change. Knowledge/dev versions and locks are updated.
- Focused validation42 passed10.60s. Scoped transport24 passed6.61s; peers.py23/24 statements,1/2 branches (unchanged oversized-Artifact guard not exercised). Ruff, dependency boundaries and506-schema check passed.
- `.test-results/knowledge-processing-independent-20261004/manifest.json`: two isolated Knowledge0.18 installs,325 scoped owner/contract cases37.56s and actual three-owner acceptance170.47s, including9 publication interruption stages. Uses retained Data0.29/Research0.33 and SDK0.2. Sessions75087,65099 and55741 FINISHED; no active tests/hosts known.
- Actual evidence proves ordinary read200 with process permission absent, new graph/reasoning rejection, old decisions/rebuild stable, regrant permitting new reasoning without changing an old rejection, then full revocation/replacement behavior. Evidence: `docs/Audits/Evidence/BP-07-Extraction/Knowledge_Processing.json`.
- Source-adjacent Knowledge service/validation/transport READMEs updated. Replace new-consumption workers with0.18 before relying on this fence; older builds still use ordinary reads. Earlier accepted records remain unchanged.

## Versions, verification and cutover

- Planning/dev0.23.0; public Planning0.7.0. All506 public schema bytes remain unchanged. uv lock/sync completed.
- Planning migrations0001..0009 are applied and immutable. **Never run Planning<=0.22 migrators/writers on the new preparation workflow.** Data0.29/artifact0012 remains retained; no reset or downgrade.
- Final isolated proof: `.test-results/planning-repair-workflow-final-independent-20261004/manifest.json`:630 tests163.34s,28 process stages, two installations.
- Final actual Data proof: `.test-results/planning-repair-data-final-actual-20261004/manifest.json`:7 Planning workers,2 Data0.29 hosts.
- Source regression:626 tests151.89s before the additive publication-profile correction and three additional guard cases. The final installed630 suite covers final code. Focused coverage:125 tests96.23s;789 statements,80 branches,98.1588%. A later8-case runner run includes three new membership/abstention guards.14 dev boundary/schema cases passed17.63s. Ruff, schema publication and production dependency-boundary checks passed.
- Evidence: `docs/Audits/Evidence/BP-07-Extraction/Repair_Workflow.json`. Sessions32407 and41345 completed. **No active tests or fixture host processes remain.**

## What B2.02c.ii implements

- `repair/history.py` resolves the exact owned root/member, parent task/trace/observation and prior projection. `preparation.py` freshly reads feedback and interpretation via Data processing-content, verifies stored history, builds the deterministic child, and reviews every consumed source plus pinned Knowledge/Research inputs. Readers share one default20s operation deadline. Missing Research configuration produces explicit gaps, not scientific acceptance or a global quality veto.
- `source_access/artifacts.py` extracts the existing exact Artifact metadata/body/scope/hash/size checks. SourceReviewer reuses it. `ReadBudget.remaining_total()` prevents sequential owners from restarting the elapsed-time allowance. No persistent rights cache.
- `repair/manifest.py` binds a bounded256KiB input_observation_only manifest to root/parent/request/task, Artifact identities, Knowledge/Research hashes or gaps, and the actual packet digest/size. It re-renders the packet before binding. It does not duplicate raw source bodies or grant continuing processing permission.
- `persistence/preparation.py` and forward0009 own immutable SELECT/INSERT preparation records. They require matching family/member/task/parent, reject first registration after issuance or observation, permit an unissued reservation, and preserve exact replay bytes/timestamps. All66 journal statements and4 branches were covered.
- `repair/runner.py` creates one deterministic child with physical ordinal1. It enrolls and persists preparation before the ordinary PlanningRunner. PacketProvider delivers the actual diagnostic packet to the configured adapter. Completed/issued history requires its existing preparation and recovers without new input reads or calls. An unissued reservation needs fresh matching preparation. Membership-change reconciliation has at most3 retries. No SQL transaction encloses peer/provider I/O.
- `repair/chain.py` uses the original root attempt ceiling and authoritative aggregate admission. It retains earlier steps when later diagnostics are unavailable, work is pending, the model abstains, or budget is exhausted. A configured producer supplies published RepairInputs tied to the preceding trace, None, or RepairInputUnavailable. This is not a production automatic diagnostics publisher. Unknown/weak scientific output can still support bounded iteration.
- Source-adjacent repair, source_access, persistence and service READMEs describe these boundaries. BP-07.02 is still active, so its final child closeout audit is not due yet.

## Actual owner proof and compatibility correction

The actual Data probe publishes parent interpretation through TracePublisher and synthetic feedback through the public derived-upload SDK. It checks a missing Artifact, deliberate local response-byte tampering, revoked processing rights before issuance, regrant followed by one call, then another revocation and Data restart followed by historical replay with zero HTTP reads or calls. The combined Data fixture uses a **scripted Knowledge profile**. Earlier actual Knowledge/Research reader proofs remain separate. No live provider or scientific validity is claimed.

The first Data startup rejected the predecessor private feedback schema because its root `$id` is prohibited by Data0.29's closed local-reference validator. The correction preserves `feedback-v1.schema.json`, its digest `e4cda60bdfb4da8b841d983d9764d374f4972eaa7cab52b823589c50d7acc3e9`, and feedback record bytes. A new `feedback-publication-v1.schema.json` omits only that root `$id` and uses the distinct identity `planning.repair-feedback-publication-content/v1`. `publication_descriptor()` selects it; `bind_reference()` accepts only the exact legacy or publication profile. Data validation was not weakened. The new profile passed installed Data validation and actual HTTP publication.

The failed first fixture `.test-results/planning-repair-data-actual-20261004` is retained. `.test-results/planning-repair-workflow-independent-20261004` passed before the correction and is **not** final-source proof. Use the paths containing `final` above.

## Next authorized work

1. Finish final tracker/diff consistency review and commit/push the verified Knowledge checkpoint if not already done. B2.02 was pushed as6ee28ddc. Continue after push.
2. Current B2.03a.ii: read `docs/Build Plans/BP-07/BP-07.02 Owner handoff and accepted replay.md`. It has equal a/b/c gates; a splits i/ii. Current progress: a.i100%, a.ii0%, a50%, b/c0%; B2.03=16.67%. No declaration code exists yet.
3. Research0.33 public reads/DTOs already exist for ResearchQuestion and EvidenceNeed. `persistence/ledger.py` atomically publishes private immutable revisions/heads/links but has no authenticated public registrant. Add a focused declarations module, explicit optional host enablement and separate question/need write grants. Reuse existing declaration DTOs rather than inventing scientific acceptance. Return exact owner-stored declarations; changed bytes or stale head conflict. Do not access Research tables from Planning.
4. New registration provenance must commit atomically with new record/head/link changes. Extract a transaction-level private ledger publication helper without changing existing publish semantics. A forward Research0013 may add immutable first-public-registration actor/time/digest and distinguish a preexisting private record; never relabel the first public registrant as the historical creator. Keep applied0001..0012 immutable. Once0013 is applied, forbid older Research migrators, including the retained0.33 used by current fixture scripts. Closed BP-06 plans remain closed.
5. Refine a.ii into bounded owner-store and HTTP/installed-proof substeps if useful, preserving its weight and updating canonical current task. Before implementation read Research declarations/identity/persistence/transport boundaries and targeted tests. Existing API invoke maps ResearchIdentityError to503 for reads; new declaration policy failures need their own safe403/404/409/422 mapping without changing read corruption behavior. Public writes require an explicit host flag; default read hosting stays read-only.
6. Gate b later owns Planning automatic diagnostics/candidate-answer Artifact publication and durable question/need/graph handoff. Gate c owns actual receipt binding and accepted typed-correction replay. Do not start these before owner prerequisites pass. Preserve exact original requests, stable retry identities, current rights, and future-campaign correction policy. Knowledge/Research retain acceptance authority; Runtime owns execution acceptance.
7. Update canonical trackers, MBT, history and Restore before significant commits. Absolute local timestamps with seconds; MBT at most25 recent rows, archived under proper table headings. Design writing earns no credit. No live provider call without model/egress/spend choices.

No owner choice blocks deterministic work. Live provider/model, egress and spend are still unset and block only real calls. Human scientific corrections apply between campaigns. Preserve weak, contradictory and unknown points for future improvement; do not add an in-campaign human wait or global scientific-quality veto.

## Environment and retained installations

- Workspace `Z:\mvp20-split`, PowerShell, America/Chicago. Git: `git -c safe.directory=//DesktopNAS/Code/mvp20-split`; main, `https://github.com/neverhumanbot/mvp20-split.git`. Commit/push authorization persists.
- Set `PYTHONUTF8=1`. Python: `v2/dev/.venv/Scripts/python.exe`; uv: `v2/.venv/Scripts/uv.exe`. pytest: `-c v2/dev/pyproject.toml --tb=short`. Coverage belongs under `v2/.test-results`.
- PostgreSQL suites run **serially**. Never reset/downgrade/delete retained fixtures. URLs/tokens remain environment-only; never print them. `dev/postgres_fixture.py` supplies owned state and scoped roles.
- Tests use importlib mode; behavior folders have no `__init__.py`. Use `.absolute()`, not `.resolve()`, on the mapped drive. Discover filenames with `rg --files`; avoid Windows wildcard paths as rg operands. Verify new patch paths exist.
- Latest Planning: `.test-results/planning-repair-workflow-final-independent-20261004/{initial,replacement}/Scripts/python.exe`. `verify_planning.py` includes0009, both feedback schemas and preparation/run/replay process stages. Old-history replay uses the new installation, never an old migrator.
- Data0.29: `.test-results/data-processing-content-independent-20261004/environment/Scripts/python.exe`. `verify_planning_repair_data.py` pins Planning0.23/Data0.29.
- Latest Knowledge0.18: `.test-results/knowledge-processing-independent-20261004/{initial,replacement}/Scripts/python.exe`. Prior0.17 read fixture remains `.test-results/knowledge-exploration-http-20261003/environment/Scripts/python.exe`; do not use it for new processing authorization.
- Research0.33: `.test-results/research-views-http-20261003/environment/Scripts/python.exe`.
- Runtime0.20.2: `.test-results/runtime-domain-receipt-peer-20261002/environment/Scripts/python.exe`.
- `verify_planning_knowledge.py`, `verify_planning_research.py` and their probes still pin Planning0.20. Update pins before future runs. Do not relabel those earlier reader proofs as combined actual Knowledge repair execution.
- Qdrant1.19.1 primary/replacement fixtures remain retained. Their `.test-results/qdrant-fixture.json` and replacement files contain keys: never dump them or restart/reset them during another suite.
- No goal, skill or subagents are active. v1 LICENSE baseline debt remains; do not edit v1.
