# BP-01A Test Ownership and Graph Baseline Closeout

- Status: complete; bounded scope aligned, no blocking drift.
- Reviewed: `2026-09-24 09:01:20` (America/Chicago).
- Scope: module-owned tests, coverage tooling, source-derived v1 graph and tracker rules; uncommitted working tree after `99d219c`.

## Evidence

The foundation gate passed lint, declared dependency boundaries, deterministic schema publication and **44 tests** (39 retained, five new ownership/source checks). Focused runtime graph suite: **6 passed**; tools contract suite: **15 passed**, each with a separate coverage/JUnit report. Aggregate coverage reports **83% combined line/branch coverage** over 527 statements and 186 branches; graph and API each report 90%, admission 70%. Contract declarations report 100%, which does not establish complete schema behavior. Dev runner CLI is covered by command smokes, not inferred as pytest coverage. Missing lines/branches remain visible in ignored local `.test-results` reports; no blanket coverage claim or arbitrary threshold.

Frozen v1 source hashes (normalized LF for checkout portability), ordered native scoring chains, connected extracted topology and the typed two-iteration scaffold pass validation. `git diff --stat -- v1` is empty. Rust was not run; no v1 source was changed. Existing four-package isolated-build evidence remains BP-01's; this task changes tests/dev dependency/docs and adds fixtures, not production package APIs.

## Boundary Assessment

Module suites now live beside their owning packages. Runtime graph, admission, API and source-baseline tests have distinct folders and commands. Dev owns verification helpers and the source-to-suite registry; guards reject orphan/overlapping test ownership. Source denominators remain explicit even for focused suites. README/process/template updates preserve these boundaries during module replacement.

The source graph correctly separates CLI molecule-only execution, sequential capability chains and parallel candidate batches. Mutation/selection limitations and known empty-parent/cancellation differences are explicit. The scaffold has fixture-only placeholder bindings and cannot execute scientific work. BP-03 owns adapters; BP-04 owns orchestration parity and recovery scenarios; BP-08 owns genuine evolutionary/scientific behavior. Those are successor gates, not hidden unfinished BP-01A implementation.

## Follow-ups

Starlette/httpx deprecation remains a nonblocking dev-tool maintenance item. Additional missing behavior branches are owned by future changes to the relevant modules; present coverage is a baseline, not proof of complete correctness. No new user decision is needed. Resume BP-02 decomposition/coherence audit. Canonical plan percentages and MBT mirrors are required at every checkpoint; completed scope is archived at 100% separately from runtime readiness.
