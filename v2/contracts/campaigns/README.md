# Campaign Definition Contracts

- Status: `amphora-contracts-campaigns` 0.2.1 exposes unchanged validation-only wire v1 plus executable wire v2; Runtime compiler accepted, durable interpreter gates in progress.
- Architecture: [Graph Execution Model](../../docs/Architecture/System/Graph_Execution_Model.md)

## Behavior and Public Boundary

Public root exports `CampaignDefinition`, `GraphBody`, tagged invoke/branch/join/iterate/finish nodes, edges and a bounded predicate vocabulary. Nested iteration bodies are structured graph scopes with explicit iteration limits. No arbitrary executable expression or Python source is accepted. This first subset models control edges and remains validation-only. The separate [executable boundary](src/amphora_contracts_campaigns/executable/README.md) adds explicit data bindings, finite predicates, join/scatter/loop/state/checkpoint declarations and immutable plan/activation records under wire v2. External waits, scientific acceptance and actual execution remain later Runtime gates.

Shape validation bounds nodes/edges per scope and rejects unknown versions/tags. Node uniqueness, cycles, predecessor identity, branch routing and terminal structure are semantic checks owned by the runtime's immutable graph objects. Passing the DTO schema alone does not establish an executable graph.

## Dependencies and State

Depends on public core/tool contracts and Pydantic; no runtime or database imports. No I/O, mutable graph store, scientific authority or permissions. Tool bindings are pinned descriptors to resolve later, not callable objects.

## Replacement Contract and Verification

Preserve scope/revision identity, tagged alternatives, strict decoding and schema export/fixture agreement. A new node kind or wire field requires a new compatibility decision; never silently reinterpret stored definitions. Consumers: runtime validation, schema publication and later UI/LLM clients. [Verification](../../dev/README.md) covers strict interchange, invalid tags/unbounded loops and separate runtime semantic tests. No Rust/UI conformance or graph execution is claimed yet.

## Owned Tests

`tests/test_wire.py` owns this package's strict input/serialization and JSON Schema conformance cases using shared language-neutral examples under `contracts/fixtures/v1`. Core additionally checks immutable scope; tools checks version/unknown-field rejection. The suite measures `src/amphora_contracts_campaigns`; schema import coverage alone is not semantic coverage. More schema edge cases remain future contract-change work.

From repository root: `uv run --project v2/dev --locked python v2/dev/run_tests.py --module campaigns --coverage`. Test and coverage reports are written under `v2/.test-results/campaigns/`. Preserve these tests as the package replacement boundary.

The B1 executable suite is separately selectable with `--module campaigns --area executable`. It checks strict language-neutral shapes, legacy rejection, versioned publication and frozen values; declarative model coverage is not compiler semantic or execution coverage. The eight new schemas live in `contracts/schemas/v2`; the 102 wire-v1 schemas are unchanged.

B1 checkpoint 2026-09-28 17:40:35: 23 owned tests, 100% of 275 declarative statements (no algorithmic branches); 619 full foundation tests/twelve independent builds and actual REC-01..09 passed. Coverage of DTO declarations is not compiler semantic or runtime execution coverage. Eight wire-v2 schemas published separately; the 102 prior schemas remain byte-identical.

BP-04.02 adds public exports for existing scalar/artifact literal DTOs without changing campaign wire schemas. The graph-runtime package reuses those identities while giving command numbers an explicit decimal-string representation compatible with the unchanged command-v1 fingerprint profile.
