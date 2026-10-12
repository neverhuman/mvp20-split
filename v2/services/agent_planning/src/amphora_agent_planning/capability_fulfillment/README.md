# Capability fulfillment journal

UI-01.08/P3.2b complete. Owns immutable authorized fulfillment commands, original
pending receipts and terminal verification evidence. Managed processing and the
approved HTTP write route are P3.2c; neither is installed yet.

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
