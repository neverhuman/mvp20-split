# Campaign compiler journal and dispatch

- Owner: Planning BP-07.03/B2.03a/b/c.i/ii, implemented in Planning0.69; c.iii SQL/HTTP integration and d installed actual-owner/crash proof remain pending.
- Design: [compiler handoff](../../../../../docs/Build%20Plans/BP-07/BP-07.03%20Compiler%20handoff.md).
- Tests: `tests/campaign_dispatch` pure values; `tests/campaign_dispatch_storage` owned persistence; `tests/campaign_dispatch_coordinator` owned SQL with scripted peers. These are separate from actual-owner acceptance.

## Original identities and authority

CompilerSelection retains original Planning actor/attempt, preparation/proposal hashes and bounded declaration/budget/Registry configuration. Stable slot identity excludes generated output and configuration; changed contents conflict at that slot. Runtime owner/actor are configured separately from model data. CompilerHistory reconstructs original preparation, attempt observation, reservation and settlement from Planning-owned immutable rows. Missing history, changed accounting or foreign actor/scope reject. No source-rights or execution grant follows from retained bytes.

CompilerEffect derives exact Runtime save/validate or selected Registry commands. Its canonical1MiB envelope retains selection identity/hash, kind, owner and exact command bytes; public command limits remain256KiB. Save preserves numeric command v2; validate preserves v1. Validation depends on the exact saved receipt/readback. Configuration/payload changes retain operation identity and conflict. Registry check identities remain stable after uncertainty.

CompilerObservation binds exact public receipt/readback to the request and original selection/configuration. Saved, compiled, structural_invalid, rejected, candidate, pending and awaiting_readback remain distinct. Registry receipts do not echo command identity/hash; do not invent that guarantee. Historical candidates retain original expiry and never imply execution admission.

## Owned state and replay

planning0013 stores immutable selections and separate lease control;0014 stores immutable rounds, effects and events plus per-effect position control. Never run Planning<=0.65 migrators against0014. Service histories grant SELECT/INSERT only; UPDATE is confined to control columns. Existing migrations and extraction/public command bytes are unchanged.

CompilerStore uses scoped advisory locks, DB-clock1..300s leases, opaque holders and monotonic fences. Stale/foreign/released holders cannot mutate. CompilerJournal registers one save and one validation and at most16 complete Registry rounds of1..64 original selected tools. Zero-tool graphs have no Registry rounds. A new round requires the previous round to be terminal. Exact retries retain first bytes/timestamps; changed retries conflict. Every mutation checks the final lease fence in the same transaction so expiry rolls back all inserted rows.

CompilerOperations reconstructs indexed identities/digests and replays at most64 events against mutable position control. Prepared begins history; dispatch is intent; uncertain never proves remote absence; blocked retains a bounded reason; observed carries typed owner evidence. Slot64 is reserved for terminal evidence. Corrupted projections fail closed. Read-only reconstruction needs original read authority but no live lease or current processing grant.

The journal caches at most one immutable original context for the exact principal including grants and selection. Mutable progress, leases and rights are never cached. Derived Registry batches use a mutex-protected two-entry cache. Replacement reconstructs from SQL. No database transaction spans a peer call.

## Guarded single-operation step

CompilerDispatcher is configured with the journal, current-input RefreshCollector and bounded Runtime/Registry clients. Their owner/actor identities must match the stored configuration. `step(principal, lease, effect_id, check_id=...)` performs at most one effectful POST and returns DispatchStep with exact operation state, current prerequisites where checked and an explicit pause reason. It acquires no lease itself; caller ownership must already exist. It neither creates a provider call nor activates a campaign.

Runtime reconciles original receipt/readback first. An accepted retained receipt is used to read its exact object without resubmitting. Missing, pending, denied, malformed and unknown reads are different. Committed outcomes can be recovered after current processing denial. Only absent or pending original commands may be sent/replayed after fresh original-origin/current-input and complete selected-tool checks. Zero-tool drafts require no Registry observations. Accepted structural-invalid validation is terminal for that effect, not successful compilation.

Registry has no read-only receipt route. Every resolve/replay requires current processing and relevant-input checks, and retains the same original check after uncertainty. A terminal historical candidate may be read but is not renewed. Runtime preparation rechecks all selected candidates after current-input refresh; transport guards also recheck candidate expiry immediately before send. Large tool sets are not guaranteed to fit a short configured age window; expiry remains explicit.

Each write journals dispatch first and supplies a lease guard before connect/send. CompilerFenceLost propagates as lost local authority, not a peer failure. Local fencing cannot cancel already transmitted writes; successors reconcile original receipts. Recovery and write exchanges each have a bounded20s window; current-input collection retains its separate budgets. Source permission observations are not distributed leases. Positions above61 cannot issue a new POST, leaving room for nonterminal evidence and final terminal recovery. Denied/conflicting/protocol replies stay explicit; transport uncertainty never selects a new command identity.

CompilerPrerequisites constructs CampaignOriginReader/CompilerPreparer internally. There is no caller-provided ready flag. Relevant changed inputs require a future proposal; active pins are not rewritten. Exact Research revision reads do not claim latest-head discovery. Missing/weak/contradictory science remains explicit and is not a blanket quality veto.

## Replacement evidence and limits

Planning0.68:23 owned SQL/scripted-peer cases cover155 statements/50branches in dispatcher/prerequisites,100%;23 isolated SQL cases and198 isolated pure/contract dispatch cases pass. Earlier storage and actual primitive-owner evidence remains in BP-07-Campaigns. These proofs cover original recovery under processing denial, current checks before new writes, Registry uncertainty, pending/negative/malformed outcomes, last-moment expiry and final event capacity. They do not establish actual combined HTTP/process crash recovery, remote fencing, scientific capacity, execution admission or live model quality. A replacement must preserve exact bytes, ownership, bounded histories and these failure oracles.


## Bounded progression

CompilerProgression.advance acquires a300s selection lease and releases it after one invocation. It prepares/replays save and, after exact saved history, validation; CompilerDispatcher reconciles Runtime first. Only when those new-use prerequisites need checks does progression select the next unresolved operation of the latest observed round. Latest-round reads preserve original actor/scope/configuration/read grants. CompilerRound.next_operation owns pending selection; no second check identity is allocated for an unresolved round.

An expired terminal round can start the next deterministic planning-check-N identity, at most16 rounds. Rejected rounds remain explicit unless the caller supplies the Boolean retry_rejected policy; no human approval is required. Busy ownership, lost fences, event exhaustion and round exhaustion return explicit pauses. Unexpected failures propagate while cleanup releases owned authority; an already lost lease is not released again as if it were current. There is no hidden retry loop, campaign activation or silent extension of candidate expiry.

CompilerAdvance retains stage, exact dispatch/round and pause reason. Terminal means a rejected save or a terminal validation effect; a saved draft or individual Registry candidate is not a completed compilation. Repeated terminal reads preserve original history without further peer writes. One invocation performs at most one effectful POST. This bounds work but does not guarantee all selected tools fit a short freshness window; incomplete results stay visible for a subsequent bounded invocation or future proposal.

Planning0.69 progression proof:13 scoped SQL cases,67/68 progression statements and18/18 branches; the unexpected ValueError rethrow during lease release is unexecuted, so statement coverage is99%, not100%.36 installed coordinator SQL cases and198 isolated dispatch cases pass. Timing-independent progression fixtures explicitly use the existing60s maximum-age option with30s capacity observations; separate expiry tests verify rejection. Default5s configuration is unchanged. Real HTTP failure and actual-owner/crash acceptance remain c.iii/d.
