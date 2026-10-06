# Numeric evolutionary search boundary

- Owner: BP-08.01 complete; generation-step integration belongs to BP-08.02.
- Scope: finite continuous numerical search primitives; independent Python implementation, not a verified v1 port.
- Design: [Search](../../docs/Architecture/Campaigns/Search.md); [activation](../../docs/Audits/BP-08.01_Activation.md).

CandidateScore owns finite objective/constraint values and an explicit eligibility flag. ObjectiveSpace owns direction, dimensional compatibility, bounded pairwise constrained dominance, Pareto front assignment and normalized crowding. Selection retains every candidate rank and distinguishes requested zero, empty feasible set, insufficient feasible membership and selected results. Unknown/ineligible fitness rejects the whole selection; it never becomes a favorable zero. Feasible-only survivor policy preserves infeasible ranks for explanation. No scientific acceptance follows from a numeric rank.

Input bounds: 1..256 uniquely identified candidates, 1..16 objective dimensions, finite float64 values, nonnegative finite violation, closed minimize/maximize directions. Lower violation dominates higher violation; equally infeasible candidates do not dominate one another through attractive objectives. Feasible Pareto comparison respects each direction. Crowding normalizes each nonconstant axis, uses an explicit boundary flag instead of JSON-incompatible infinity, scales differences to avoid overflow, and breaks ties by candidate ID. Constant axes add no crowding or arbitrary boundary preference. Input order cannot select a different tied candidate.

The module reads no files, SQL, environment, network or global RNG. It owns no graph scheduling, model/source authority, molecular representation, evaluator, tool worker or registry descriptor yet. Public search/checkpoint DTOs, intrinsic consistency checks and seeded candidate state are implemented; graph-step/standalone worker integration belongs to BP-08.02. Existing synthetic solver tools remain unchanged.

Mathematical reference: [Deb et al., NSGA-II](https://ieeexplore.ieee.org/document/996017). No v1 or external source copied. Exact v1 pins/license observations and Lab placeholder disposition are in [reuse disposition](../../docs/Build%20Plans/BP-08/BP-08.01%20Reuse%20disposition.json). This is constrained Pareto/crowding selection with an explicit feasible-only policy, not a claim to reproduce the v1 SBX/mutation/RNG implementation or scientific benchmarks.

Rebuild acceptance: module-owned tests under tests/ranking cover independent fronts, objective direction, constraint precedence, stable ties, invalid/ineligible/mismatched data, extreme numeric ranges and bounded membership. Preserve result ordering/dispositions or publish a new policy version. Cross-platform or algorithm-performance claims require separate evidence.


## Original specification and portable random stream

OriginalSearch validates the public SearchSpec again at entry, rejects reversed bounds, duplicate coordinate/objective/implementation identities, blank units and cross-scope or duplicate context references. Its digest binds every original pin, including seed, budgets, evaluator and implementation versions. Resume requires a separately supplied original specification; a checkpoint cannot authorize its own replacement specification. Canonical search-json-v1 bytes are validated DTO JSON with sorted keys, compact separators, UTF-8/ensure_ascii=False, allow_nan=False and no trailing newline. This Python JSON profile is not an RFC 8785 claim.

CounterRandom is immutable. sha256-counter-u53-v1 hashes ASCII `amphora.search/sha256-counter-u53-v1` followed by one zero byte, the decoded 32-byte seed and an unsigned eight-byte big-endian counter. Take the first eight digest bytes as unsigned big-endian, shift right 11, then divide by 2^53. One draw advances the counter by one; the terminal safe-JSON counter 2^53-1 is serializable but cannot draw again. No global state, Python random internals or pickle is involved. Resume verifies the algorithm and original seed. NumericBox consumes one draw per coordinate, including fixed axes, interpolates low+(high-low)*u and clamps floating-point endpoint rounding.

Dependencies are the public search contract closure plus the Python standard library. Algorithm golden vectors were calculated independently using Windows .NET SHA256/UInt64. Tests live in tests/randomness and tests/specification; synthetic specification pins are fixture labels, not scientific authority. Cross-installation replay is verified; accepted predecessor-chain and generation-transition verification remain BP-08.02.


## Checkpoint mapping

CheckpointSnapshot validates intrinsic state against a separately supplied OriginalSearch: canonical attempt identities, seed replay, RNG intervals, generation/slot/population membership, duplicate ancestry, exact proposed-to-pending/terminal correspondence, request digests, evaluator/objective/unit/constraint/evidence scope, progress and phase/stop consistency. Selection receipts are recomputed from the frozen evaluated membership; unavailable fitness cannot enter ranking. Stable evaluation IDs are ev- plus the candidate digest. Candidate IDs hash compact JSON [numeric-attempt-v1, original-spec digest, generation, ordinal, operator, float.hex genes, parent IDs, draw start, draw end]; outcome disposition is retained separately. Selection membership hashes the sorted candidate-ID list as compact JSON.

encode/decode are pure transport mapping. They do not prove that evidence or predecessor Artifacts exist, have authorized access, or that a prior Runtime commit accepted a transition. Data/Runtime and BP-08.02 own those checks, predecessor-chain verification, generation transitions and actual tool dispatch. A snapshot with internally consistent pins does not authorize execution. Full variation replay is not implemented yet.

Tests/checkpoint independently constructs a zero-seed candidate, pending request and single-candidate rank, then mutates identities, scope, units, evaluator, budgets and receipts. Initial-state, duplicate/rejection and budget cases are verified; generation-transition failure/recovery belongs to BP-08.02.


## Initial numeric population

InitialPopulation.generate performs one bounded seeding step. It retains exactly population_size attempted samples and one RNG draw per axis per attempt. Unique samples become requests up to the evaluation budget; repeated genes refer to their earlier proposed attempt; budget-limited samples are retained as rejected/evaluation_budget. No request is sent. A zero evaluation budget produces a stopped checkpoint with every rejected attempt preserved. max_generations=0 still permits generation zero; no offspring generation is authorized by that value.

The returned request set is validated against all proposed attempts before exposure. Checkpoint mapping independently verifies initial-population completeness and duplicate/budget dispositions. Two separate Python processes reproduce identical canonical bytes for a 128-member fixture. This is process replay, not yet isolated installation or Runtime recovery.


B3 verified 2026-10-06 10:17:52:129 checks14.10s;426/438 statements and92/98 branches covered (96% combined). Malformed RNG/version/operator/pending identities, false stop reasons, forged ranks, missing attempts and duplicate targets reject. Seven frozen v1 source hashes match; no v1/Rust/Lab source copying or scientific claim. Remaining uncovered paths are future-generation ancestry/predecessor handling and the defensive ranking empty-front guard; generation transition/replay belongs to BP-08.02. Source audit tests/reuse requires the read-only workspace; installed algorithm tests exclude only that source audit.

Replacement verified 2026-10-06 10:22:13: two separately built wheel closures,133 tests each, identical wheel hashes and saved128-member checkpoint. Public JSON Schema consumer accepted the retained bytes; pending identities and the next RNG draw matched after replacement. No private service package, SQL or provider credential was available. [Installed proof](../../docs/Audits/Evidence/BP-08-Search/Installed.json); dev/verify_search_installations.py reproduces this bounded check. Different-version upgrades, target-host portability and accepted Runtime generation replay are separate gates.
