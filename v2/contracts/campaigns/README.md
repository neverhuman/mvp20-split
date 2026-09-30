# Campaign Definition Contracts

Package0.4.1 additively exports the existing Occurrence union at the public root for navigation consumers. No wire schema changes.

- Status: `amphora-contracts-campaigns` 0.3.0 preserves wire v1/v2 and adds await-capable wire v3. Runtime compiler supports v3; v3 execution remains gated in BP-04.03.
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

BP-04.03 adds `AwaitV3`, recursive `ExecutableScopeV3`, `ExecutableCampaignV3`, `PlanLockV3`, `PlanDocumentV3` and `ExecutionPlanV3`. `parse_executable_campaign` and `parse_execution_plan` dispatch explicitly by wire version; old roots do not silently accept waits. Unchanged leaf nodes, value/predicate types and wire-v2 ActivationPath are reused. The new schema roots are separately published under `contracts/schemas/v3`; fixtures are `contracts/fixtures/v3/await_cases.json`. An await binds issuer/purpose/revision, an artifact subject and output type, bounded timeout and blocked/abstained timeout disposition. It does not issue a laboratory effect or grant acceptance authority.

Package 0.3.1 additionally exports the existing `AllCollectionPolicy` and `PartialCollectionPolicy` from the public root for Runtime policy validation. Their fields and published schema bytes are unchanged. Graph-runtime 0.2.1 updates its exact campaign-package dependency without changing wire contracts.

Package 0.4.0 adds separately versioned executable wire-v4/profile-v3 roots with `ArtifactProjectV4` and `ArtifactMaterializeV4`, bounded conversion limits and a builtin primitive descriptor. Public parsers dispatch v2/v3/v4; all 134 predecessor schema bytes remain pinned. [Binding fixtures](../fixtures/v4/README.md) define explicit scalar/reference/inline-item projection and named-field materialization, including missing-slot and authority rules. Runtime 0.9.0 executes this boundary only with explicitly configured binding peers under BP-04.04A/B2; default admission remains gated. A DTO or compiled plan is not evidence of executed conversion.
