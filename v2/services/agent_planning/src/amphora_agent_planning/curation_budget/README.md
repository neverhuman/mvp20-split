# Initial curation qualification allowance

UI-01.08/P2.3a. Planning owns fixed scope-group accounting. Architecture:
../../../../../docs/Architecture/Agents/Planning.md.

One declared qualification scope has at most4 reserved attempts and1000000000
USD nanodollars ($1). Each original request has one attempt, at most262144
conservative input units and8192 output tokens, and at most250000000 reserved
nanodollars. At those token maxima, pinned integer rates require233472000 units.
Underreservation, wrong model/profile/currency or widened limits reject before an
attempt is created. Default scope ceilings remain four/$1.

UI-01.08a owner approval2026-10-12 adds a packaged, immutable release policy for
exact scope internal/owner-records-7e21ca85bd6044198b1585aa2c41d336: six original
slots/$1.50. ceiling.py owns the exact tenant/project match and authorization ID.
Browser input, environment and worker configuration cannot enlarge it. This is a
reviewed one-scope qualification extension, not a general management API. Both v1
and v2 original reservations count; no new profile, process or scope can refund
existing holds. A replacement without the extension fails closed at default caps.

BudgetLedger and DispatchJournal take the curation scope lock before existing
family/request locks. Existing own reservations/policies/primary and late observations
are the durable ledger; no new table or in-memory counter. Exact reservation replay
does not consume another slot. Unissued, failed, unknown and underused reservations
retain their original floors; no refund. Known overage blocks other new reservations
and issuance before settlement. Already-issued history remains recoverable.

Only OpenAI curation-profile histories count; old supervision and deterministic
fixtures retain their original budgets. Namespace claims with wrong schema/model
pins fail policy validation. Queries return at most active ceiling plus one matching
reservations (5default/7approved) to detect overflow. Reservation, dispatch and
read-only allowance reports share ceiling_for. All SQL is Planning-owned; no peer
I/O in a transaction.

The provider adapter separately pins the configured qualification scope. P5 must
declare that scope before any paid call and keep the whole approved group there;
creating another scope is not permission to reset the owner's $1 authorization.
Synthetic tests use distinct fixture scopes with no external provider connection.

Tests: tests/curation_budget. Replacement gates: competing fourth-slot reservations,
exact replay, under/overreservation, unknown hold, primary/late overage before new
issuance, no second physical ticket, legacy budget regressions. This is bounded
local admission accounting, not a guarantee against remote billing anomalies.

UI-01.08b approval2026-10-12 11:04:00 extends only the same exact scope to seven/$1.75 original holds: one additional supported call/$0.25 after offline qualification. Six older holds remain. Default scopes stay four/$1; no refund or reset.

UI-01.08c approved2026-10-12 11:58:32 extends the same exact qualification scope to nine/$2.25 original holds. Seven prior holds remain; at most two new requests/$0.50, stop on success. The second requires a specifically identified repair and offline verification. The dev qualification freezes the first diagnostic request separately; the owner ledger enforces the aggregate ceiling and unchanged per-call bound. All other scopes remain four/$1.

UI-01.08d approved2026-10-12 12:52:13: exact scope now10 originals/$2.55. Only v5 within that exact scope permits16384 output tokens/$0.30 per original; all other profiles retain8192/$0.25, and other scopes retain4/$1. CallCeiling owns this conjunction. Nine earlier holds remain immutable; SQL race tests cover the final slot. No refund/retry.

UI-01.08f: exact reviewed scope extends to11 originals/$2.80; ten prior holds
remain. One new v6 original capped$0.25/8192 output, no retry/refund. Other scopes
unchanged. This does not extend the completed dev isolation probe series.

UI-01.08g approved 2026-10-12 20:03:38: exact scope12/$3.05, all11 prior holds
retained; one new v7 original/$0.25/8192. Other scopes and per-call caps unchanged.

UI-01.08h approved 2026-10-12 20:20:43: exact scope13/$3.30 preserves12 prior holds; one new v8 original/$0.25/8192. Other scopes unchanged; no retries/refunds.

UI-01.08i additional$10 approved 2026-10-12 20:48:00: exact scope53/$13.30, preserving13/$3.30 old holds. At most40 new$0.25 calls,8192 output each; unchanged model/profile and other scopes. Stop on qualification success; no refunded reservations or blind retry.
