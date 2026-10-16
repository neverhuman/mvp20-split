# POP-01 numerical policy and compatibility

- Status: D2 source and independent replacement verified.
- Reviewed: 2026-10-13 21:59:44 America/Chicago.
- Owner: [POP-01.01/E1 D2](../Build%20Plans/POP-01/POP-01.01%20Population%20Execution.md).
- Implementation: Search0.11; population0.5/population-steps0.1 schemas unchanged.
- Source evidence:320 source Search/process/publication tests;740 predecessor schema
  pins. No population Runtime admission/deployment or scientific performance claim.

## Explicit primary-method numerical fixture policy

PrimaryBirthBatch is an explicit policy entry for the first numerical fixture,
not a topology guess for arbitrary scientific graphs. Each unique proposed candidate
reserves one logical evaluation and first-attempt floor for every configured named
method. Optional methods retain their admitted reservation; an unavailable optional
annotation does not itself make the candidate ineligible for fitness.

Every seed/successor birth ordinal consumes its prescribed random interval. A duplicate
links to the first proposed equal gene vector, retains its own birth ID and consumes
no new evaluation. A candidate that cannot fit a whole method set is rejected with
evaluation_budget or attempt_budget, using evaluation exhaustion first when both
apply. A partial budget does not silently remove a method or invent a zero score.
Remaining-capacity changes under the same original specification do not change birth
IDs or future random draws; changing the admitted specification intentionally does.

The helper produces pure proposals. It does not reserve real worker capacity, count
orchestration/retries, prove current counters or estimate arbitrary process expansion.
Those require the admitted graph cost and Runtime's authoritative ledger. Graphs with
several occurrences per method must supply and qualify their own admitted expansion
policy rather than silently use the primary-method helper.

## Selection, missing values and termination

PopulationSelection retains complete eligible/excluded membership and runs the same
constrained feasible-only Pareto/crowding mathematics over the full union. Required
unavailable fitness excludes that candidate with its reason; optional unavailable
annotations and present zero/low-confidence values do not fabricate a failure or
scientific guarantee. Below the pinned minimum-parent count stops; a smaller survivor
set at or above that minimum continues without repeated fake parents.

FitnessFront preserves legacy numerical meaning: compare feasible first-front objective
vectors, not birth IDs. Retained-parent and selected-survivor fronts determine the
stagnation count. Identical values on newly named candidates are unchanged; a changed
front resets the count. The original minimum/maximum directions remain explicit.

SelectedGeneration stop precedence is deterministic: initial insufficient resource
budget before any fitness exists; selection's minimum/feasibility stop; generation
limit; insufficient remaining primary-method evaluation/attempt budget; activation
ceiling; configured unchanged-front limit. Duplicate-only generations consume their
birth draws but no fresh scientific evaluations; they may continue until a pinned
stop condition rather than being misrepresented as newly evaluated work.

## Compatibility and replacement boundary

The old128-member embedded population,256-member selection, numeric checkpoint,
wire schemas and CLI worker behavior stay unchanged. The larger2000-member selection
entry is explicit and has separate rejection oracles; it does not loosen old calls.
CounterRandom, NumericBox and BoxVariation reuse their prior deterministic mathematics.
Schema publication pins all740 predecessor roots, including new D1 records.

The existing replacement harness rebuilds the isolated Search closure twice, runs
copied owner and public contract tests, and compares legacy checkpoint/RNG replay and
wheels. Source-only v1 disposition tests separately verify the frozen reference files;
they neither run v1 as a service nor alter it. New population policy is still pre-
activation engineering work; no accepted population history is migrated or repinned.
Exact installation counts/digests are retained in D2 evidence and owning plan history.

## Remaining gates

D3 supplies combined boundary/semantic oracles across record families, including
aggregate closure limits. D4 supplies the compiled graph, real resource calculation
and transition/write-set review. POP-01.05 remains a proposed public admission
extension; these pure numerical checks cannot enforce campaign-wide concurrency.
Actual dispatch, protected artifacts, producer acceptance and restart stay in E2-E4.

Final proof: two isolated Search0.11 builds326tests EACH, identical wheels and legacy
checkpoint/RNG replay. [Evidence](Evidence/POP-01/Numerical_Policy.json).
