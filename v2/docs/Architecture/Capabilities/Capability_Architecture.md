# Scientific Capability Platform

- Document role: intended domain architecture; not an implemented code-module contract
- Design status: proposed architecture; implementation not claimed
- Last reviewed: `2026-09-23 09:41:20` (America/Chicago)
- Parent: [Master Architecture](../../../Architecture.md)

## Scope and Ownership

Owns the callable functional universe: tool contracts, eligible versions, discovery, development and retirement. A capability defines behavior; a campaign node binds it to a task.

## Integration Boundary

Exposes compatible contracts to Campaigns and Agents. Research owns questions; Knowledge supplies applicability context; Platform supplies environments and grants. Hidden domain dispatchers must not replace configurable graphs.

## Domain Coordination

Catalog owns capability definitions, immutable versions, eligibility, deployment metadata and lifecycle. Execution owns the public invocation/result boundary and implementation adapters. These responsibilities allow the planner to discover a scientific function independently of how it is packaged or where it runs.

The domain exposes versioned descriptors, compatibility decisions, gap/build requests and typed invocation contracts. It consumes scientific validation evidence, dependency artifacts and operational health. It cannot turn a healthy deployment into scientific authority, or treat a semantic match as proof of valid composition.

Tool implementation, tool deployment and campaign node instance are different identities. One tool version may be installed in several environments or appear many times in one graph with different parameters. Its invocation may produce a structure, dataset, state checkpoint or external job handle; neither a universal score nor one mandatory four-stage behavior is required.

## Immediate Children

- [Catalog and Capability Lifecycle](Catalog.md)
- [Tool Invocation and State Boundaries](Execution.md)
- [Independently Deployable Tool Services](Tool_Services.md)

## Delegation Rule

This summary owns domain responsibilities and integration boundaries. Its children own focused behavior and verification. Navigate one level at a time; do not duplicate child implementation details here. Cross-domain contracts name their owner rather than replicating its rules. Children inherit revision pinning, least privilege, explicit uncertainty and provenance from the master principles.
