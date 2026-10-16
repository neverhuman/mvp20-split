# Authored population composition preflight

Owner: POP-01.01/E2.3. This module is under implementation; complete composition
and batch/cap qualification are not claimed. Search owns this pure authoring
assessment. Runtime alone compiles/adopts plans, admits work and enforces capacity.

The first component bounds the expanded wire-v4 graph: every authored activation,
scope, named tool call, materialization and declared binding budget. Scatter total
work uses max_members; concurrent queued work uses active child scopes. Sequential
iterations multiply work but do not multiply concurrent width. Active-attempt caps
do not reduce the queue bound. Every reachable or potentially unreachable authored
invoke is accounted for; speculative branch pruning is not used. Empty scatters
retain authored binding identity while expanding no child work. Retry budgets
include every counted invocation, not just evaluation methods.

Counts use checked safe integers and a bounded supported scope depth. Await nodes
are outside this first finite numerical composition profile. Positive counts are
not graph admissibility, execution authority, physical throughput or full resource
preflight. A supplied compiled document/definition is hash-checked against an
expected plan hash; the caller must obtain that expectation from its trusted owner
flow. This does not prove admission by itself. Spec/release pins, worker publication/ancestry/envelope and
validation I/O accounting remain to be integrated. Runtime's compiler/owner gates
remain authoritative. No service implementation, network, filesystem or private
state access belongs in this module. Source-owned tests live under tests/composition.

Fifteen focused checks cover nested expansion, serial loop width, batch-dependent
orchestration, queue saturation, retries, empty scatters, binding budgets, branch
conservatism, overflow/depth and compiled-plan identity. Full source401 passes;
independent verification is recorded in the POP-01_Composition_Preflight audit.
