# Initial checkpoint demo allowance

Owner: Planning, BP-09.03/B1.2. Architecture: [Planning](../../../../../docs/Architecture/Agents/Planning.md).
This fixed private profile limits the dedicated project scope to six reservations and
USD0.50 (500000000 nanodollars), regardless of process/actor restarts. It uses existing
Planning policy, reservation, primary and late-observation journals; no new database
schema, external coordinator, in-memory counter or public DTO. Mixed historical policy
profiles in the selected scope fail closed. Choose the dedicated synthetic demo scope
explicitly; changing to another project does not transfer or erase the old allowance.

One request allows one attempt, at most65536 input-bound units and2048 output tokens,
with the exact checkpoint model/profile and USD accounting. Integer pinned rates require
at least58368000 nanodollars at those maximum limits. All six full reservations total
USD0.350208; unused headroom does not authorize more calls. Operator-reviewed policies
may reserve more conservatively, but never underreserve. Existing fixture/evaluation
profiles bypass this new rule and preserve their original budgets and replay.

`BudgetLedger.reserve` acquires a scope advisory transaction lock before family/request
locks, validates the request policy and reads at most seven immutable scoped reservations.
A new reservation/attempt commits only when both count and money ceilings fit. Replay
returns the original reservation without consuming another slot. `DispatchJournal.issue`
takes the same lock order and checks known overage before a new once-only ticket. No
transaction spans provider I/O. The scoped lock is not acquired by old profiles.

Unknown, failed, unissued and interrupted reservations retain their full floor. Primary
and late usage are reconciled before new work, including observations not yet settled;
overage blocks new reservations/issuances. Existing issued history still recovers. This
does not cancel remote effects or prevent a provider from reporting overage after a
concurrent call has started. It is a conservative local admission ceiling, not a guarantee
of remote billing behavior. Underused calls never refund spend to this initial group.

Private count/cost exhaustion maps to the existing public `accounting_budget_exhausted`
checkpoint completion; attempt history remains truthful, including zero calls. No new
public stop enum or migration. Owner configuration cannot enlarge this profile; a later
budget policy must be explicitly versioned while preserving these histories.

Tests live under `tests/checkpoint_budget/`: actual PostgreSQL contention at the sixth
slot, cumulative money ceiling, underreservation, fresh-object replay, primary/late
overage, unknown-usage floor and pure limit checks. Configured-worker completion/restart
is covered by `tests/checkpoint_openai/`. Tests do not spend money or prove provider efficacy.

Verified `2026-10-07 00:32:46`: 220 affected regressions pass; final focused46 tests pass
with combined new-module coverage114/115 statements,11/12 branches (98.43%). The final
selection omits the legacy bypass, which the earlier broader suite exercised. Independent
Planning0.101 wheel passes114 copied profile/worker/SQL tests; two wheel sets match.
No paid calls or deployed scientific claim.
