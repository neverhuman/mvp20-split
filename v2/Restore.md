# Restore

## Current Checkpoint

- Last refreshed: `2026-10-03 15:00:03` (America/Chicago).
- Active BP-06.05/B1.04c recoverable publication orchestration. No owner blocker; continue authorization persists. Latest pushed12ee369 covers B1.04a; b verified and ready to commit/push. a-b100%, c-d0%, B1.04=50%, B1=58.33%, Build19.44%, child14.58%, parent69.10%, gates0/4 and16/24.
- Data0.16.0 editable and independent package installed. artifact_0009 applied successfully to retained DB; Data<=0.15.0 must NOT run migrations on it. No reset/downgrade. Public representations0.1.0/420 schema bytes unchanged.
- No tests running. Independent full run418 passed/2 failed due to omitted separate Research interpreter; both pass38.17s when configured, completing420 distinct cases. Source147 pass11.10s; dev14, lint/boundaries/schema pass. Independent Data0.16.0 is `.test-results/data-binding-state-20261003/environment/Scripts/python.exe`. Coverage982/983 statements,63/64 branches; claim-publication race assigned B3. Evidence Binding_State.json retains initial failure and recovery.

- b implementation: SourcePreflight exact source revision/Artifact/span/hash/UTF8/profile and current read/process rights, retained cache reuse for unavailable exact encoder. BindingRequests immutable jobs and actor aliases with rights epoch; request conflicts roll back new jobs. BindingLeases independent DB-clock token/fence; BindingJournal ordered commands-before-effects, actual CommandStore.inspect proof, selected upload proof, actual final derivation and current-rights visibility. artifact_0009 has immutable jobs/requests/events/finalbindings plus narrow mutable cursor. No source bytes in journal.
- Attempt1 binding command bytes unchanged. Later numbered attempts allowed only after actual retained rejection; absent/pending acknowledgements reuse same command. Tests manually drive actual Artifact pipeline and reconstruct lost-response prefixes. B1.04c must supply orchestration; d broader source-independent reuse/rights/convergence proof; APIs are B1.05-.06.
- Next: commit/push verified b checkpoint (trackers/history updated), immediately implement c. No new approval needed.

- c boundary: check all needed grants, original published request replay before source reread, fresh preflight for pending/new alias; register intent before compute. Use WorkLeases/EncodingResults then BindingLeases/Journal. Orchestrate DerivedPublications.begin, Uploads.start/finish, LocalBytes.writer and Finalizer.finalize outside SQL locks. Close writer before settlement; lost effects recover through retained prefix. One bounded call, no infinite polling. Handle abandoned/exhausted uploads explicitly without treating missing response as rejection. Public EncodingStatus remains pending/published; no silent wire-v1 additions.
- READMEs describe verified b. foundation-packages inventory updated0.16.0. Existing B1.03 repeated-migration test now expects0009 and disposes migrator engine. Initial0009 migration passed, but no pre-upgrade checksum claim; repeated-upgrade preservation remains separately tested. Earlier source fixture typo (profile object instead of ref) and conflict test accidentally using same default profile fixed before passing147.
- Use rg --files before path guesses; no JARVIS/v1/subagents. PYTHONUTF8=1, dev/.venv/Scripts/python.exe, uv .venv/Scripts/uv.exe, pytest -c dev/pyproject.toml, COVERAGE_FILE under .test-results, git safe.directory=//DesktopNAS/Code/mvp20-split. Avoid simultaneous PostgreSQL suites. Milestones/commits are not stopping points.

## Decomposition and Resume Discipline

BP-02 now has six focused child plans and separate history. BP-03..09 now have 35 canonical child plans with owned objects/contracts, transition/algorithm decisions, named failure oracles, independent test tiers and replacement acceptance. BP-02 children have detailed API/transaction/crash matrices. Parent planning histories preserve prior task pairs; new queued-parent denominators are 16/24/16/24/20/20/20; current progress is above. The nearest child gets physical design, failure tests, module replacement boundaries and scoped audit. Parent rollups count child implementation once. The preliminary 34-task count was explicitly corrected to 32 by separating pure design gates S1/A1; prior design work remains complete.

Contract and persistence READMEs describe actual implemented boundaries. Earlier scripted artifact-client probes remain distinct from the actual installed REC-01..09 evidence now completed by .06. Do not confuse either tier with scientific or target-host correctness. Use [MBT](docs/Build%20Plans/Master%20Build%20Tracker.md) and child tracker, not old task IDs in history.

## Product and Architecture Direction

The engine stays general, with bio-available polymers a likely application. First many releases are internal/demo, one user and one active autonomous campaign with concurrent tool invocations. Target host is DGX Spark or a partner Threadripper; exact host/provider/data-egress selection remains a deployment decision.

Human changes apply between campaigns. Deterministic policies and eligible agents handle routine execution/review; unresolved prerequisites produce truthful terminal outcomes rather than indefinite human waits. Emergency termination/revocation remains available. Knowledge, scientific evidence and model promotion retain explicit authority and provenance.

Two authored graphs remain distinct: campaign execution and neuro-symbolic knowledge. Lineage is derived. Graph Runner is within Campaign Runtime and owns coordination, aggregation and supervision; durable model engagements return proposals, never execution authority. Primary services/tools have private code/state and public versioned contracts. Independently packaged tool replicas add capacity; the registry remains the node/tool index. K3s is proposed, not deployed.

Module rewrites are expected. The source-adjacent README and linked schemas/tests define the replacement boundary. Preserve state/evidence and version intentional contract changes. Do not edit v1 to obtain reusable components.

## Read and Resume

1. [AGENTS](AGENTS.md), [MBT](docs/Build%20Plans/Master%20Build%20Tracker.md), then the owning plan.
2. [Master Architecture](Architecture.md), following immediate children to the active boundary.
3. [Product Requirements](docs/Architecture/Requirements/Product_Requirements.md), [requirements guide](docs/Architecture/Requirements/README.md) and [architecture guide](docs/Architecture/README.md).
4. [Contract packages](contracts/README.md), [runtime foundation](services/campaign_runtime/README.md), [foundation tooling](dev/README.md).

The high-level specifications and earlier flat design/history files live in `docs/Architecture/Requirements/`; indexes, source map and reuse baseline stay at Architecture top level. PDF exports may be stale; Markdown is authoritative. JARVIS is external reference only and requires task-specific authorization to access.

## Implementation Limits

Private PostgreSQL schemas/migrations and canonical command registration/terminal receipt transactions exist. Default runtime construction remains validation-only; explicit fixture hosting enables durable lifecycle and read endpoints. General campaign validation reports `executable=false`. Artifact upload/finalization APIs now publish verified immutable references; protective reservation/confirm/reconcile handshake is implemented against a configured public runtime outcome client; bounded reconciliation/cleanup and standalone hosting are implemented. Optional synthetic fixture admission is implemented; configured claim/renewal handlers are implemented; atomic fixture completion acceptance and retention delivery are implemented; configured deterministic graph admission/advancement and process/peer replacement acceptance are complete in BP-04.02; validated scientific tools and provider calls are not implemented; bounded synthetic Knowledge reasoning and Data artifact/logical-receipt publication exist; Research assessment/publication/correction and actual Runtime receipt/partial-output/recovery verified; Studio has verified transport/page models, measured synthetic interaction and production-client browser failure proof; actual-owner observation UI is accepted; topology/navigation accepted under BP-05.02; next-campaign authoring is accepted under closed BP-05.03; integrated interaction/performance/replacement acceptance closed under BP-05.04. Paired integration establishes fixture retention; process-crash tests do not establish target-host power-loss durability or scientific validity. Those gates remain in their named children/successor plans.

Baseline verification: no changed manifest file content; verifier reports pre-existing added `v1/LICENSE` already present in commit `99d219c`. Do not regenerate the frozen manifest or alter v1 to suppress this discrepancy.
