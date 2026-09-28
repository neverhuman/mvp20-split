# Campaign Definition Contracts

- Status: implemented definition subset; `amphora-contracts-campaigns` 0.1.0 / wire v1
- Architecture: [Graph Execution Model](../../docs/Architecture/System/Graph_Execution_Model.md)

## Behavior and Public Boundary

Public root exports `CampaignDefinition`, `GraphBody`, tagged invoke/branch/join/iterate/finish nodes, edges and a bounded predicate vocabulary. Nested iteration bodies are structured graph scopes with explicit iteration limits. No arbitrary executable expression or Python source is accepted. This first subset models control edges; data-port mapping, scatter, external waits, full scientific compatibility and execution instructions remain BP-04 contract extensions.

Shape validation bounds nodes/edges per scope and rejects unknown versions/tags. Node uniqueness, cycles, predecessor identity, branch routing and terminal structure are semantic checks owned by the runtime's immutable graph objects. Passing the DTO schema alone does not establish an executable graph.

## Dependencies and State

Depends on public core/tool contracts and Pydantic; no runtime or database imports. No I/O, mutable graph store, scientific authority or permissions. Tool bindings are pinned descriptors to resolve later, not callable objects.

## Replacement Contract and Verification

Preserve scope/revision identity, tagged alternatives, strict decoding and schema export/fixture agreement. A new node kind or wire field requires a new compatibility decision; never silently reinterpret stored definitions. Consumers: runtime validation, schema publication and later UI/LLM clients. [Verification](../../dev/README.md) covers strict interchange, invalid tags/unbounded loops and separate runtime semantic tests. No Rust/UI conformance or graph execution is claimed yet.

## Owned Tests

`tests/test_wire.py` owns this package's strict input/serialization and JSON Schema conformance cases using shared language-neutral examples under `contracts/fixtures/v1`. Core additionally checks immutable scope; tools checks version/unknown-field rejection. The suite measures `src/amphora_contracts_campaigns`; schema import coverage alone is not semantic coverage. More schema edge cases remain future contract-change work.

From repository root: `uv run --project v2/dev --locked python v2/dev/run_tests.py --module campaigns --coverage`. Test and coverage reports are written under `v2/.test-results/campaigns/`. Preserve these tests as the package replacement boundary.
