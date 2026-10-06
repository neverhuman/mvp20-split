# Supervisor journal

Runtime0.31 adds separate CheckpointFrame with private frame.v2 and explicit CheckpointRequest. Original RequestFrame.from_bytes stays v1-only. Pure v2 reconstruction binds named fields, all observation bytes and original Planning context; tampering and profile reinterpretation reject. Journal SQL and delivery still need explicit version dispatch before these frames can be stored. No admission/checkpoint/effect claim.


Implementation: Runtime0.28/runtime0020; immutable frames/series and atomic request/outbox storage under BP-07.04/B1.03a?d, plus fenced delivery history and immutable response recording. Independent installed-process recovery is verified; transports and decision acceptance remain later gates.

`RequestFrame.capture` binds the public supervisor request to original byte-owned Runtime observations and the configured Planning actor. It records the separate preparing Runtime actor. `from_bytes` revalidates the private `runtime-supervision-request-frame.v1` profile, canonical JSON/base64 and all existing request/observation hashes. Limits: 16 MiB per frame, existing 256 KiB request, 256 observations, 1 MiB per observation and 8 MiB combined state/output. Returned documents are fresh projections; bytes own retained state.

`RequestSeries` validates 1–16 immutable frames with exact root/parent hashes, unique Planning engagements, unchanged decision/checkpoint/actors/footprint and nondecreasing Runtime cuts. Context bindings stay fixed; call ceilings, action set and deadline cannot widen. Required entries persist except the prior declaration constraint identified by the original declaration digest. That exception does not authorize a broader declaration; admitted policy validation belongs to B2.

Frames/series have no side effects. The SQL journal has no network effects, signatures, source-rights decisions, provider ledger, scientific authority or graph mutation. Received frames cannot prove actual stored node membership, active ancestors or absence of a materialized worker activation. The SQL producer rederives those facts under the run lock using configured principals. Future-only receipt corrections remain unchanged.

Dependencies are public supervision contracts and local scope/request objects. Tests live in `tests/supervision_journal`; replacement must preserve exact original bytes/hashes and rejection behavior. Future private profiles need retained readers. SQL migration and independent persisted-history cutover remain B1.03b–d.

## Atomic SQL boundary

`RequestJournal(engine, planning_actors)` consumes an operator-configured mapping `(tenant, project, Runtime actor) -> Planning actor`. `prepare(principal, frame, canonical_command)` requires `supervise_prepare`, exact original scope/actors and a canonical numeric-v2 `planning.supervision.request` containing the same request. It takes the existing run lock, returns exact prior records for identical retries, validates the whole bounded series, and inserts the frame and outgoing command in one short transaction. Changed retries conflict; database uniqueness/FK failures roll back both records. No network spans SQL.

`verify_current` loads the retained typed plan and selected concrete nodes. It checks plan/path/kind/scope identities, every active ancestor and issued parent, actual loop iteration or scatter membership, no materialized target activation, unchanged selected observations, nondecreasing global cuts and a DB-clock-valid deadline within the campaign deadline. An unrelated revision does not itself make a request stale. Initial graph admission still materializes ready root tools: B2 must add admitted-policy checkpoints before that step; this journal does not pause execution.

`series` requires scoped `read` and reconstructs frames, commands, lineage and stored index fields. Historical reads do not consult fresh provider/source-processing permission. Recorded retry preserves original timestamps even after run termination; fresh requests still require a running campaign. Service-role permissions on `supervision_requests` and `supervision_outbox` are SELECT/INSERT only. Scoped run/plan, root/parent and outgoing-request foreign keys plus command/engagement uniqueness preserve identity. The outbox contains intent only, not dispatch authority or a public command receipt.

## Migration and acceptance

Runtime0.26 requires forward runtime0019; prior migration bytes are untouched. Explicit migration only, no startup DDL. Never run a Runtime<=0.25 migrator against the new head. Preserve retained original request/outgoing bytes during replacement; do not backfill old campaigns with inferred supervisor history. HTTP remains B1.04 and winner/effects B2.

Verified: 53 journal/migration tests9.96s (33 pure,14 actual journal SQL,6 prior migration cases),236 statements/28 branches100%. Tests include nested scatter/loop origins, stale membership/ancestors, materialization despite reopened status, rollback, exact replay after termination, read-scope/actor enforcement, immutable grants and FK/identity collisions. No concurrency, independent-install, provider-call or accepted graph-effect claim from this gate.

## Delivery and response history

`DeliveryJournal.claim` requires original Runtime holder/scope and `supervise_dispatch`. The database clock grants 1?300 seconds, capped by the original request deadline. Original claim event-ID retries retain exact expiry/fence; a new claim ID is required to reacquire. `observe` validates current holder/fence/expiry before append, except exact existing event retries that return immutable original evidence. Pending, ambiguous and awaiting-readback results release the lease for reconciliation; recorded/rejected outcomes terminate delivery only. A lease never authorizes a paid call, graph effect or a new command identity.

Delivery has 16 claims and an absolute 64-event guard with a reserved terminal event. Normal claim/result cycles hit the tighter 16-claim ceiling first. Each immutable event stores a canonical private evidence profile, submission fingerprint, fence, original receipt operation and verified readback when available. The same outgoing command remains in the immutable outbox. Control rows are created lazily for existing requests; migration fabricates no past delivery. `history` requires scoped read access.

`ResponseJournal.record` accepts only numeric-v2 `runtime.supervision.respond`, the configured original Planning actor and `supervise_respond`. It rebinds exact request/attempt/candidate/capture, registers the original command and atomically inserts the response plus terminal command receipt under the run lock. The private command status is accepted for completed storage; the public receipt is **recorded**, never an accepted graph effect. There are at most64 distinct response records per request; changed response identities/new commands and overflow receive explicit rejection receipts. Late diagnostic responses after run termination remain useful immutable evidence. `response` and `receipt` provide scoped history with read permission even when fresh-response permission is absent. Unknown usage is never converted to zero or refunded here.

runtime0019 adds narrow mutable delivery controls and SELECT/INSERT-only delivery events/responses, with scoped request/outbox/command foreign keys. Responses retain exact capture bytes (up to64KiB), immutable canonical response and original operation ID. No cancellation winner, checkpoint pause, provider-call integration or public HTTP handler is implemented by these classes.

B1.03c proof:65 journal/migration cases20.50s, including26 actual journal SQL cases.486 statements,1 unexecuted;60 branches,1 partial (99% combined). The reserved 64th-event fallback is not reached by normal16-claim cycles; bounded16-claim exhaustion is verified. Initial event closure-variable error was found and fixed; all reruns pass. Lease expiry/fence loss, original operation/readback, response limits, unknown usage, late capture/read permission and atomic response/receipt rollback are verified. Competing processes and independent retained-state replacement are verified below.

## Installed replacement and process evidence

`dev/verify_supervision_journal.py` builds only Runtime's public dependency closure, verifies162 unchanged predecessor production files and111 scope/public-contract cases, and runs33 journal reconstruction cases in each of two isolated installations. `tests/supervision_journal/process_worker.py` is an explicit probe, not part of ordinary pure test collection; SQL credentials are environment-only and cleanup cancels only its unique owned fixture scope.

Seventeen actual processes verify four abrupt exits: after request/outbox inserts before commit; after a lease commits; after a response insert before receipt commit; and after response/receipt commit before the caller retains success. Replacement proves rollback, exact original bytes/hashes/timestamps, current fences and immutable receipts/captures. File barriers release both contenders together: exact root retries converge; conflicting successor commands yield one winner/one conflict; only one live delivery lease wins. History is retained; the database is never reset. No private peer package is installed.

The Planning receipt used by this probe is a deterministic public fixture. This evidence covers actual Runtime/PostgreSQL and process replacement, not Planning HTTP, paid calls, independently authored replacement code, power loss or graph decision acceptance. Those claims retain their owning successor gates.


## Cancellation recording (BP-07.04/B1.04b.ii)

CancellationJournal.record(principal, canonical_command) requires supervise_cancel, original command actor/scope and the original preparing Runtime actor or original Planning actor. It binds the exact retained request/reference and records at most16 cancellation objects per request. It uses the existing command registration and run lock; cancellation and public recorded receipt commit atomically. Exact retries preserve original operation and timestamp; duplicate identity/new command and history overflow retain explicit rejected receipts. cancellation and receipt reads require scoped read rights. Late recording remains possible after run termination. No run/node/decision winner changes, provider cancellation, accounting refund or graph pause is implied; B2 arbitrates effects.

Forward runtime0020 grants SELECT/INSERT only on cancellation history with original request and command foreign keys. Earlier migration bytes remain unchanged. Runtime0.27 requires this head; NEVER run Runtime<=0.26 migrators against it. Stored reconstruction validates original bytes/digest/index fields and actor. Four SQL tests cover both original actors, exact replay after run end, late records, no run status mutation, read-only recovery, receipt rollback, authority, identity conflicts,16-record bound and immutable grants.87 statements10 branches100%. Combined capture/journal/persistence96 cases24.31s. Actual concurrent winner races remain B2/B3; actual installed transport recovery remains B1.04d.


Runtime0.28 response receipt recovery verifies stored profile/hash/original bytes even when the command is pending. The new supervisor HTTP adapter uses this read before any fresh Data capture fetch; immutable storage formats and migrations remain unchanged.
