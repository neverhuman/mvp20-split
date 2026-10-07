# Restore

Refreshed 2026-10-06 23:32:34 (America/Chicago). Read FIRST after compression.

## Current task

BP-09.02/V1 independent replacement/browser compatibility/scoped drift audit. B1-B3 complete.
Child75%, Build100%, Acceptance0%; BP-09 parent35%,7/20. BP-09.01 and BP-08 closed.
Owner chose this Windows x86_64/Python3.12 computer and local access127.0.0.1 only.
Continue until genuinely needed; commit/push significant verified work. No current decision blocker.
B2.01 pushed d15276f1; B2.02 pushed77a2659a. B3 ready to commit; all tests/probes exited.
No owner/gateway/supervisor processes remain; dedicated PostgreSQL/Qdrant remain running.

## Latest verified B2 boundary

Six explicit owner migrations plus repeat migrations succeeded on dedicated schemas only.
Planning0.99 fixes reproduced0.98 serving with planning_migrator: actual wrong-role rejection,
service /ready success;34 persistence Pythonfiles byte-identical, schema0020 unchanged.
New serving install ROOT.test-results/local-planning-role-20261006a; original0.98 preserved.
Allsix owners plus gateway started over supervisor control, restricted serving roles, no migrations
on startup. Gateway SERVING_HOSTS has no database authority; OWNERS remains six SQL owners.

B2.02 actual ROOT.test-results/local-outage-receipt-20261006b PASSED: allsix owners report DB
unavailable during dedicated PostgreSQL stop/start, recover, accepted dormant synthetic Registry
registration replays byte-for-byte, journal unchanged, all7 processes cooperatively drain exit0.
No campaign/scientific activation/provider call. Registration remains dormant, not eligible.
Earlier outage a recovered but Registry drain hung on unbounded connect; fixed every serving
DB URL with connect_timeout=5. First outage also exposed Docker dynamic ports changing60687->51130.
Explicit forward repair fixed both dedicated stores while preserving volumes, credentials, images,
identity and recorded60687/60688 ports. Old containers renamed -dynamic-baseline, STOPPED.
NEVER start a stopped baseline alongside replacement on shared volume. No data deletion/reset.

Deployment lifecycle uses Windows jobs, gated owner startup, one-shot unbuffered controlpipe
D -> interrupt_main for cooperative HTTP drain. Repeated drain sends no second interrupt.
45second timeout reports timed_out and leaves process alive; explicit force-stop is separate.
Original buffered daemon pipe reader caused Windows exit fault, fixed os.read. Gateway0.2
uses non-daemon accepted requestthreads; actual blocked proxyresponse test waits for completion.
Current transport drain does not yet quiesce future autonomous workers; BP-09.03 must do so.

Readiness CLI takes --root and --manifest; public owner HTTP/checkCLIs only, noforeignSQL.
Three static health endpoints are liveness only; ownerCLI checks assessDB access. Data/Planning
ready and Registry catalog read use actualDB. Read-only config/journal snapshots work under
supervisor lifetime writerlease. Health checks are observations, not scientific eligibility.

138 deployment/gateway regressions passed12.20s; coverage rerun138passed12.25s.
Parent-process coverage1283/1689statements,156/260branches,73.83%combined. Live Docker/SQL/CLI
proof is separate; rareOS/process errors, explicit repair interruption remain gaps. Production
boundary check passed. Metadata foundation-packages regenerated only (not fullfoundationtest).
Evidence docs/Audits/Evidence/BP-09-Deployment/{Local_Outage_Drain,B2_Coverage,Planning_Host_Role}.json.

## Local installation

Logical root LOCALAPPDATA/Amphora/local-v2/installation. Windows Store Python redirects it to
physical LOCALAPPDATA/Packages/PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0/LocalCache/Local/
Amphora/local-v2/installation (verified GetFinalPathNameByHandleW). Use physicalpath fromPowerShell,
logicalroot fromselectedPython. stores.json, credentials.dpapi/current-userDPAPI, supervisor.dpapi,
stable routes and boundedlogs. Identity7be3465bdf1e4fa6b9189637e51e6f96. PG127.0.0.1:60687,
Qdrant127.0.0.1:60688. PostgreSQL databaseamphora_local,12migrator/service roles,sixschemas.
Read routes for eight API/control ports; never print vaultvalues/rawDockerinspect/errors.

Manifests under root/configurations: readonly-20261006a original7hostproof;
readonly-drain-20261006a gateway0.2; outage-receipt-20261006a grantsRegistryread/registerONLY.
Noactivation/deploy. Allotherprincipalsread-only. dev/compose_local_readonly.py --registry-evidence
creates fresh immutable nonsecret configuration; driver verify_local_readonly.py --drain
--dependency-failure --registry-evidence owns exact outageproof. repair_local_store_ports.py is
one-timeexplicitforwardrepair, not startup. migrate_local_owners.py uses originalownerreleases.

Six original installs ROOT.test-results/local-owner-inventory-20261006a/owners:
Runtime0.65,Data0.30,Registry0.1,Research0.40,Knowledge0.18,Planning0.98;79localwheels.
NewPlanning0.99 directoryabove; gateway0.2 ROOT.test-results/local-gateway-drain-20261006a.
Older gateway0.1installb preserved. Deployment0.2 currenteditable awaits V1 independentqualification.
Studio0.9 dist/local assets, CSPsafe standaloneAJVvalidators, Monitorentry. Design/Explore shell
assembly remains BP-09.03. Earlier actualbrowser proof v2/.test-results/studio-local-entry/
2026-10-07T03-44-36-139Z used isolatedgateway0.1 and syntheticRuntimepeer, nofullsystemclaim.

## Next tasks

Commit B3 then V1. B3 evidence copied to docs/Audits/Evidence/BP-09-Deployment:
Local_Capacity (8-byte servicequota notphysicaldiskfull), Wrong_Roles (five correctmigrator
CLI rejection), Provider_Unavailable (installedPlanningloopback503/refusal,noexternalcall),
Current_Profile (actualindependentDeploymentCLIvalidate/preflight,current7hostsCPUonly),
Deployment_Reproduction (two fresh0.2installsidenticalwheelsha).
FreshDeployment0.2 ROOT.test-results/local-deployment-runtime-20261006{a,b}. Use b for
actual V1 independentcontroller; verify_local_readonly.py imports only Deployment+stdlib,
so run with isolated b Python -I scriptpath to make sys.executable the installedcontroller.
Add replay-evidence option to replay original Registry command/receipt from Local_Outage_Drain
withoutnewmigration/admission. Retained artifact/bytes from Local_Capacity can be reread using
its stored scope/capacity configuration if needed. Browser should requalify isolated gateway0.2
using AMPHORA_GATEWAY_TEST_PYTHON and existing studio/tests/browser/local_entry.mjs.
Independentcontroller builds passed; V1 execution/replacement/audit remain. No owner blocker.
Providerprobe source owned by Planning/tests/openai_provider/unavailable_probe.py, noPytest import;
uses explicit test-only connectionfactory through real installedadapter, preservesunknownusage.
No production source changed in B3. Boundarycheckpassed. ScientificLinux-onlytools and actual
model/campaign/Design-Explore shell remain BP09.03 after acceptance. No paidcalls in thischild.
## Operating rules

Read v2/AGENTS.md. v1 read-only; noJARVIS/subagents/goals. PYTHONUTF8=1 each exec.
Python v2/dev/.venv/Scripts/python.exe; pytest -c v2/dev/pyproject.toml --import-mode=importlib.
uv v2/.venv/Scripts/uv.exe; PYTHONPATH Z:/mvp20-split/v2/dev fordevimports. No source/test/dev/README
edits while any verification/build/probe active; wait actualexit. .absolute(), not.resolve();
no broadNASvenvscan or tests/__init__.py. Never reset oldfixtureDBs/replayoldmigrators.
Git -c safe.directory=//DesktopNAS/Code/mvp20-split; main. KAPPython18720/2912 are unrelated.
Update canonical child/parent/MBT percentages and Restore. UIguidelines alreadyread; noUIchanges
in B2. Existing syntheticOpenAIauthorization remains for later selected-modelgate; no keysneeded.
