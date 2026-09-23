# Graph Studio and Interventions

- Design status: detailed proposed contract; implementation and scientific acceptance pending
- Naming note: component/record/operation names below are proposed logical design, not implemented APIs or selected deployment technology
- Last reviewed: `2026-09-22 18:56:40` (America/Chicago)
- Parent: [Domain overview](Experience_Architecture.md)
- Requirement source: [Product Requirements](../Product_Requirements.md#human-graph-studio)

## Owned Contract

Initial profile: live execution is inspectable, while human edits and overrides target the next campaign. Do not offer ordinary controls that modify the active scientific pathway or require a human decision for progress. Clearly separate live/pinned views from next-campaign drafts. Emergency termination is an operational action with recorded effects; broader pause/edit/approval workflows below are future-profile capabilities.

Studio presents campaign definitions, domain knowledge and derived lineage as distinct connected views. Navigate from objectives/nodes to actual inputs, assertions, uncertainty, constraints and decisions. Large graphs use progressive loading, filtering and scoped projections without pretending the entire context fits one screen or model prompt.

Campaign editing exposes typed ports, nested stages, branches, loops, parameters, missing capabilities, validation and revision comparison. Domain authoring centers on source text and plain-language interpretation; expert corrections persist as amendments/overrides. Execution views distinguish live state from pinned historical revisions.

## Boundary and Flow

Views consume authoritative projections. Edits, pause/resume, approvals and amendments are version-bound commands to owning domains. Preview compatibility, evidence and cost impact before activation. Stale commands expose conflicts. Visual positioning is not execution topology unless committed through validation.

## Invariants and Verification

No UI-only mutation of knowledge or run state. Permissions apply to nodes, counts, search and drill-down. Verify users inspect iterations/branches, compare ancestry, trace decisions to assertions and correct knowledge without predicate expertise. Demonstrate navigation and intervention, not merely rendering.

## Component and View Design

| Proposed component | Owned presentation responsibility |
|---|---|
| Graph explorer | Viewport, selection, filters, semantic zoom and loaded subgraph boundaries |
| Revision editor | Local draft changes, validation diagnostics and proposed command payloads |
| Execution inspector | Node/attempt/iteration views over authoritative run projections |
| Evidence navigator | Traversal from decisions to sources, assertions, artifacts and downstream consumers |
| Comparison surface | Definition/state/lineage differences and attributable interventions |

Keep layout coordinates, expansion state and user view preferences separate from scientific graph revisions. Every loaded projection declares graph/run revision, completeness/freshness and access scope. A partial viewport must visibly distinguish unexpanded content from absent relationships.

## Command and Refresh Protocol

Edits stay local drafts until submitted with actor, expected revision and intended changes. The owning domain returns accepted revision, validation errors or conflict/rebase information. Optimistic visual feedback must not depict a draft as activated work. Notifications wake refresh; revision-aware reads reconcile missed, duplicate or out-of-order notifications.

Selection and drill-down preserve the same historical snapshot unless the user explicitly changes mode. Execution updates may advance live views while the user compares an older iteration. Show that difference instead of silently replacing the inspected evidence.

## Failure and Boundary Example

A scientist drafts a node change while a campaign runs. The editor preserves the next-campaign draft and displays the active pinned revision; it cannot apply the draft to the running campaign. If an evidence source becomes inaccessible, show a permission/retention-limited reference rather than substitute a different source or reveal restricted metadata.

## Design Basis and Open Decisions

Human Graph Studio requirements define editing, traversal and intervention. Remaining decisions: graph rendering/layout technology, server projection/query contract, large-context interaction budgets and representative usability tasks. A fast canvas is not proof that users can understand or safely change the campaign.
