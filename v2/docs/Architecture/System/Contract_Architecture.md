# Contract Architecture

- Design status: accepted architectural direction; schemas and implementation pending
- Last reviewed: `2026-09-22 20:53:09` (America/Chicago)
- Parent: [System Architecture](System_Architecture.md)
- Scope: typed interchange across API, runtime, capabilities, scientific kernels, knowledge, UI and LLM boundaries

## Architectural Decision

Use Pydantic v2 to author and validate Python boundary contracts. Publish immutable, versioned JSON Schema bundles as the language-neutral interchange definition. API descriptions, frontend transport types and LLM-facing schema projections derive from these owned contracts; consumers must not maintain competing handwritten definitions. This does not require Rust kernels or domain objects to use Python models internally.

Pydantic supports [JSON Schema generation](https://docs.pydantic.dev/latest/concepts/json_schema/). Generated schemas express structural constraints; Python custom validators and scientific policy do not automatically become equivalent validators in other languages. Each published contract therefore includes semantic rules and shared valid/invalid fixtures alongside its schema.

## Contract Families and Ownership

| Family | Semantic owner | Examples |
|---|---|---|
| Scientific values and references | Owning research/data domain; shared publication through contracts | Entity/revision references, quantities with units, representation identity, uncertainty, evidence and artifact references |
| Campaign definitions | Campaign compiler and definition domain | Typed nodes/ports/edges, branches, iteration, tool bindings and compiled-plan manifests |
| Runtime interaction | Runtime application boundary | Invocation, attempt/fence/lease, checkpoint reference, completion, cancellation and command receipt |
| Scientific capabilities | Capability catalog and each reviewed tool | Descriptor, parameter/input/output schemas, applicability and scientific/operational dispositions |
| Knowledge exchange | Knowledge authoring domain | Source spans, proposed assertions, reviewed change sets and graph revisions |
| API and UI projections | Owning application query/command boundary | Commands, read views, pagination, freshness and change notifications |
| LLM proposals | Domain accepting the proposal | Graph proposals, tool requests and knowledge extraction outputs |

Every schema has one named owner and consumers. Keep families decomposed beneath the proposed `contracts/` package; avoid a single growing models file or a universal record with unrelated optional fields. Common primitives have one definition, while domain-specific molecule/sequence/polymer contracts remain explicit. Tagged unions distinguish alternative node, representation and result types.

## Publication and Dependency Direction

The owner maintains Pydantic definitions, contract identity, semantic documentation and compatibility fixtures. A release produces a schema bundle with digest, supported serialization profile and dependencies on exact shared-contract versions. Validation-input and serialization-output schemas must be distinguished where their shapes differ.

OpenAPI describes HTTP operations using these contracts. Frontend transport types are generated from the published API/schema surface; static TypeScript types alone do not validate received data. Rust adapters implement the same wire contract with native types and conformance tests. Generated files are reproducible build artifacts, not a second place to edit contracts.

Domain objects own behavior and invariants. Explicit mappers turn validated boundary records into domain values and produce response/projection records from domain results. Contract models must not import web handlers, persistence sessions, provider SDKs or runtime orchestration. ORM records are a separate persistence concern; neither database schema nor DTO shape substitutes for the domain model.

## Validation and Acceptance Pipeline

```text
Untrusted request / worker result / external observation / LLM proposal
    -> bounded decoding and structural contract validation
    -> domain mapping and semantic/scientific validation
    -> authorization, revision and execution-policy checks
    -> application transaction and durable acceptance
    -> versioned receipt / projection / notification
```

Authentication and basic scope checks occur before expensive processing; authorization and mutable preconditions are rechecked at commit. Pydantic validation is not authority to execute code, accept evidence or modify a graph. Validators must be deterministic and bounded; database queries, model calls and remote scientific checks belong in explicit application/domain stages.

Use strict validation at internal command and invocation boundaries, reject unexpected fields in closed command contracts and define any extensible metadata explicitly. Normalize source-specific data in acquisition adapters, preserving raw input, conversion identity and provenance. Never silently repair scientific units or representations merely to pass validation. [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/) reduces coercion but differs between Python and JSON inputs, so both boundary paths need fixtures.

Structural validity checks required fields, tags, ranges and formats. Semantic validity checks units, representation compatibility, port meaning, graph dependencies and scientific applicability. Transactional acceptance checks live authority, expected revision, budget and attempt fencing. A structurally valid molecule is not necessarily synthesizable; a well-shaped knowledge assertion is not accepted evidence.

Return stable reason codes, safe field paths and the validation stage. Do not expose raw private payloads through validation errors or logs. Bound input size, graph depth, collection length and error output before accepting a contract as safe to process.

## Rust and Other Capability Adapters

The runtime validates an invocation, then a capability adapter maps it to a native Rust/library/subprocess/remote interface. The kernel computes using native types. The adapter maps its output to the pinned result contract, validates it and proposes completion to the runtime committer. Kernel success cannot bypass scientific acceptance, fences or durable publication.

Protocol contracts remain stable across transport choices; selecting JSON Schema does not select a Rust ABI or force every in-process call through JSON. Large populations, structures and tensors use verified artifact references or separately specified binary interfaces. Their manifests bind media/encoding version, dimensions where relevant, representation, units and digest. Define ownership/lifetime rules before adopting shared-memory or zero-copy interfaces.

Shared fixtures cover valid values, omitted versus null fields, unknown tags, units, timestamps, numeric bounds and rejection cases. Specify cross-language numeric fidelity, non-finite value policy, byte encoding and canonicalization before using serialized values for hashes. Do not assume default Pydantic JSON serialization is a canonical hashing protocol.

## LLM and Dynamic Graph Contracts

The capability registry exposes reviewed, versioned schemas and semantic descriptions as the LLM's functional vocabulary. Provider adapters may project that vocabulary into a supported schema subset; record the projection version and revalidate returned proposals against the full engine contract. Structured generation improves shape compliance but does not establish scientific correctness or activation authority.

Tool-specific schemas are resolved from registered identities, never arbitrary executable validators supplied inside a campaign. The graph compiler checks input/output compatibility and explicit conversions against those pinned contracts. Schema compatibility alone cannot establish unit, biological-context or scientific-method compatibility. Unsupported or ambiguous bindings produce a proposal error rather than a guessed conversion.

## Versioning, Replay and Compatibility

Contract identity/version is separate from tool implementation, model, graph and database-migration versions. Invocations, accepted results and checkpoints bind the contracts used to interpret them. Runs retain those bindings across deployment.

Treat changes as compatibility decisions, not merely semantic-version labels. With strict unknown-field rejection, even adding a field can break older consumers. Evaluate producer/consumer direction explicitly; retain compatible readers or explicit version adapters for outstanding runs and external jobs. Reject unsupported versions before dispatch. Never silently reinterpret an old checkpoint with the newest model.

Migrations create new versioned records with source references and conversion provenance; original evidence remains available under retention policy. Canonical serialization and schema digests identify the exact published contract but do not prove scientific equivalence. Update compatibility fixtures when a release changes permitted behavior.

## Architecture Acceptance and Remaining Decisions

The implementation plan must demonstrate reproducible schema publication; Python/Rust conformance; generated UI contract alignment; LLM proposal rejection; meaningful semantic failures; unsupported-version rejection; and reading or explicitly migrating a prior-version checkpoint. Contract tests complement the concurrency/recovery tests owned by runtime architecture.

Still to select: package/build tooling, JSON Schema dialect and supported subset, frontend generation/validation tooling, Rust transport, canonical serialization, supported version window and first concrete schema families. No contract package, schema bundle or runtime implementation is created by this design document.
