# BP-01A Module Tests and V1 Graph Baseline

## Canonical Tracker

- Status: complete; archived after scoped audit
- Last refreshed: `2026-09-24 09:01:20` (America/Chicago)
- Overall implementation: **100%**; four equally weighted bounded delivery gates, all complete.
- Active phase/task: none; P1-P4 complete.
- Next task: BP-02 decomposition and coherence audit.
- Blockers: none within scope.
- Acceptance: source/structure only; no v1 execution-equivalence claim.
- Return point: BP-02 decomposition and coherence audit.

| Phase | Completion | Gate / evidence |
|---|---:|---|
| P1 Module ownership | 100% | Tests moved to owning packages; runtime sub-suites; scope registry and coverage runner implemented |
| P2 Baseline extraction | 100% | Source-hashed CLI behavior graph and typed campaign scaffold; source/structure checks |
| P3 Boundary documentation | 100% | Module/process/replacement instructions and future parity gates |
| P4 Verification and closeout | 100% | Passing aggregate and granular runs; scoped audit; synchronized trackers and archival |

## Scope and Coherence Review

User-directed bounded successor to closed BP-01; preserves existing contracts and validation-only runtime. Frozen v1 is read-only. Tests follow functional ownership, with dev owning shared verification tooling. Coverage measures exercised implementation, not scientific validity. The CLI source graph is a behavioral reference; synthetic fixture bindings are not registered deployable tools. No durable execution, scientific adapters or BP-02 implementation is introduced. Prerequisite BP-01 is complete. Review recorded `2026-09-24 08:58:00` against local module contracts and Graph Runner/execution design; no conflicting boundary found.

## Phase Gates

P1 requires module-local tests, an explicit source-to-suite registry, selectable runtime sub-suites and line/branch coverage output. P2 requires source hashes/locations, control-flow and scoring-chain extraction, retained state/failure semantics, and a campaign scaffold accepted structurally by existing contracts. P3 requires module README/replacement guidance and BP-04/BP-08 acceptance ownership. P4 requires preserved existing tests, new integrity/ownership tests, aggregate gate, selected suite smokes, scoped drift audit and consistent MBT/Restore. Existing package APIs are unchanged; independent wheel builds were verified by BP-01 and need not be repeated for test/document-only changes.

## Closeout Evidence

`2026-09-24 09:01:20`: 44 tests pass; graph-only 6 and tools-only 15 pass with coverage reports. Foundation lint/boundaries/schema gate passes. Source hashes and scaffold validated; frozen v1 unchanged. [Scoped audit](../../Audits/BP-01A_Test_and_Graph_Baseline_Closeout.md) records 83% combined coverage and remaining successor gates. MBT and Restore synchronized; BP-01 remains closed.
