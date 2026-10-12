# Initial curation qualification allowance

UI-01.08/P2.3a. Planning owns fixed scope-group accounting. Architecture:
../../../../../docs/Architecture/Agents/Planning.md.

One declared qualification scope has at most4 reserved attempts and1000000000
USD nanodollars ($1). Each original request has one attempt, at most262144
conservative input units and8192 output tokens, and at most250000000 reserved
nanodollars. At those token maxima, pinned integer rates require233472000 units.
Underreservation, wrong model/profile/currency or widened limits reject before an
attempt is created. There is no operator-configurable larger allowance here.

BudgetLedger and DispatchJournal take the curation scope lock before existing
family/request locks. Existing own reservations/policies/primary and late observations
are the durable ledger; no new table or in-memory counter. Exact reservation replay
does not consume another slot. Unissued, failed, unknown and underused reservations
retain their original floors; no refund. Known overage blocks other new reservations
and issuance before settlement. Already-issued history remains recoverable.

Only OpenAI curation-profile histories count; old supervision and deterministic
fixtures retain their original budgets. Namespace claims with wrong schema/model
pins fail policy validation. Queries return at most5 matching reservations to detect
the four-call ceiling. All SQL is Planning-owned; no peer I/O in a transaction.

The provider adapter separately pins the configured qualification scope. P5 must
declare that scope before any paid call and keep the whole approved group there;
creating another scope is not permission to reset the owner's $1 authorization.
Synthetic tests use distinct fixture scopes with no external provider connection.

Tests: tests/curation_budget. Replacement gates: competing fourth-slot reservations,
exact replay, under/overreservation, unknown hold, primary/late overage before new
issuance, no second physical ticket, legacy budget regressions. This is bounded
local admission accounting, not a guarantee against remote billing anomalies.
