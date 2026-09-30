# Durable Runtime Command Protocol

- Design status: BP-02 protocol baseline implemented for prepared synthetic invocations; implementation evidence is owned by module READMEs and closeout audits.
- Reviewed: `2026-09-25 13:40:55` (America/Chicago).
- Parent: [State and Consistency](State_and_Consistency.md).
- Owner: Campaign Runtime. [Artifact protocol](Artifact_Publication_Protocol.md) defines the separate publication owner.

## Boundary and Command Identity

The first durable slice admits prepared synthetic invocations only. Arbitrary CampaignDefinition validation still returns `executable=false`; fixture-run readiness is a separate explicitly labeled capability. Synthetic inputs pin scope, fixture plan digest, tool release/schema identities, finite attempt budget and initial checkpoint. Admission enforces one RUNNING campaign for the initial installation. BLOCKED is a terminal execution disposition under the initial requirements: it cannot dispatch or resume, but retains unresolved evidence/reservations. It does not hold the active slot for a later campaign, whose admission cannot settle or revive that predecessor. General compiler/registry activation belongs to BP-03/04.

Proposed public operations: AdmitFixtureRun, ClaimInvocation, RenewAttempt, CompleteInvocation, CancelRun, RevokeWorker and scoped GetRun/GetInvocation/GetCommandReceipt. Commands carry contract family/version, scope, authenticated actor identity, command ID, payload and any client preconditions. Handler policy validates the actor; caller labels do not grant authority. Workers have no database access.

Command uniqueness is `(scope, actor_id, command_family, command_id)`. Store request digest and a durable disposition. Same key/digest returns the same terminal receipt after authorizing receipt access; a different digest returns `command_identity_conflict` even if the original is pending. An in-progress duplicate returns the pending operation identity and may trigger idempotent reconciliation; it never starts another logical operation. Infrastructure failure is retryable and must not be saved as business acceptance. Business rejections are stable receipts; attempting a corrected payload needs a new command ID. Authorization failures before a scope/actor is established are not public durable commands.

### Canonical digest profile 1

Use the validated, schema-versioned command model with defaults materialized. Include family/version, command ID, scope, stable actor ID, payload and supplied semantic preconditions. Exclude the digest field itself, transport credentials, trace IDs and server-derived reservation metadata. Reject duplicate JSON keys before parsing, non-finite numbers, unpaired Unicode surrogates and unsupported fields. Command values are null/bool/bounded integer/string/list/closed object; floating measurements belong in typed artifacts or declared decimal strings. Preserve Unicode code points and array order; do not case-fold, trim or apply Unicode normalization to identities/content.

Encode sorted object keys as compact UTF-8 JSON, ASCII escaping enabled, no whitespace or final newline, integers in decimal without alternate numeric spellings; SHA-256 those bytes. The initial implementation is the Python profile, not an assertion of universal language canonicalization. The command-contract package publishes golden canonical bytes/digests for optional/default fields, escaping, order, nulls, integers and rejected duplicates; any future Rust/JS producer must pass them. Artifact/schema digests retain their separately named profiles.

### Explicit numeric profile 2

BP-05.03 adds the owner-approved `amphora-command-v2` envelope for definition.save and graph.admit_draft. An explicit encoding marker is retained in canonical bytes/digests; unmarked envelopes and other command families retain v1. This closes the authored NumberConstant float versus command-v1 mismatch without reinterpreting historical requests. Runtime NumberValue inputs remain decimal strings.

V2 permits finite binary64 values under strict consuming DTO bounds, rejects overflow/nonzero underflow, retains safe integer tokens, duplicate-key/Unicode/depth/size checks, materializes defaults and normalizes signed zero to positive zero. Python-owned shortest-round-trip JSON float rendering is fixed by public golden vectors, not assumed equivalent to browser JSON.stringify. Runtime stores and verifies the actual profile with immutable canonical bytes; changed profiles under the same identity conflict. Original v1/v2 bytes and receipts must survive restart. Studio emits explicit v2 only for the two opted-in actions and retains the original submission for reconciliation. [Commands boundary](../../../contracts/commands/README.md) owns exact profile rules and fixtures.

## Owned Records and Domain Objects

| Owner record/domain object | Invariant / behavior |
|---|---|
| Run / RunBudget | Scope, immutable fixture plan/input binding, status, revision, budget limit/reserved/spent; one authoritative row serializes consequential transitions |
| Activation / AttemptLease | Stable activation identity; immutable attempt history; strictly increasing fence per activation; lease and worker identity |
| RuntimeCommand / CommandReceipt | Unique request identity/digest, pending or terminal disposition and committed references |
| CompletionIntent | Immutable semantic completion payload digest; bound command/attempt/fence; PREPARED, COMMITTED or ABORTED disposition |
| AcceptedCompletion / StateRevision | At most one accepted result per activation; exact outputs/checkpoint bound to plan, attempt and artifact receipts |
| AuditEvent / OutboxEntry | Persist with the state transition; stable event identity, run revision and ordinal within that transition |

Pydantic validates the wire; focused domain objects own transitions, budget accounting and receipt eligibility. Repositories/mappers own persistence, not DTO constructors. No foreign key or query traverses artifact/research/knowledge private schemas.

## Transition Baseline

| Object / command | Required state | Committed outcome |
|---|---|---|
| AdmitFixtureRun | Eligible immutable synthetic fixture, finite budget, no other nonterminal run | RUNNING run, queued activation(s), command receipt and audit/outbox |
| ClaimInvocation | RUNNING run, eligible QUEUED activation, active worker authority, budget remaining | LEASED attempt, new fence and lease, budget reservation, claim receipt |
| RenewAttempt | Current unexpired LEASED attempt and active run/worker | New bounded lease; same fence; duplicate renewal returns prior receipt |
| Expire/reclaim | Database time at or past lease expiry | Old attempt EXPIRED, its unit settled; eligible pure work QUEUED, then separately claimed with greater fence and another unit |
| CompleteInvocation | RUNNING run, current unexpired attempt, active worker, valid PREPARED intent and protected output references | Terminal attempt/activation, one accepted completion, checkpoint/state change, budget settlement and audit/outbox |
| CancelRun | Nonterminal run | CANCELLED run; queued work cancelled; live attempts revoked/settled; PREPARED intents ABORTED; no new claims |
| RevokeWorker | Authorized local policy command | Durable worker revocation epoch; affected attempts fenced/reconciled before reuse; no new claims for revoked worker |
| Exhausted budget / permanent failure | No permitted further progress | FAILED or BLOCKED terminal run with reason, not indefinite wait |
| All fixture activations accepted terminal | No pending/uncertain work under fixture policy | COMPLETED run; tool abstention remains an abstention, not scientific success |

Attempt terminal dispositions distinguish SUCCEEDED, ABSTAINED, FAILED, EXPIRED, CANCELLED and UNCERTAIN. Invalid completion is a rejected proposal, not necessarily a terminal activation: an eligible current worker can retry with a new command. Retryable failure requeues only under declared bounded pure-tool retry policy; abstention is never silently retried into a score. Initial fixture admission rejects effectful dispatch; a reported uncertain effect freezes automatic retry and yields truthful BLOCKED disposition with diagnostics. Full provider reconciliation is outside BP-02.

Leases use database time, not worker clocks. At exactly the expiry boundary, completion/renewal rejects. Pure computation may continue after lease loss but cannot accept outputs. Initial policy defaults: lease 30 seconds, heartbeat target 10 seconds, maximum 3 issued attempts per activation, maximum lease extension bounded by invocation deadline. These are configurable developer defaults, not measured performance promises; fixtures control time/barriers explicitly.

## Budget and Authority

Budget unit = one issued execution attempt. Claim atomically reserves one unit; `reserved + spent <= limit` always. Every terminal/expired/cancelled issued attempt transfers one reserved unit to spent exactly once; no refund because computation may already have occurred. Reclaim spends another unit. Unclaimed cancellations cost zero; uncertainty retains its reservation until a terminal reconciliation decision settles it. Budget limit and policy are immutable for a run; exhaustion terminates with a reason. Monetary, provider-token and scientific-resource budgets are future policy extensions.

The local authority adapter authenticates server-configured identities/scopes and persists run/worker revocation inside runtime ownership. Configuration is pinned at run admission; mutable revocation records are checked under the transaction lock. A worker cannot self-assert a role or revive a grant. Service-to-service artifact requests have distinct scoped credentials. This is a concrete local policy boundary, not deployment identity or cross-service scientific acceptance. Credential rotation/remote identity adoption requires separate compatibility design.

## Transaction Order and Completion Preparation

Use short PostgreSQL transactions with explicit locks: installation admission guard when required, then run, worker-policy rows, activation, attempt and completion intent; multi-row siblings in stable ID order. Domain mutation and command terminalization occur under the same run lock. Insert the unique command identity first only as a short pending-registration transaction, never hold that registration lock across remote I/O. Domain transactions follow the stated lock order and lock the registered command row last. Reads/preflight cannot waive live rechecks. Worker revocation uses this same order; authority rows are not changed through a separate unsynchronized path. Evaluate the database lease clock after obtaining locks, so time spent waiting cannot admit an expired attempt.

CompleteInvocation first registers the immutable semantic command and PREPARED completion intent under runtime authority. Outside that transaction, request protective artifact reservations bound to the intent and output metadata. There is no digest cycle: command identity binds semantic output references; server-acquired reservation receipts are derived execution metadata, not caller payload. Reenter the runtime transaction, recheck attempt/fence/lease, worker/run authority, expected activation/checkpoint revision, budget and intent state, then atomically accept or reject. ABORTED/COMMITTED intent IDs cannot be repurposed.

Normal independent completions validate activation/checkpoint-specific preconditions rather than demanding the stale global run revision seen at dispatch. Run revisions serialize accepted mutations and identify receipts. A caller that explicitly requires a particular run revision gets a stable conflict if it changed. Serialization/deadlock errors retry the whole transaction at most three times with a bounded retry delay policy (zero delay for the initial local store), reloading state; remote actions stay outside the retry closure. On exhaustion return a retryable infrastructure disposition for the same command, not a false business rejection. Same-command commit-before-response loss returns the existing receipt on retry.

At commit insert accepted output/checkpoint references, settle attempt/budget, advance revision, terminalize intent/command and append audit/outbox together. Outbox delivery is at least once; deduplication uses stable event/operation IDs. Publishing notifications never changes acceptance. Artifact retention confirmation is an outbox operation after acceptance, never a remote call under the run lock.

## Required Race Table

| Race / failure | Required observable outcome | Gate |
|---|---|---|
| Two identical commands | One mutation, identical terminal receipt | T2 fixtures, P2/P5 DB proof |
| Same command identity, different payload | Conflict; first payload remains authoritative | P2/P5 |
| Two workers claim one activation | One current lease/fence; other gets no eligible work | P4 |
| Lease expires then stale completion | Stale attempt rejected; new fence alone can accept | P4/P5 |
| Two valid activations complete concurrently | Both accepted serially if policy allows; unrelated run revision is not a reason to lose work | P5 |
| Cancellation/revocation versus completion | Lock order chooses committed winner; cancellation first prevents later acceptance, completion first remains historical | P4/P5 |
| Two budget spenders at remaining one | One claim; invariant never exceeds finite limit | P4 |
| Crash with PREPARED intent | Reconcile same intent; never create a conflicting semantic command | P3/P6 |
| Commit succeeds, response/notification lost | Existing accepted receipt and outbox recover; no double settlement | P5/P6 |
| Permanent rejection with held reservations | Atomically ABORT intent; artifact release requires authoritative outcome proof | P3/P5 |

## Verification Status

The protocol remains a design contract, not self-evidencing implementation. BP-02 now publishes versioned contracts and module-owned PostgreSQL/concurrency tests, plus independently installed REC-01..09 process recovery/replacement. See [runtime module](../../../services/campaign_runtime/README.md), [recovery runbook](../../../services/campaign_runtime/RECOVERY.md) and [parent closeout](../../Audits/BP-02_Foundation_Closeout.md). A valid schema is not evidence of runtime or scientific acceptance. Cross-language canonicalization, general graph interpretation, scientific validity and target-host power-loss remain their named gates.

The R5 review corrected earlier ?one nonterminal campaign? wording to the requirements' one-active-campaign/terminal-blocked semantics. The implementation prevents dispatch in BLOCKED, preserves unresolved budget/evidence, and permits a distinct successor campaign. No automatic uncertainty settlement or provider reconciliation is implied.
