# Restore

Refreshed `2026-10-05 15:06:59` (America/Chicago). **Read first after compression.**

## Resume

Latest pushed06fd08b0 (B1.03b). B1.03c VERIFIED `2026-10-05 15:06:59` but not committed. Runtime/dev0.26, DB runtime0019 applied. NEVER run Runtime<=0.25 migrators.65 journal/migration cases20.50s (33pure,26journalSQL,6legacy),486 statements/60branches99% (one reserved64th-event fallback unexecuted; normal16claim exhaustion verified). SQL tests all finished; boundary suite12passed8.54s,Ruffpassed. Allverificationfinished. No owned hosts.

Canonical child17.19%,Build22.92%,Acceptance0%,0/4;parent63.44%,12/20. B1 .01/.02=100%,.03=75%,.04=0%;B1=68.75%. B1.03a/b/c100%,d0%. NEXT diff/links, commit/push c, then B1.03d actual competing processes and independently installed retained SQL recovery. Do not end at checkpoint.

C modules: delivery.py/delivery_values.py own DB-clock1..300s capped original deadline, same claimID returns original expiry/fence, newID reacquires, expired holder cannot append.16claims/64events; receipt operation/readback exact;unknown retained same outgoing command. ResponseJournal responses.py binds original request/actor/attempt/capture,64immutable responses/request, commands.register then atomic response+recorded receipt under runlock; exact retry after terminalrun,read history without fresh permission. No graph acceptance or provider dispatch.0019 adds lazy control + immutable events/responses, scopedFKs/narrowgrants. Initial closure reason local error fixed.65tests allpass. Current production README truthful99%gap.

D design not yet coded: use new dev helper to build isolated Runtime/public closure, own copied testroot preserving services/campaign_runtime/tests and contracts fixtures. Existing verify_runtime_scope builds currentclosure and compares162old Runtime0.20.2 productionfiles, tests111scope/publicGraphRuntime, noSQL/migrators. Reuse builds for two current0.26 independent installs. Need actual SQL barriers/process death around lease/append/response commit and exact retained frame/command/receipt/timestamps recovery, oldmigration34+0018 unchanged. Secrets env-only, noURL/token logs. No oldRuntimepeer migrator! Rootpostgrestest fixture imports dev/postgres_fixture and compiler fixture references root/contracts/fixtures; carefully isolate testroot support. Can author standalone worker using envSQL and current installed package/public contracts with persisted metadata input; actual independently installed process steps, not mocked service clients.

## Next implementation boundaries (b complete; c design refinement in journal doc)

Read BP-07.04 Supervisor journal.md, physical/exchange designs and supervision_journal/README.md. Pure RequestFrame stores original request, Runtime preparer and canonical observation bytes/base64; reconstructs exact footprint/request. RequestSeries1..16 validates lineage/root/parent, unique engagements, same actors/decision/checkpoint/footprint/context bindings, monotonic cuts and narrowing actions/limits/deadlines. Required entries retained except prior declaration constraint; B2 still validates admitted policy. Hashes are not auth.

B1.03b forward runtime0018 after0017; preserve all old migrations, no old migrators after head. Producer must reconstruct actual graph/plan/node membership, paths, kind/status/state/output under existing run lock; prove active ancestors and no materialized activation row. Configured Runtime/Planning actors, never caller delegation. Atomic request/origin/outbox, exact replay/conflict, own immutable SELECT/INSERT history and narrow mutable control grants. Leases do not authorize paid calls or graph effects. No SQL across network. CommandStore terminal accepted means storage only; public supervisor receipt recorded. New receipt routes must not widen old parsers. B1.04 transports; B2 admission-pinned checkpoint policy and conditional winner/effects.

## Persistent rules

Continue across milestones, commits, pushes and compaction until concrete blocker. No subagents/JARVIS/v1 edits. Commentary every60s. No source/test/dev/source-adjacent README edits during verification. SQL serial opt-in retained fixture; no reset or old migrators. Future-only receipt corrections, no active repinning. Weak science remains visible; no blanket quality veto. Live provider/model/egress/spend unselected blocks only actual calls. Private declarationv2 correction already approved/implemented.

## Environment and lookup

Root Z:/mvp20-split; activev2, PowerShell. Python v2/dev/.venv/Scripts/python.exe; uv v2/.venv/Scripts/uv.exe. PYTHONUTF8=1 each Python call. Windows absolute(),notresolve(). Normal Ruff discovery. Secrets env-only. Git safe.directory=//DesktopNAS/Code/mvp20-split; main; commit/push authorized. Tracker docs/Build Plans/BP-07/BP-07.04 Durable supervisor and races.md; parent BP-07 Autonomous LLM Campaign Supervision.md; MBT max25rows; BP-07 Planning History.md.

Planning0.69/public0.9/DB0014 (never<=0.65migrators), Research0.34/public0.14/DB0013 (never<=0.33), Data0.29/DB0012 (never<=0.25), Knowledge0.18/public0.8, Registry0.1. No active skills/goals/subagents. v1/LICENSE metadata debt untouched.

Independent exchange installs .test-results/supervision-exchange-independent-20261005/initial/environment and replacement have Runtime0.23/supervision0.2, no private peers;265initial/105replacement,162 unchanged predecessor files,520 old schemas and7 exact Windows checkout-filter vectors. Root.gitattributes LF rule preserves public fixture hashes. PriorRuntime0.20.2 runtime-domain-receipt-peer-20261002/environment. CurrentPlanning final .test-results/planning-campaign-final-20261005/initial/environment and replacement0.69; BP-07.03 archived100%,Final_Installation.json1262initial/49replacement. Actual-owner/crash/rights/compiler/semantic/catalog evidence under docs/Audits/Evidence/BP-07-Campaigns. New supervisor evidence under BP-07-Supervisor. Inspect helper versions before any migrations.
