# Numeric search graph acceptance

Status: B2 Runtime transactions and real Artifact/worker HTTP passed; recovery is B3.

This Runtime-owned fixture composes public numeric and synthetic evaluator CLI descriptors/schemas. No production Runtime dependency on a scientific tool is introduced. Catalog image pins are declared test identities, not built-image evidence.

`definition.py` authors wire-v4 seed, context materialization, pending-request expansion, explicit array-to-Artifact projection, bounded scatter, all-terminal collection, selection and successor iteration. The specification and actual policy Artifact are explicit campaign inputs and loop captures. The policy is a second evaluator input; it is never looked up implicitly. Checkpoint content and its exact source Artifact reference travel together. Scalar stop predicates inspect the collected checkpoint phase. No hidden tool loop exists.

A zero-generation graph still evaluates/selects the initial population. For a positive bound, Runtime's post-body iteration predicate can enter once with an already stopped initial checkpoint. Numeric vary/expand/collect are then bounded no-ops: zero evaluator calls and no RNG advancement. An exhausted graph limit with a non-stopped checkpoint blocks instead of silently claiming search completion. Graph/specification limits must agree in the acceptance fixture.

Collections cap at128, parallel members8, conversion bytes262144. Large otherwise structurally valid search specifications may exceed byte bounds and must fail explicitly; no truncation or capacity claim. Missing member positions remain visible via the partial/all_terminal policy and feed unavailable-fitness handling.

`test_compilation.py` checks0/1/2/10000 bounds, exact repeat plan identity, policy captures/port incompatibility, missing slots and declared bounds. It is pure compiler evidence only: no SQL, actual Artifact authorization, deployed workers, durable generations, process recovery or scientific validity is claimed. Run through dev pytest with --import-mode=importlib.

`test_transactions.py` uses actual PostgreSQL Runtime transactions, numeric/evaluator CLI subprocesses and an explicitly scripted Artifact peer. Five cases cover zero-generation/one-member, two generations with reverse evaluator completion order, zero evaluation budget, fixed duplicates and a failed evaluator. Independent assertions cover draw counts, exact quadratic arithmetic, minimum-fitness selection, final state, evidence binding and zero extra evaluations. This tier does not establish actual Artifact protection or SDK worker HTTP.

Actual independent wheel/API execution is now demonstrated by [acceptance](acceptance/README.md):15 invocations,6evaluations,54confirmed reservations. Scripted transaction tests retain their narrower role.
