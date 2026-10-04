# Restore

## Resume here

- Refreshed 2026-10-04 09:22:48 (America/Chicago). **Read this file first after compression**, as the owner explicitly requested. This was done at the previous compression.
- Continue authorized work across milestones, commits, pushes and compression. Do not stop merely to report completion of a checkpoint. No subagents, no JARVIS access, and no v1 edits.
- **BP-07.02/B2.02c.ii is verified complete. Current task: B2.03 owner handoff and accepted typed-correction replay.** Next: B3 failure and semantic-category oracles.
- The verified checkpoint is ready for final diff review, commit and push. Previous pushed commit:565c0622. Check Git log/status before repeating any commit; then continue B2.03 without another permission request.
- Canonical child, parent, MBT and history are updated. Child41.67%, Build55.56%, Acceptance0%,1/4 deliveries closed. B1=100%, B2=66.67% (.01/.02=100%, .03=0%), B3/V1=0%. Parent28.33%,5/20 closed; P1=100%, P2=41.67%, remaining phases0%. MBT has25 recent rows.

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

1. Finish final Git diff/tracker consistency review, commit/push the verified B2.02 checkpoint if not already done, then continue. All known working changes belong to this task.
2. Start B2.03 with a bounded design/coherence review against actual owner contracts. Scope includes automatic published diagnostic production, public Research declarations, Data candidate-answer Artifacts, Knowledge proposal submission and accepted typed-correction replay. Research currently exposes reads but **no public declaration-write endpoint**. Do not bypass that gap with Planning access to peer SQL/private implementations.
3. Read the current tracker and owning Research/Knowledge/Data/Planning READMEs/public contracts before targeted source. Decompose B2.03 inside its existing milestone weight before implementing it. Preserve exact owner receipts, immutable idempotency, current rights and future-campaign correction policy. Knowledge accepts domain changes; Research owns research state; Runtime accepts execution decisions.
4. Keep canonical trackers, MBT, history and Restore current before significant commits. Use absolute local timestamps with seconds. MBT retains at most25 recent rows; archive overflow under a proper table header in BP-07 Planning History. Design writing earns no implementation credit. Earlier phases stay closed.

No owner choice blocks deterministic work. Live provider/model, egress and spend are still unset and block only real calls. Human scientific corrections apply between campaigns. Preserve weak, contradictory and unknown points for future improvement; do not add an in-campaign human wait or global scientific-quality veto.

## Environment and retained installations

- Workspace `Z:\mvp20-split`, PowerShell, America/Chicago. Git: `git -c safe.directory=//DesktopNAS/Code/mvp20-split`; main, `https://github.com/neverhumanbot/mvp20-split.git`. Commit/push authorization persists.
- Set `PYTHONUTF8=1`. Python: `v2/dev/.venv/Scripts/python.exe`; uv: `v2/.venv/Scripts/uv.exe`. pytest: `-c v2/dev/pyproject.toml --tb=short`. Coverage belongs under `v2/.test-results`.
- PostgreSQL suites run **serially**. Never reset/downgrade/delete retained fixtures. URLs/tokens remain environment-only; never print them. `dev/postgres_fixture.py` supplies owned state and scoped roles.
- Tests use importlib mode; behavior folders have no `__init__.py`. Use `.absolute()`, not `.resolve()`, on the mapped drive. Discover filenames with `rg --files`; avoid Windows wildcard paths as rg operands. Verify new patch paths exist.
- Latest Planning: `.test-results/planning-repair-workflow-final-independent-20261004/{initial,replacement}/Scripts/python.exe`. `verify_planning.py` includes0009, both feedback schemas and preparation/run/replay process stages. Old-history replay uses the new installation, never an old migrator.
- Data0.29: `.test-results/data-processing-content-independent-20261004/environment/Scripts/python.exe`. `verify_planning_repair_data.py` pins Planning0.23/Data0.29.
- Knowledge0.17: `.test-results/knowledge-exploration-http-20261003/environment/Scripts/python.exe`.
- Research0.33: `.test-results/research-views-http-20261003/environment/Scripts/python.exe`.
- Runtime0.20.2: `.test-results/runtime-domain-receipt-peer-20261002/environment/Scripts/python.exe`.
- `verify_planning_knowledge.py`, `verify_planning_research.py` and their probes still pin Planning0.20. Update pins before future runs. Do not relabel those earlier reader proofs as combined actual Knowledge repair execution.
- Qdrant1.19.1 primary/replacement fixtures remain retained. Their `.test-results/qdrant-fixture.json` and replacement files contain keys: never dump them or restart/reset them during another suite.
- No goal, skill or subagents are active. v1 LICENSE baseline debt remains; do not edit v1.
