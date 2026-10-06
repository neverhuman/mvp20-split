# Numeric evolutionary search boundary

- Owner: BP-08.01/B2.02 verified; initial seeded state next.
- Scope: finite continuous numerical search primitives; independent Python implementation, not a verified v1 port.
- Design: [Search](../../docs/Architecture/Campaigns/Search.md); [activation](../../docs/Audits/BP-08.01_Activation.md).

CandidateScore owns finite objective/constraint values and an explicit eligibility flag. ObjectiveSpace owns direction, dimensional compatibility, bounded pairwise constrained dominance, Pareto front assignment and normalized crowding. Selection retains every candidate rank and distinguishes requested zero, empty feasible set, insufficient feasible membership and selected results. Unknown/ineligible fitness rejects the whole selection; it never becomes a favorable zero. Feasible-only survivor policy preserves infeasible ranks for explanation. No scientific acceptance follows from a numeric rank.

Input bounds: 1..256 uniquely identified candidates, 1..16 objective dimensions, finite float64 values, nonnegative finite violation, closed minimize/maximize directions. Lower violation dominates higher violation; equally infeasible candidates do not dominate one another through attractive objectives. Feasible Pareto comparison respects each direction. Crowding normalizes each nonconstant axis, uses an explicit boundary flag instead of JSON-incompatible infinity, scales differences to avoid overflow, and breaks ties by candidate ID. Constant axes add no crowding or arbitrary boundary preference. Input order cannot select a different tied candidate.

The module reads no files, SQL, environment, network or global RNG. It owns no graph scheduling, model/source authority, molecular representation, evaluator, tool worker or registry descriptor yet. Public search/checkpoint DTOs are published; checkpoint consistency and seeded candidate state are the next BP-08.01 units; graph-step/standalone worker integration belongs to BP-08.02. Existing synthetic solver tools remain unchanged.

Mathematical reference: [Deb et al., NSGA-II](https://ieeexplore.ieee.org/document/996017). No v1 or external source copied. Exact v1 pins/license observations and Lab placeholder disposition are in [reuse disposition](../../docs/Build%20Plans/BP-08/BP-08.01%20Reuse%20disposition.json). This is constrained Pareto/crowding selection with an explicit feasible-only policy, not a claim to reproduce the v1 SBX/mutation/RNG implementation or scientific benchmarks.

Rebuild acceptance: module-owned tests under tests/ranking cover independent fronts, objective direction, constraint precedence, stable ties, invalid/ineligible/mismatched data, extreme numeric ranges and bounded membership. Preserve result ordering/dispositions or publish a new policy version. Cross-platform or algorithm-performance claims require separate evidence.

Verified2026-10-06 09:37:53:30focused checks13.44s including12ownership/dependency guards. Combinedcoverage98%; exact branches/gaps in Ranking.json. This proves only the pure numerical boundary.

## Original specification and portable random stream

OriginalSearch validates the public SearchSpec again at entry, rejects reversed bounds, duplicate coordinate/objective/implementation identities, blank units and cross-scope or duplicate context references. Its digest binds every original pin, including seed, budgets, evaluator and implementation versions. Resume requires a separately supplied original specification; a checkpoint cannot authorize its own replacement specification. Canonical search-json-v1 bytes are validated DTO JSON with sorted keys, compact separators, UTF-8/ensure_ascii=False, allow_nan=False and no trailing newline. This Python JSON profile is not an RFC 8785 claim.

CounterRandom is immutable. sha256-counter-u53-v1 hashes ASCII `amphora.search/sha256-counter-u53-v1` followed by one zero byte, the decoded 32-byte seed and an unsigned eight-byte big-endian counter. Take the first eight digest bytes as unsigned big-endian, shift right 11, then divide by 2^53. One draw advances the counter by one; the terminal safe-JSON counter 2^53-1 is serializable but cannot draw again. No global state, Python random internals or pickle is involved. Resume verifies the algorithm and original seed. NumericBox consumes one draw per coordinate, including fixed axes, interpolates low+(high-low)*u and clamps floating-point endpoint rounding.

Dependencies are the public search contract closure plus the Python standard library. Algorithm golden vectors were calculated independently using Windows .NET SHA256/UInt64. Tests live in tests/randomness and tests/specification; synthetic specification pins are fixture labels, not scientific authority. Full checkpoint/ancestry validation and cross-installation replay remain subsequent gates.

Verified 2026-10-06 10:04:32: 69 owned/boundary checks in 12.57s; 182/185 statements and 35/36 branches covered (98% combined). Random stream 100%; remaining gaps are ranking empty-front guard and original-spec resume delegate, to be exercised through checkpoint mapping.

## Checkpoint mapping

CheckpointSnapshot validates intrinsic state against a separately supplied OriginalSearch: canonical attempt identities, seed replay, RNG intervals, generation/slot/population membership, duplicate ancestry, exact proposed-to-pending/terminal correspondence, request digests, evaluator/objective/unit/constraint/evidence scope, progress and phase/stop consistency. Selection receipts are recomputed from the frozen evaluated membership; unavailable fitness cannot enter ranking. Stable evaluation IDs are ev- plus the candidate digest. Candidate IDs hash compact JSON [numeric-attempt-v1, original-spec digest, generation, ordinal, operator, float.hex genes, parent IDs, draw start, draw end]; outcome disposition is retained separately. Selection membership hashes the sorted candidate-ID list as compact JSON.

encode/decode are pure transport mapping. They do not prove that evidence or predecessor Artifacts exist, have authorized access, or that a prior Runtime commit accepted a transition. Data/Runtime and BP-08.02 own those checks, predecessor-chain verification, generation transitions and actual tool dispatch. A snapshot with internally consistent pins does not authorize execution. Full variation replay is not implemented yet.

Tests/checkpoint independently constructs a zero-seed candidate, pending request and single-candidate rank, then mutates identities, scope, units, evaluator, budgets and receipts. Initial-state, duplicate/rejection and generation-transition failure branches remain subsequent scoped gates.

Verified 2026-10-06 10:10:34: 99 checks passed in11.90s; 342/367 statements,74/86 branches covered (90% combined). Remaining branches: variation/ancestry/duplicate/rejection, some stop/predecessor paths and ranking empty-front guard; no full-generation recovery claim.
