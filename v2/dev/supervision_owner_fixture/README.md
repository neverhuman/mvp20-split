# Supervisor owner fault fixture

- Test-only dev ownership; verified `2026-10-05 16:32:49` (America/Chicago), BP-07.04/B1.04d.ii.

Owner starts only explicit installed local service interpreters, supplies credentials through environment, probes readiness and kills only its owned process on cleanup. Planning uses its supervisor CLI; Runtime/Data use their configured host CLI. Logs are local and never contain intentional credential dumps. No migration/reset or production owner imports in the orchestrator.

LostReplyProxy forwards one bounded original HTTP request to the actual owner. It drops a selected reply only after a200 public recorded receipt arrives, retaining that exact receipt in test memory for comparison. Receipt queries/readbacks forward normally. It never fabricates success, retries or changes command bytes. Replacement changes the configured local target endpoint; original request identities remain unchanged. Sockets/threads close after the proof.

verify_supervision_owners.py uses copied owner-local probes and isolated installations.11 process stages and6 actual owner hosts verify original request/outbox, actual Planning recorded receipt in Runtime delivery history, actual Data upload/capture, response/cancel receipts, two commit-before-drop losses, replacement timestamps/bytes, processing-rights withdrawal/history replay/fresh denial/regrant and scoped cleanup. Runtime probes receive only Runtime SQL; Planning probes only Planning SQL. Synthetic capture and test-owned guards are not an autonomous provider coordinator or execution winner. Runtime0.29/Planning0.72/Data0.29; current schemas already applied. First fixtures required correcting a placeholder schema hash to Data's registered JSON-object profile and a probe column to Planning recorded_at; no production validation was weakened.


B2.01b.iv successor verification targets Runtime0.33/Planning0.75 and explicit checkpoint v2. The Runtime-owned probe authors a small wire-v4 scalar materialization graph with its own pinned fixture schema; the checkpoint is recorded before any binding intent exists. Planning request loss uses /v2/supervision/requests; response/cancel remain their original public families. Existing B1 evidence is historical. Helpers never migrate/reset SQL; require already current0021/0016 and Data0012. Installation verification now checks536 schemas/528 predecessors and includes owned v2 scope/frame/client/intake cases. Current actual manifest passed; verification details below.


Verified 2026-10-05 20:04:57: B2.01b.iv current Runtime0.33/Planning0.75 actual materialization-target exchange passed11 process stages,6 hosts,2 lost replies and original/replacement recovery. Four isolated installs668 cases;40/30 old migration files unchanged. No provider call, SQL reset or execution-winner claim. All owned processes closed. Evidence: docs/Audits/Evidence/BP-07-Supervisor/Checkpoint_Owners.json (relative to v2).
