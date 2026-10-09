# Restore

Refreshed2026-10-09 10:02:00 America/Chicago. Read FIRST after compaction.
Owner says continue until needed; milestones/commits are not stopping points.
No subagents/JARVIS; v1 read-only. Preserve untracked ocular PDF/DOCX.
Do not edit source/tests/module READMEs while verification/installation runs.

## Current task and trackers

UI-01.06 bounded launch API approved2026-10-09. L1/L2/L3 complete;
L4=75%, overall75%. UI-01.05=58.33%, K1=100/R1=75/I1=0.
UI-01 parent55%/Build68.75% unchanged. Sequence UI-01 -> UI-02 -> POP-01 -> ML-01.
LR-01 paused25%/Build33.33%, never advance for blocking launch repairs.
Latest pushed8d1c9676. L4 corrections/helpers/tests/docs uncommitted; commit/push
significant verified checkpoint next. No owner decision currently required.

## Verification and outstanding gates

- Deployment0.18.2 independent installation498 tests and four process/container
  recovery probes PASS: v2/.test-results/launch-installation-20261009c.
- Source166 launch/catalog checks; Studio238 page-model checks pass.
- Local actual browser launch/reload/scientific results1440/390 PASS:
  launch-actual-browser-20261009e, run644881543fc34638b205a396594b7fe5,
  request1cf42d0e-c640-4e06-85e3-93bedc45f8e9. Five succeeded nodes, public
  released receipt and graceful owner drain documented public-final.json and
  launch-live-20261009d/drain.json. About16seconds launch-to-completion.
- LAN actual campaign844270e31d9f40198fee0def932542b0/requestaccfb14d-1a4c-42ed-958e-c74773ef149f
  completed/released, but original browser completion wait stalled. Preserved
  launch-lan-browser-20261009a/runtime-final.json; Node terminated after diagnosis.
  Read-only restored browser shows completed run: launch-lan-inspect-20261009a.
- Reproduced missing automatic retry for Runtime409/410 coherent-snapshot conflict.
  Studio0.23.2 corrects retrySnapshot/visible execution polling; denied/invalid still
  hide data and do not retry. Injected browser BEFORE fails, AFTER passes:
  launch-snapshot-conflict-before/after.238 page-model checks pass, build passes.
- Final verification PASS:337 Studio tests, production boundaries and3 campaign
  integration tests. No verification currently running at this checkpoint.
- Corrected actual LAN browser launch/reload/results1440/390 PASS:
  launch-lan-browser-20261009b. No serious/critical axe violations. Original LAN
  failed attempt remains preserved. Scoped audit UI-01.06_Launch_Integration.md.
- L4 credits configuration, actual results, terminal drain (3/4). Accepted-run restart
  preserved identity but deadline expired; actual pending-container interruption
  still required. L5 installed evidence accumulating does not bypass that gate.

## Current serving installations

New local helper session93769, output launch-live-20261009f, READY10:00:06 until
2026-10-10 10:00:06. New completed LAN launch receipt is in launch-lan-browser-20261009b.
New LAN helper41240, launch-lan-20261009b, READY https://192.168.1.70:57013.
Local http://127.0.0.1:57013. Both use immutable Deployment0.18.2/Gateway0.4 in
launch-live-installation-20261009d and copied Studio0.23.2 assets in outputF.
Default campaign is completed LAN run844270e31d9f40198fee0def932542b0.
Previous local E91066 and LAN A10910 drained cleanly; D7786 also drained cleanly.
No active campaign at latest checkpoint. No paid model calls.

Physical private root (WindowsStore Python redirects logical AppData):
C:/Users/alb_p/AppData/Local/Packages/PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0/LocalCache/Local/Amphora/local-v2/restore-20261007b
TLS sibling: .../LocalCache/Local/Amphora/lan-demo-20261008.
Runtime57018, Artifact57012, Registry57016, launchAPI57021, toolTLS53955/53956.
LAN Gateway separate process, same backend; no shared Docker daemon outage needed.

## Implemented corrections / history

Deployment AdmissionCapacity offers standby without turns and requires acknowledged
fresh Registry capacity before Runtime admission; rebinding withdraws standby.
Unresolved admission rechecks preflight after restart, preserves first pendingreceipt,
and latches changed/disappearing receipt. RuntimePeer reads modern graph-observation
metadata; legacy graph-runs endpoint rejects authored graphs403.
Identical authenticated launch POST can explicitly reconcile a known accepted run;
requires original receipt + scope/run/plan before next-tick original binding checks.
No new admission POST/identity inside recovery. Studio0.23.1+ provides explicit button.
Original requestdd04e99e-b6bf-434f-b230-20643833f936/run70fa8eddf8de40cfa380dd9b8fb57e7a
recovered after installed restart, then blocked graph_deadline_exhausted/released.
Preserve original C/D browser recovery/evidence; never call that scientific success.

Dev helpers campaign_launch_demo/serve_campaign_launch_demo publish a self-contained
draft from five exact original ArtifactRefs, preserving nodes/edges/Knowledgecontext.
Browser alone admits. Shared Controller shutdown now quiesces workers before TLS,
Gateway and owners; actual clean shutdown verified twice. LAN helper loads dedicated
launch credential sidecar separately from original owner vault.

## Next actions

1. Commit/push significant verified L4 checkpoint; audit/trackers updated.
2. Knowledge/result regression over LAN via verify_knowledge_review.py --suite knowledge,
   session launch-lan-20261009b, new output, --tls physicalTLS.
4. Controlled actual campaign interruption while a scientific container is pending:
   retain original request/run/container IDs; stop ONLY owned supervisor/helper,
   restart exact config/installation, prove no duplicate admission/container.
   Existing L2 installed Docker proofs do not substitute actual L4campaign evidence.
5. L5 audit/trackers/commit, then remaining UI-01 N2 gates and I1 in MBT order.

Direct actual browser probe: studio/tests/integration/campaign_launch.mjs accepts
ready.json outputdir optionalbrowser-recovery.json (explicit original-run recovery).
launch_inspection.mjs is read-only restored-state diagnostic. All keys environment-only.
Preserve failed attempts, distinguish synthetic science and fixture recovery evidence.

## Commands and constraints

Git -c safe.directory=//DesktopNAS/Code/mvp20-split -c core.safecrlf=false.
Stage exact owned files only; NEVER ocular PDF/DOCX or private .test-results.
Python v2/dev/.venv/Scripts/python.exe; pytest -c v2/dev/pyproject.toml mandatory.
Set PYTHONUTF8=1. uv v2/.venv/Scripts/uv.exe; npm.cmd cwd v2/studio.
Original owners: .test-results/demo-20261008/frozen-original/owners.json (root).
One supervisor lease/root. Immutable installations/config/assets; no in-place patches.
Stop serving helpers through their output/STOP, wait session; never kill unrelated PIDs.
Use rg --files before guessing filenames; PowerShell glob paths do not expand for rg.
