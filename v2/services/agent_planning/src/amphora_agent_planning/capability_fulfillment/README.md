# Capability fulfillment journal

UI-01.08/P3.2 complete, independently qualified. Owns immutable
authorized fulfillment commands, original pending receipts, terminal verification
evidence, the approved HTTP intake and bounded managed verification. Source package
0.127; the immutable serving demo remains unchanged.

FulfillmentJournal.receive requires the distinct fulfill_capabilities grant and
exact authenticated scope/actor. It loads the original captured capability gap
through Planning's existing projection in the same transaction. Missing or foreign
originals cannot be admitted. No model, Registry or Data call occurs at intake.

planning_0026 adds an append-only command table under planning_service SELECT/INSERT.
Identity-based transaction locks serialize duplicate submissions. Exact retry
returns the original pending receipt; changed bytes at the same identity conflict.
The frozen gap is an immutable acceptance-time snapshot, never a second editable
catalog. Restoring a record verifies canonical command, gap, indexes and receipt
digests. A crash before commit leaves no acknowledged request. Separate commands
for the same gap retain separate histories; intake alone never fulfills a gap.

Worker authority is execute_curations for the retained original scope/actor. That
grant cannot submit an owner fulfillment command. Scientific validity, tool
installation, future Runtime eligibility and source permissions are not owned here.

Tests: tests/capability_fulfillment, including actual PostgreSQL duplicate races,
rollback, service-role immutability and corruption rejection. Replacement must
preserve original bytes/receipts and actor isolation. Peer reads must stay outside
transactions when verification is connected.

Architecture: [Planning](../../../../../docs/Architecture/Agents/Planning.md).

planning_0027 adds one immutable terminal verification per original command. Registry
and current Data processing reads happen outside SQL. Known evidence rejection is
retained; transport/integrity failures propagate without inventing acceptance. An
exact already-verified/rejected original recovers before any peer access. A request
transaction lock plus a unique verified-request index admits only the first verified
fulfillment; later competing commands retain rejection and any collected witness.
There is no model call, paid retry, tool installation or scientific promotion.

VerificationWitness retains the exact original report bytes, observed Registry
snapshot and processed Artifact references/digests. Supporting payloads stay with
Data. Capture rechecks all actual processed bytes; replay checks the immutable
attestation's bindings, report digest, exact descriptor/lock and criteria semantics.
This attestation is internal journal evidence, never a caller-supplied public DTO.
The owner's authenticated command endorses the report; its text grants no authority.

Capability GET prefers the immutable verified winner, otherwise the latest submitted
command's pending/rejected result. Submission retry always returns its ORIGINAL
pending receipt. Current source rights, Registry capacity and future compiler/Runtime
eligibility are independent of historical fulfillment. Readiness requires0027; only
an explicit compatible migrator may advance schema. Demo installations stay pinned.

Verification: intake30pass84.58s; acceptance/read regressions56pass with3 replay
parser failures subsequently repaired; final20pass133.59s including witness,
concurrency, rollback, actual process replacement and test ownership. Source JSON
must be restored using strict JSON validation, preserving frozen tuple contracts.

POST /v1/capability-requests/{request_id}/fulfillments requires fulfill_capabilities,
exact path/payload reference and original numeric command.401/403 deny,404 hides
missing/foreign originals,409 conflicts/history inconsistency,422 malformed input;
whole-body limits apply and responses are no-store. Intake never contacts peers.
Configured curation routes install this endpoint; that write grant without explicit
curation configuration fails startup. Successful response is the original pending
receipt even after verification; capability GET owns current winner readback.

FulfillmentWorker scopes keyset discovery to authenticated actor/project and excludes
terminal originals. A bounded turn collects public Registry/Data evidence outside
SQL. Source denial/missing evidence and exact descriptor mismatches produce retained
rejection. Named transient peer failures remain pending; unknown integrity faults
propagate. Discovery wraps fairly over pending commands. CurationPoller alternates
fulfillment and campaign work with idle fallback, at most one non-idle operation per
turn. Shutdown drains the current bounded turn; no new job starts afterward.

Verification has no effectful peer calls. Concurrent workers may repeat bounded
reads, but the original command's unique terminal record and first-winner transaction
lock prevent competing accepted histories. No paid retry, duplicate external write,
or network exactly-once guarantee. A committed terminal result replays before peers;
an outage before commit remains pending and a replacement can re-read it.

Source qualification:56 HTTP/SQL/worker/configuration/process checks182.75s.
Production CLI with scripted public HTTP peers stays pending on Registry503, then
verifies after restart, then reads no peers on another restart. Four public GETs
across those processes, no model calls. Independent installed qualification: capability-installation-20261012a,150pass458.67s;
actual isolated0.127 wheel/public-only dependencies, SQL, HTTP and CLI replacement.
No paid model calls, no real provider keys, serving demo unchanged.
