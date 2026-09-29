# Restore

## Current Checkpoint

- Last refreshed: `2026-09-29 17:57:39` (America/Chicago).
- Canonical position: BP-04 -> BP-04.05 / Build / B1; activation audit corrected_ready. No owner input needed.
- Progress: BP-04 active 83.33% (20/24); .01/.02/.03/.04A/.04 closed/audited 100%; .05 active 0% (Build/Acceptance 0%); BP-05..09 queued.
- .04/V1 passed first installed run, exec17677 finished exit0; log .test-results/bp0404-v1-installed.log. Scope894ba643856043aaa19373c0fc7f1675, 17 independent wheels, 9 owner/SDK/tool installs plus fresh Runtime replacement. Five actual tools, 17 invocations, 44/44 reservations confirmed through five bounded passes, original predecessor/successor/receipt/Artifact/proof history preserved. Audit docs/Audits/BP-04.04_Baseline_Closeout.md; evidence docs/Audits/Evidence/BP-04-Baseline/V1.json. No verification running.
- Five solver images/goldens/nonroot/sibling-isolation passed; manifest .test-results/tool-images/bp0404-solver-20260929-1747/manifest.json, exec23625 finished. Linux/amd64 image proof is distinct from Windows wheel-process acceptance. dev build_tool_images.py/verify_graphs.py now have solver profiles preserving defaults. Fixture profile dedup uses public schema identity instead of file path. Twelve dev tests passed. No production change in B3/V1.
- Current supported versions: Runtime0.10.0, graph-runtime0.4.0, campaigns0.4.0; migration runtime_0014, 168 schemas (all162 predecessors preserved). B2 fullgate passed1169 tests,19 installs,RECscope54fdb5ad5a5f4126b54151e1b2242bba. First attempt had one transient Windows TCP address-in-use failure; focused/repeated gates passed with no production change.
- Resume: .05/B1 bounded graph inspection/snapshots/detail and resumable invalidations. Read owning .05 activation audit, inspection/README.md, coordinator/reads.py and inspection/cursors.py/history.py before coding. Existing graph pages use raw activation cursors over mutable state; existing audit pages already pin immutable history with signed revision/filter/scope/expiry. Reuse receipt/completion/history authority; do not add another journal or generic backend. Refine a focused graph observation architecture/contract, preserve existing schemas/routes, explicitly resnapshot stale/gapped cursors. .05B2/B3 integrate recovery/reader consistency; V1 closes parent.
- Git: df17a9f B1,6d2f92e B2,939b79d B3 pushed. V1 closeout changes pending commit/push. Identity tkn1234 <alb_gen@live.com>, origin https://github.com/neverhumanbot/mvp20-split.git. Update canonical child -> parent -> MBT -> Restore before significant commits.
- B3 evidence:116 focused tests,five actual process cases; successors104/104 statements,6/6branches; retain kernel49/49,26/26(parent only). Source test executor extracted into tests/baseline/execution.py; process/installed controllers intentionally separate. Source hashes/independent oracles remain original; no scientific authority claimed.
- Workspace v2 active, v1 frozen/read-only. External JARVIS not authorized. Named stage tools/readmes own rebuild boundaries. No subagents authorized. Scientific/provider/host choices remain their later gates, not blockers here.
- Environment: use mapped-path v2/dev/.venv/Scripts/python.exe for pytest/verification; uv run resolved UNC and failed native psycopg DLL loading. uv still supports locks/build/sync. Retained labeled PostgreSQL fixture credentials only ignored .test-results/postgres-fixture.json; never reset or run installation-wide admission suites concurrently. AMPHORA_TEST_POSTGRES=1 explicit. PowerShell redirected logs may be UTF-16; exit $LASTEXITCODE after native redirection. Git safe.directory=//DesktopNAS/Code/mvp20-split; do not override newline config. v1/LICENSE is a pre-existing manifest discrepancy, do not edit baseline.
- One-use scripts under .test-results/close_* and scaffold/refactor/extract scripts are not idempotent; never rerun them. check_changed_links.py is safe to repeat.

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

Private PostgreSQL schemas/migrations and canonical command registration/terminal receipt transactions exist. Default runtime construction remains validation-only; explicit fixture hosting enables durable lifecycle and read endpoints. General campaign validation reports `executable=false`. Artifact upload/finalization APIs now publish verified immutable references; protective reservation/confirm/reconcile handshake is implemented against a configured public runtime outcome client; bounded reconciliation/cleanup and standalone hosting are implemented. Optional synthetic fixture admission is implemented; configured claim/renewal handlers are implemented; atomic fixture completion acceptance and retention delivery are implemented; configured deterministic graph admission/advancement and process/peer replacement acceptance are complete in BP-04.02; scientific tools, knowledge reasoner, provider calls and Studio are not implemented. Paired integration establishes fixture retention; process-crash tests do not establish target-host power-loss durability or scientific validity. Those gates remain in their named children/successor plans.

Baseline verification: no changed manifest file content; verifier reports pre-existing added `v1/LICENSE` already present in commit `99d219c`. Do not regenerate the frozen manifest or alter v1 to suppress this discrepancy.
