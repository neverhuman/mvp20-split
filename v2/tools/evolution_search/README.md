# Numeric evolutionary search boundary

- Owner: BP-08.01/B1.01; numeric selection proof verified; public checkpoint contracts verified; original-spec/RNG/domain mapper next.
- Scope: finite continuous numerical search primitives; independent Python implementation, not a verified v1 port.
- Design: [Search](../../docs/Architecture/Campaigns/Search.md); [activation](../../docs/Audits/BP-08.01_Activation.md).

CandidateScore owns finite objective/constraint values and an explicit eligibility flag. ObjectiveSpace owns direction, dimensional compatibility, bounded pairwise constrained dominance, Pareto front assignment and normalized crowding. Selection retains every candidate rank and distinguishes requested zero, empty feasible set, insufficient feasible membership and selected results. Unknown/ineligible fitness rejects the whole selection; it never becomes a favorable zero. Feasible-only survivor policy preserves infeasible ranks for explanation. No scientific acceptance follows from a numeric rank.

Input bounds: 1..256 uniquely identified candidates, 1..16 objective dimensions, finite float64 values, nonnegative finite violation, closed minimize/maximize directions. Lower violation dominates higher violation; equally infeasible candidates do not dominate one another through attractive objectives. Feasible Pareto comparison respects each direction. Crowding normalizes each nonconstant axis, uses an explicit boundary flag instead of JSON-incompatible infinity, scales differences to avoid overflow, and breaks ties by candidate ID. Constant axes add no crowding or arbitrary boundary preference. Input order cannot select a different tied candidate.

The module reads no files, SQL, environment, network or global RNG. It owns no graph scheduling, model/source authority, molecular representation, evaluator, tool worker or registry descriptor yet. Public search/checkpoint DTOs and domain mapper are the next BP-08.01 units; graph-step/standalone worker integration belongs to BP-08.02. Existing synthetic solver tools remain unchanged.

Mathematical reference: [Deb et al., NSGA-II](https://ieeexplore.ieee.org/document/996017). No v1 or external source copied. Exact v1 pins/license observations and Lab placeholder disposition are in [reuse disposition](../../docs/Build%20Plans/BP-08/BP-08.01%20Reuse%20disposition.json). This is constrained Pareto/crowding selection with an explicit feasible-only policy, not a claim to reproduce the v1 SBX/mutation/RNG implementation or scientific benchmarks.

Rebuild acceptance: module-owned tests under tests/ranking cover independent fronts, objective direction, constraint precedence, stable ties, invalid/ineligible/mismatched data, extreme numeric ranges and bounded membership. Preserve result ordering/dispositions or publish a new policy version. Cross-platform or algorithm-performance claims require separate evidence.

Verified2026-10-06 09:37:53:30focused checks13.44s including12ownership/dependency guards. Combinedcoverage98%; exact branches/gaps in Ranking.json. This proves only the pure numerical boundary.
