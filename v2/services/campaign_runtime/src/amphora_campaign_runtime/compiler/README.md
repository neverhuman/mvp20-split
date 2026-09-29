# Executable campaign compiler

- Status: BP-04.01 complete and audited; boundary evidence retained in the [owning plan](../../../../../docs/Build%20Plans/BP-04/Completed/BP-04.01%20Compiler%20and%20executable%20contract.md).
- Owner: Campaign Runtime. Architecture: [Graph Execution Model](../../../../../docs/Architecture/System/Graph_Execution_Model.md).
- Public wire boundary: campaigns 0.3.0, executable wire v2/v3. Existing v1/v2 schemas and plan identity are unchanged. BP-04.03 owns the await extension; the completed predecessor stays closed.

## Responsibilities and interfaces

`compile_campaign(ExecutableCampaign, ToolCatalog, SchemaCatalog)` returns an immutable `ExecutionPlan` or raises `CompilationError` with one bounded, reason-coded finding. It has no network, filesystem, database, environment, capacity or execution side effects. Each call owns its temporary analysis; no mutable global compilation cache exists. A failure never publishes a partial plan.

The same entry accepts `ExecutableCampaignV3` and returns `ExecutionPlanV3` with separate definition/compiler/plan profiles. Await nodes require an artifact subject and output shape, using the same local source resolution and exact schema pinning. Issuer/purpose/revision/timeout pins participate in semantic identity; the compiler never calls an issuer or accepts evidence. Nested scatter/loop bodies retain the same scope rules. The independently specified v3 plan fixture is compared exactly, and 116 predecessor schema hashes remain frozen. Runtime v3 execution and issuer/Artifact replacement acceptance subsequently passed BP-04.03.

Runtime 0.8.0 adds `ExecutableCampaignV4`/`ExecutionPlanV4` and the separate compiler/plan `v3` profiles. `bindings.py` owns finite Artifact projection and object materialization interface checks. Mode, source availability, pinned schema path, unit, collection/resource bounds and field identities are checked without I/O; complete actual payload validation remains the execution boundary. Named materialization fields sort canonically; collection order remains significant. [Independent fixtures](../../../../../contracts/fixtures/v4/README.md) and compiler tests assert exact scopes/ports/order while preserving all 134 earlier schema artifacts. Wire-v4 Runtime admission is deliberately disabled until BP-04.04A/B2; graph-page-v3 DTO publication does not imply an installed route.

The caller supplies public `ReleaseDescriptor`/`LockEntry` pairs and exact schema bytes. `ResolvedTool` verifies the documented Registry descriptor hash and port/checkpoint lock identities. `PinnedSchema` verifies exact bytes, a bounded Draft 2020-12 document and local JSON-pointer references; it never fetches a URI. Catalogs resolve exact identities and reject duplicate entries. These checks establish immutable compatibility, not live availability, scientific eligibility or permission to run. The initial profile accepts pure synthetic tools with required outputs; optional tool outputs await an explicit missing-value contract and are rejected; no external-effect or scientific-authority execution claim follows.

| Module | Owned behavior |
|---|---|
| `compiler.py` | Scope compilation, node policies, used-pin closure and complexity limits |
| `topology.py` | Deterministic DAG order and control-dependent value availability |
| `resolution.py`, `shapes.py` | Local bindings, types/units/bounds and finite predicate checks |
| `catalog.py`, `schemas.py` | Exact public descriptor/schema identity and conservative projection typing |
| `normalization.py` | Immutable domain projections, canonical definition/plan hashes |
| `addresses.py` | Plan-bound loop/scatter activation identities |

## Control and data rules

Each scope is a DAG with exactly one Finish. Nodes without incoming control edges are roots. Every non-Finish node has an outgoing edge; Branch has exactly one true and one false route. Ordinary multi-predecessor nodes require all predecessors. Alternative branch routes must converge through an explicit Join. Source references are local to the enclosing scope; nested bodies receive explicit state/item/capture inputs and return declared ports.

An ordinary binding may consume only an output guaranteed by its incoming control paths. Join members may name control ancestors that can be skipped or missing. A node after a join cannot bypass the collection to consume an alternative branch's output. Required unconditional all-join members retain their guaranteed availability. Members are ordered, uniquely identified and type-compatible. Optional members and partial joins require typed missing slots. Partial policy declares minimum and either all-terminal closure or an explicit deadline; reaching the minimum alone does not close a join.

Scatter requires a bounded collection without unresolved missing slots, an item input, explicit captures, compatible child result and sufficient output bound. Zero-member all collection is valid. The later interpreter must freeze actual membership/order from committed input before issuing work, then preserve that order across completion races. Compile-time bounds are not a capacity reservation. Iteration requires explicit initial state, matching body input, compatible feedback ports and a finite maximum; termination sees named body results. No implicit cycles, parameter packing, coercion, unit conversion, arbitrary expression or hidden scope capture is supported.

Predicates use constant/compare/all/any/not only, at most 256 operations and depth 16. Scalars match declared type and units; integer may flow into number. Ordered comparisons are numeric. Artifact projections require application/json and an unambiguous scalar schema path; unions/conditionals/reference siblings that could change the projected type are conservatively rejected. Optional properties/indexes can still be absent in actual payloads: the interpreter must return an explicit missing-value disposition, never silently coerce or choose false. Schema type checking does not read or validate an artifact's content.

Definitions have at most 4096 total nodes, 1024 scopes, depth 16, 256 used tools and 512 schemas, in addition to wire limits. Findings truncate locations to 256 characters. The compiler validates all branches/bodies, including statically false paths, so latent incompatible work cannot hide behind a predicate.

## Identity and replacement

Canonical JSON uses sorted keys, compact separators, ASCII escaping and finite numbers. Named ports/bindings, nodes, edges, state slots, context pins and lock entries are sorted; ordered join members and predicate operands retain authored order. The definition hash covers `{profile: amphora-executable-definition-v2, definition: normalized-definition}`. The plan hash covers the complete canonical `PlanDocument`, excluding its envelope hash. Semantic edits produce a new identity; presentation data is outside this contract.

`ActivationAddress.for_plan(plan, path)` checks every nested occurrence kind/index and target node. Its key hashes the plan digest and complete wire path under `amphora-activation-address-v1`; scatter paths include a committed membership digest. An address does not establish that membership exists or grant an attempt, fence or budget. A caller must supply a trusted compiled plan, not an unverified hand-built hash envelope.

No persistence or migration is introduced here. Replacing this module must preserve accepted normalized bytes, hashes, scoped bindings and failure dispositions, or explicitly version the compiler profile. Retained old plans must never be silently recompiled with new semantics. Dependencies are Python, public contracts and jsonschema; no Registry/tool private code or scientific library is imported.

## Verification and remaining gates

Owned tests: `services/campaign_runtime/tests/compiler`; selector `dev/run_tests.py --module runtime --area compiler`. Runtime source/test ownership remains registered in `dev/test_scopes.json`. Manual wire examples predate this compiler; the numerical plan is compared byte-for-byte as an independent oracle. Public numeric descriptor/schema fixture bytes are retained under `tests/fixtures/compiler`, not generated by the compiler.

B3: 111 focused cases pass; compiler-only coverage extracted from the Runtime owner report is 573/573 statements and 144/144 branches (100% each). This is scoped code coverage, not exhaustive state-space or scientific proof. The whole Runtime denominator includes unrelated unexecuted lifecycle modules and is not a compiler coverage score. A 52-case independently authored rejection matrix covers control, binding, pin, policy, scope and wire-limit failures; every semantic rejection is followed by a successful original-plan compilation to detect contamination. Positive cases preserve parallel AND paths, all-join availability, partial missingness, zero scatter, explicit captures, checkpoint mapping, typed artifact projection and plan-bound occurrences. Manual scope-order oracles and the pre-existing numerical plan establish expected output independently of compiler algorithms. Ordered member/context edits affect identity; irrelevant named-map ordering does not.

V1 passed: five plans against actual public Registry and both installed tools, fresh compiler/Registry replacement, retained receipts/plans and stable exact history after drain. See [owned installed acceptance](../../../tests/compiler/acceptance/README.md) and [audit](../../../../../docs/Audits/BP-04.01_Compiler_Closeout.md), scope 498bc3389bca4a96b0d7f7690bd39577. No capacity or dispatch authority was fabricated. Interpreter persistence, predicate evaluation, aggregate terminalization, actual scatter freezing, scheduling/recovery and executable HTTP admission remain subsequent child gates. No general execution API is enabled by this module.

BP-04.04A B1 focused verification (`2026-09-29 13:20:55`): 142 compiler tests passed; scoped compiler coverage 664/668 statements and 172/174 branches. The twenty binding cases include manual port/order oracles, incompatible collection types/bounds, scalar fields, empty arrays and reference manifests with explicit missing slots. Remaining uncovered binding branches are single-Artifact materialization and inline Artifact schema compatibility; actual assembled payload validation/publication remains B2 and failure/replacement proof B3/V1. Prior B3/V1 evidence above belongs to the closed compiler child, not to the new execution profile.
