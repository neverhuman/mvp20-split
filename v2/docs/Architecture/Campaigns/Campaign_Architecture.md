# Campaign Execution and Evolution

- Document role: intended domain architecture; not an implemented code-module contract
- Design status: proposed architecture; implementation not claimed
- Last reviewed: `2026-09-22 18:56:40` (America/Chicago)
- Parent: [Master Architecture](../../../Architecture.md)

## Scope and Ownership

Owns executable graph revisions, authorized execution state and search coordination. It is the sole authority for campaign topology, execution position and committed run transitions.

## Integration Boundary

Consumes Research objectives, Knowledge projections and Capabilities contracts. Agents proposes work through this boundary; Experience submits commands. Platform supplies persistence and authorization mechanisms.

## Domain Coordination

Definitions owns reviewed executable revisions and activation receipts. Runtime owns attempts, committed state and execution position. Search supplies bounded iterative strategies and graph-change proposals; it consumes Runtime rather than maintaining an independent execution ledger. The definition/run distinction permits many runs of the same revision and preserves prior experiments when definitions evolve.

The domain accepts proposals and version-bound commands, and publishes validation, transition, selection and termination records. Every consequential run update has one authoritative commit path. Tool adapters, agents and user interfaces cannot bypass that path by directly changing a population, branch state or active graph. Platform provides the persistence mechanism; the domain specifies the invariants it must enforce.

A single-process implementation is possible if these contracts remain explicit. Distributed workers add leases/fencing and recovery complexity, not a second source of execution truth. Deployment partitioning must follow measured workload and fault-isolation needs.

## Immediate Children

- [Graph Definitions and Activation](Definitions.md)
- [Runtime State and Recovery](Runtime.md)
- [Evolutionary Search and Experience](Search.md)

## Delegation Rule

This summary owns domain responsibilities and integration boundaries. Its children own focused behavior and verification. Navigate one level at a time; do not duplicate child implementation details here. Cross-domain contracts name their owner rather than replicating its rules. Children inherit revision pinning, least privilege, explicit uncertainty and provenance from the master principles.
