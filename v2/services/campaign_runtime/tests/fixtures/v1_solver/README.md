# V1 Solver Behavior Baseline

- Status: source-pinned reference plus historical scaffold; separate wire-v4 synthetic orchestration verified with Runtime/PostgreSQL and a scripted Artifact peer.
- Reviewed: `2026-09-29 16:59:32` (America/Chicago).
- Owner: Campaign Runtime; BP-04 orchestration parity, BP-03 synthetic adapters, BP-08 scientific search integration.

[behavior_graph.json](behavior_graph.json) records the frozen CLI `run_solver` control flow, source hashes (UTF-8/LF normalized for cross-platform checkout)/line ranges, retained state, failure/cancellation behavior and ordered native scoring chains. Candidate batches run concurrently; modules within a candidate run sequentially. The CLI admits the molecule lane only; formulation and evidence chains are engine alternatives, not reachable CLI solver branches.

```mermaid
flowchart LR
  A[Initialize] --> B[Seed population]
  B --> C[Parallel candidate scoring]
  C --> D[Aggregate / rank / snapshot]
  D --> E{Generation budget}
  E -->|Remaining| F[Select parents]
  F --> G[Mutate proposals]
  G --> H[Parallel candidate scoring]
  H --> I[Retain / rank / checkpoint]
  I --> E
  E -->|Exhausted| J[Finalize archive]
```

[campaign_scaffold.json](campaign_scaffold.json) uses the present CampaignDefinition contract with an explicit two-iteration body. Its invocation bindings use **synthetic fixture-only identity digests**, not deployable image digests. Stages are opaque adapter placeholders; data bindings, candidate scatter/gather, error routes, cancellation and retained-state commits are not implemented by this scaffold. Structural admission must continue returning `executable=false`. Do not register these as real capabilities or claim that matching the scaffold proves matching execution.

## Parity gates for the future runner

| Scenario | Required observable behavior |
|---|---|
| Zero generations | Initial population scored and archived, no offspring iteration |
| Two generations | Deterministic seed schedule; current population replaced, cumulative results retained; one checkpoint per completed generation |
| Partial scoring failure | Preserve request/result association despite completion order; omit failed candidates and record failure |
| Mutation rejection | Record rejection, score accepted proposals only; preserve compacted scoring seed indexing |
| All scoring failed | v2 terminates with a truthful blocked/failed outcome; do not copy v1's possible empty-parent modulo/index panic |
| Capability error | Fail-closed ERROR envelope retains missing authority; other modules still evaluated |
| Cancel between generations | No subsequent dispatch; explicit v2 terminal outcome (v1 returns without normal finalization) |
| Restart after commit | v2 recovers committed frontier without duplicate acceptance; this is a v2 requirement, not observed v1 behavior |

BP-04 must implement deterministic synthetic adapters and assert these outcomes, stage traces, collection membership and event ordering against reviewed fixtures. BP-08 adds genuine scientific transformations/selection with separate evidence. B1 tests now also execute the separate wire-v4 graph from `tests/baseline/definition.py` through actual Runtime transactions; source integrity/scaffold tests remain distinct. No Rust run or scientific parity is claimed.

BP-04.04/B1 now owns [independent expected traces](expected_traces.json). They are manually specified, not runner snapshots. Readable fixture IDs replace native mutation hashes; generation denotes the scoring batch and no molecular structure change is asserted. The equal-rank fixture profile preserves the source's cumulative top-N selection before filtering against current members: an empty intersection triggers fallback, but a partial intersection does not. Rejected proposals retain their original proposal seeds while subsequent scoring seeds use the compacted request index. These files become execution evidence only when the corresponding adapter/graph tests pass.

The frozen `mutate` function changes IDs/lineage without molecular structure changes (`QUARANTINED_NO_STRUCTURE_CHANGE`). `rank_candidates` sets `ranked=false` and has no eligible objective vector. Neither separate authorized molecule generation nor numerical NSGA-II is called by this CLI loop. Preserve these distinctions so the initial graph remains a useful orchestration baseline without turning epoxy-specific internals into engine primitives.
