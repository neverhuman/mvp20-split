# Supervisor journal

Implementation: Runtime0.25/runtime0018; immutable frames/series and atomic request/outbox storage under BP-07.04/B1.03a?b. Leases, delivery history, transports and decision acceptance remain later gates.

`RequestFrame.capture` binds the public supervisor request to original byte-owned Runtime observations and the configured Planning actor. It records the separate preparing Runtime actor. `from_bytes` revalidates the private `runtime-supervision-request-frame.v1` profile, canonical JSON/base64 and all existing request/observation hashes. Limits: 16 MiB per frame, existing 256 KiB request, 256 observations, 1 MiB per observation and 8 MiB combined state/output. Returned documents are fresh projections; bytes own retained state.

`RequestSeries` validates 1–16 immutable frames with exact root/parent hashes, unique Planning engagements, unchanged decision/checkpoint/actors/footprint and nondecreasing Runtime cuts. Context bindings stay fixed; call ceilings, action set and deadline cannot widen. Required entries persist except the prior declaration constraint identified by the original declaration digest. That exception does not authorize a broader declaration; admitted policy validation belongs to B2.

Frames/series have no side effects. The SQL journal has no network effects, signatures, source-rights decisions, provider ledger, scientific authority or graph mutation. Received frames cannot prove actual stored node membership, active ancestors or absence of a materialized worker activation. The SQL producer rederives those facts under the run lock using configured principals. Future-only receipt corrections remain unchanged.

Dependencies are public supervision contracts and local scope/request objects. Tests live in `tests/supervision_journal`; replacement must preserve exact original bytes/hashes and rejection behavior. Future private profiles need retained readers. SQL migration and independent persisted-history cutover remain B1.03b–d.

## Atomic SQL boundary

`RequestJournal(engine, planning_actors)` consumes an operator-configured mapping `(tenant, project, Runtime actor) -> Planning actor`. `prepare(principal, frame, canonical_command)` requires `supervise_prepare`, exact original scope/actors and a canonical numeric-v2 `planning.supervision.request` containing the same request. It takes the existing run lock, returns exact prior records for identical retries, validates the whole bounded series, and inserts the frame and outgoing command in one short transaction. Changed retries conflict; database uniqueness/FK failures roll back both records. No network spans SQL.

`verify_current` loads the retained typed plan and selected concrete nodes. It checks plan/path/kind/scope identities, every active ancestor and issued parent, actual loop iteration or scatter membership, no materialized target activation, unchanged selected observations, nondecreasing global cuts and a DB-clock-valid deadline within the campaign deadline. An unrelated revision does not itself make a request stale. Initial graph admission still materializes ready root tools: B2 must add admitted-policy checkpoints before that step; this journal does not pause execution.

`series` requires scoped `read` and reconstructs frames, commands, lineage and stored index fields. Historical reads do not consult fresh provider/source-processing permission. Recorded retry preserves original timestamps even after run termination; fresh requests still require a running campaign. Service-role permissions on `supervision_requests` and `supervision_outbox` are SELECT/INSERT only. Scoped run/plan, root/parent and outgoing-request foreign keys plus command/engagement uniqueness preserve identity. The outbox contains intent only, not dispatch authority or a public command receipt.

## Migration and acceptance

Runtime0.25 requires forward runtime0018; prior migration bytes are untouched. Explicit migration only, no startup DDL. Never run a Runtime<=0.24 migrator against the new head. Preserve retained original request/outgoing bytes during replacement; do not backfill old campaigns with inferred supervisor history. Leases/events remain B1.03c, independent SQL/process proof d, HTTP B1.04 and winner/effects B2.

Verified: 53 journal/migration tests9.96s (33 pure,14 actual journal SQL,6 prior migration cases),236 statements/28 branches100%. Tests include nested scatter/loop origins, stale membership/ancestors, materialization despite reopened status, rollback, exact replay after termination, read-scope/actor enforcement, immutable grants and FK/identity collisions. No concurrency, independent-install, provider-call or accepted graph-effect claim from this gate.
