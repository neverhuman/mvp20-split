# Source-derived solver verification

- Owner: BP-04.04; B1 stage/graph and independent installation verified, successor admission B2 and process/installed acceptance B3/V1 remain.
- Reference: [frozen behavior baseline](../fixtures/v1_solver/README.md); [independent traces](../fixtures/v1_solver/expected_traces.json).

`test_v1_baseline.py` checks normalized source hashes, exact native capability-chain order and the historical validation-only scaffold. `test_stage_oracles.py` composes the five pure stage kernels against manually authored zero/two-generation, mutation-rejection and partial/all-failure traces. Neither executes Rust or proves scientific evolution.

`definition.py` authors a separate wire-v4 executable graph. Seed/proposal Artifacts become explicitly published score-request members; graph scatter owns candidate concurrency. A partial all-terminal collection preserves failed slots; explicit materialization constructs the retention tool input. Retention replaces current state, appends cumulative successes and emits one checkpoint. An authored bounded iteration invokes selection/mutation and carries the retained state into the next generation. Zero offspring generations still score and retain the initial population. No tool contains the generation loop or performs graph dispatch.

`test_graph_execution.py` runs actual Runtime/PostgreSQL graph advancement, worker claims/completions and typed bindings, invoking real fixture kernels in process with a labeled scripted Artifact peer. Complete scoring batches finish in descending proposal-index order; independent expected membership/seeds/state/checkpoints remain ordered. Tool failures consume their real invocation budget and all failed populations end truthfully blocked. `catalog.py` pins actual tool schema bytes to explicitly non-deployable test image identities; no such identity is registry/deployment evidence.

Tests remain selectable through `dev/run_tests.py --module runtime --area baseline`. Each stage's schema/CLI/domain tests live under its own tool module. Actual installed tools/Artifact and process-death/successor history proof remain their named acceptance gates. Frozen v1 is read-only; molecule mutation, feasible scientific ranking and optimizer authorization remain unimplemented scientific scope.
