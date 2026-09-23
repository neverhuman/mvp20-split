# Human Research Workspace

- Document role: intended domain architecture; not an implemented code-module contract
- Design status: proposed architecture; implementation not claimed
- Last reviewed: `2026-09-22 18:56:40` (America/Chicago)
- Parent: [Master Architecture](../../../Architecture.md)

## Scope and Ownership

Owns human navigation, authoring, comparison and role-specific interaction. Graph visualization is core: people inspect and shape execution, knowledge and derived lineage.

## Integration Boundary

Reads scoped domain projections and sends version-bound commands to their owners. Owns presentation state, not independent scientific truth, authorization or execution state.

## Domain Coordination

Studio owns graph-specific authoring, navigation and execution inspection. Workspaces owns the role/task composition around those capabilities. They share object references, revision identity, commands and disclosure rules; they do not maintain alternative scientific records for each screen.

Read projections must state scope, revision, completeness and freshness. Commands must carry expected revision and actor context, with accepted/conflict/denied dispositions returned by the owning domain. Local drafts and optimistic feedback are presentation state until committed. This distinction prevents visual graph edits from silently changing active research.

The experience must explain why a result exists, what evidence it used, what is uncertain and what a proposed intervention affects. Accessible nonvisual interaction and source-linked views are required alongside graphical richness. Usability acceptance evaluates real role workflows and large-context reasoning tasks, not only rendering performance.

## Immediate Children

- [Graph Studio and Interventions](Studio.md)
- [Role Workspaces and Deliverables](Workspaces.md)

## Delegation Rule

This summary owns domain responsibilities and integration boundaries. Its children own focused behavior and verification. Navigate one level at a time; do not duplicate child implementation details here. Cross-domain contracts name their owner rather than replicating its rules. Children inherit revision pinning, least privilege, explicit uncertainty and provenance from the master principles.
