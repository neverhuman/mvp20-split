# Graph Execution Model

- Design status: proposed graph machine and execution semantics
- Parent: [System Architecture](System_Architecture.md)
- Scope: how an authored campaign becomes actual computation

## Definition, Compilation and Run

Treat the campaign as a typed program, not a picture or a list of service calls. An authored revision records scientific tool bindings and explicit control constructs. Compilation resolves contracts and dependencies and emits an immutable execution plan with a plan hash. A run binds that plan to approved inputs, budgets, knowledge/context snapshots and current authority.

Compilation is semantic validation and resolution, not generation of arbitrary executable source. Tool code remains reviewed/versioned code. Expressions for branch conditions, parameter binding and stop rules use a constrained typed representation; no unrestricted `eval` field is part of a campaign contract.

| Layer | Identity and content | Owner |
|---|---|---|
| Campaign revision | Stable nodes/edges, parameters, allowed changes, source/review lineage | Graph authoring aggregate |
| Resolved execution plan | Exact tool/contract/model/rule/source bindings, validated operators and plan hash | Compiler/resolver |
| Run | Plan reference, input snapshot, authority/budget and lifecycle | Run aggregate |
| Node activation | Definition-node identity plus iteration/expansion path and input bindings | Interpreter |
| Attempt | Worker claim, fence, grant, seed, state snapshot and deadline | Dispatcher/committer |

## Initial Instruction Set

| Instruction | Executable meaning |
|---|---|
| Invoke | Call one capability contract; route operational and scientific dispositions separately |
| Branch | Evaluate a typed predicate over committed values; choose explicit successors |
| Scatter / collect | Expand a bounded collection into activation paths; collect according to a declared completeness policy |
| Join | Wait for named predecessor conditions; define treatment of skipped, failed and optional inputs |
| Iterate | Maintain a versioned loop-state slot, iteration number, feedback bindings and stop/budget policy |
| Await external | Persist correlation/expected-return policy and suspend until an eligible event arrives |
| Review gate | Wait for an authority-bound decision matching the exact proposal revision |
| Finish | Commit a terminal outcome with outputs, unresolved limitations and stop reason |

These are runtime primitives, not required internal stages of every tool. Composite capabilities resolve to inspectable subplans or a declared opaque external implementation with explicit limits; they cannot hide unbounded orchestration.

## Values, State and Readiness

Within an activation, named output ports are assigned once to typed small values or immutable artifact references. Downstream activations bind those committed outputs, not mutable object pointers. Loops create new activation paths such as `generation[3]/evaluate[candidate-17]`; reusing a definition node does not overwrite its previous invocation.

Loop state is explicit: for example a population checkpoint, RNG state and eligible evaluation set. The interpreter advances the loop by accepting the next state revision against an expected prior revision. Tools may propose that checkpoint but cannot advance the iteration counter themselves.

Readiness depends on committed predecessor dispositions and declared control rules. A selected branch can mark an alternative path skipped; a join must distinguish skipped from missing. Batch selection must declare whether all evaluations, a deadline, or a permitted subset closes the batch. Arrival order cannot accidentally determine scientific policy.

The first compiler profile freezes scatter membership and order from committed inputs. Zero-member all-join returns an empty typed collection. Default joins wait for required members to become terminal; partial joins require an explicit minimum and missing-slot reasons. By default partial evaluation still closes only after all members are terminal; a declared deadline may close a snapshot of eligible committed members. Record that exact cut and missing reasons. Do not implement a first-arrival threshold implicitly. Predicate execution uses a finite typed DSL, not arbitrary eval or model prose. [BP-04 compiler plan](../../Build%20Plans/BP-04/BP-04.01%20Compiler%20and%20executable%20contract.md) owns implementation and compatibility fixtures.

## Graph and Knowledge Changes During Execution

Initial-profile override: human edits are staged for a later campaign and never adopted by an active one, including at an iteration boundary. The review instruction uses eligible automated policy/evaluator decisions; it is not a routine human wait. Missing evidence/authority that cannot be resolved automatically produces an explicit terminal blocked/abstained outcome and next-campaign proposal. External-result waits still suspend/resume normally. Emergency termination/revocation remains available without becoming a live-edit mechanism.

Automatic feedback already permitted by the pinned campaign contract can affect subsequent iterations. Newly human-edited knowledge/configuration remains excluded until a new campaign. Autonomous structural proposals also use the successor execution boundary below; finish/terminate and reconcile the current campaign before admitting another active campaign.

Parameter/feedback updates within a preauthorized envelope enter only at declared boundaries and retain provenance. The initial topology-amendment rule is deliberately simpler: create a new validated plan and a successor run with parent-run identity and an explicit carried-forward artifact/checkpoint mapping. Do not hot-swap instructions under already-dispatched activations. Incompatible carried state is rejected or recomputed.

New knowledge is proposed, reviewed and published separately. A running iteration keeps its pinned projection. At an adoption boundary, record the new projection and affected constraints/evaluations. If changed premises invalidate a selection, require reevaluation or a review disposition before further dependent work.

## Interpreter Loop

[Graph Runner](Graph_Runner.md) owns the coordination/supervision loop around this interpreter: versioned aggregate receipts, scoped failure handling, asynchronous model engagement and stale-proposal checks. Its supervisor uses these instructions and the same committer; it cannot create an alternate execution path outside the pinned graph contract.

1. Read a consistent run frontier and the relevant committed node/state records.
2. Calculate eligible activations using the pinned plan and current authority.
3. In a short transaction, verify run revision and budget, insert unique activations/dispatch intents and record transitions.
4. Dispatch attempts outside the transaction; never keep a database transaction open around scientific work.
5. On accepted completion, bind outputs and reevaluate affected successors.
6. On restart, recover the frontier from committed records rather than from a model transcript or RAM snapshot.

Scientific `ABSTAIN`, control `SKIPPED`, operational `FAILED` and terminal `CANCELLED` are not interchangeable. The plan declares what each permits. Schema/port validation, finite loop bounds, stale output rejection and retained attempts are first implementation gates before automatic topology evolution.

## Initial Behavioral Reference

The [v1 solver fixture](../../../services/campaign_runtime/tests/fixtures/v1_solver/README.md) supplies the initial source-derived execution topology and future parity scenarios. BP-04 first reproduces its orchestration with deterministic synthetic tools, preserving explicit population/history distinctions and error aggregation. Known v1 bugs are documented deviations, not required compatibility. BP-08 owns scientific transformation and selection. The present campaign scaffold proves structural admission only; durable execution and scientific equivalence require later evidence.

## Contract Compatibility Boundary

BP-04.01 separates legacy validation-only CampaignDefinition wire v1 from explicit executable wire v2. The [campaign contract boundary](../../../contracts/campaigns/README.md) documents typed sources, finite predicates, scoped controls and immutable plan/path records. Wire-v2 schema validity does not imply compiler or interpreter acceptance; those retain separate plan gates. Legacy stored definitions require an explicit migration decision and remain non-executable by default. Layout is not part of semantic plan identity.
