# Catalog and Capability Lifecycle

- Design status: detailed proposed contract; implementation and scientific acceptance pending
- Naming note: component/record/operation names below are proposed logical design, not implemented APIs or selected deployment technology
- Last reviewed: `2026-09-22 18:56:40` (America/Chicago)
- Parent: [Domain overview](Capability_Architecture.md)
- Requirement source: [Product Requirements](../Product_Requirements.md#extensible-capability-node-platform)

## Owned Contract

Distinguish definition, immutable version, deployment, instance, invocation and result. Descriptors declare purpose, contracts, applicability/anti-examples, uncertainty, dependencies, cost, side effects, validation, authority and visualization metadata. Package names alone do not establish a capability.

Resolve project needs through deterministic compatibility/eligibility before semantic retrieval or LLM ranking. CapabilityPlan binds a campaign revision and lockfile with alternatives/rejections. Missing functions become gaps. Domain packs combine reviewed representations, tools, rules and templates without fixing execution pathways.

## Lifecycle and Boundary

Build requests specify method, evidence and acceptance. SDK/harnesses support independent contract tests, isolated evaluation and reproducible packaging. Scientific authority and operational readiness remain independent through evaluated/shadow/limited-active/active promotion. Quarantine, deprecation and retirement retain history and affected consumers. Composite tools expose subgraphs and constituent evidence.

## Invariants and Verification

Adding a supported tool contract needs no core dispatcher edit. Reject missing/conflicting dependencies, incompatible ports/profiles and double-counted evidence. Verify at least 300 representative descriptors under declared matching/latency/prompt budgets; catalog scale does not establish 300 validated scientific tools.

## Component and Object Design

| Proposed component | Owned records and behavior |
|---|---|
| Capability registry | Stable semantic identity and immutable versions/descriptors |
| Compatibility resolver | Port, representation, method, scope, dependency and authority matching |
| Deployment inventory | Installed version, profile support, capacity and health, separate from scientific authority |
| Gap/build workflow | Unmet need, method/evidence plan, scaffold/evaluation and review artifacts |
| Lifecycle authority | Publication, quarantine, deprecation, migration and retained replay eligibility |

A capability version binds implementation digest, public contracts, model/rule/data dependencies, evaluation packet and authority ceiling. A deployment is an environment-specific installation of that version. Alias resolution happens before lockfile creation; runtime must not use a floating alias as a scientific dependency.

## Matching and Registration Flow

A capability need specifies the scientific question, typed inputs, required outputs and decision authority. Deterministic filtering produces eligible versions and reason-coded rejections. Semantic ranking helps choose among eligible alternatives. Composition can satisfy a need only if all constituent evidence and compatibility requirements survive the boundary.

A new tool enters as draft, then evaluated, shadow/limited-active and active according to policy. Signed packaging, integration tests and scientific validation contribute different evidence. Registration does not automatically deploy, activate or grant ranking authority.

## Failure and Boundary Example

A descriptor claims biological applicability but its validation packet covers only epoxy formulations. The scientific eligibility decision rejects that use even if port schemas parse. A dependency is withdrawn: determine affected versions and lockfiles, quarantine new use as required, and preserve historical metadata without silently substituting a newer method.

## Design Basis and Open Decisions

[Tool Specification](../Scientific_Tools_and_Graph_Execution.md) defines the semantic invocation contract. Remaining choices: package format, compatibility version rules, trust roots and descriptor-index implementation. The 300-descriptor acceptance fixture tests discovery and boundaries, not scientific readiness of a large tool fleet.
