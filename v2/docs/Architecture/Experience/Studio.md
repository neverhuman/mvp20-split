# Graph Studio and Interventions

- Design status: BP-05.01 accepted; BP-05.02 topology/navigation/evidence implemented and replacement accepted; authoring and scientific projections remain later scope
- Naming note: component/record/operation names below are proposed logical design, not implemented APIs or selected deployment technology
- Last reviewed: `2026-09-29 22:04:45` (America/Chicago)
- Parent: [Domain overview](Experience_Architecture.md)
- Requirement source: [Product Requirements](../Requirements/Product_Requirements.md#human-graph-studio)

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

[Studio Read-Model and Transport Protocol](Studio_Read_Model_Protocol.md) refines the browser consumer's schema-derived boundary, scoped request ownership, bounded paging and explicit invalidation/resnapshot behavior under BP-05.01.

Edits stay local drafts until submitted with actor, expected revision and intended changes. The owning domain returns accepted revision, validation errors or conflict/rebase information. Optimistic visual feedback must not depict a draft as activated work. Notifications wake refresh; revision-aware reads reconcile missed, duplicate or out-of-order notifications.

Selection and drill-down preserve the same historical snapshot unless the user explicitly changes mode. Execution updates may advance live views while the user compares an older iteration. Show that difference instead of silently replacing the inspected evidence.

## Failure and Boundary Example

A scientist drafts a node change while a campaign runs. The editor preserves the next-campaign draft and displays the active pinned revision; it cannot apply the draft to the running campaign. If an evidence source becomes inaccessible, show a permission/retention-limited reference rather than substitute a different source or reveal restricted metadata.

## Design Basis and Open Decisions

Human Graph Studio requirements define editing, traversal and intervention. [Canvas decision](Studio_Canvas_Decision.md) selects React19.3/React Flow12.12 after the bounded B2 browser comparison. Remaining decisions: production projection/query integration, automatic layout strategy, large-context interaction budgets and representative usability tasks. A fast canvas is not proof that users can understand or safely change the campaign.

## Interaction Reference Patterns

[Research Studio Interaction References](Interaction_References.md) maps the user-supplied ComfyUI, LangGraph/LangSmith Studio, Node-RED, Dagster, Bloom, W&B and MLflow references into Design, Monitor, Explore and Compare modes. The map names prototype tasks and delivery owners while preserving immutable active campaigns, source-first knowledge authoring and evidence-aware comparison.


## Implemented Inspection Boundary

Runtime owns bounded authored topology, instantiated occurrence groups and scoped capability catalog. Studio binds topology, selected detail and output pages to one observed cut; it never infers connections from activation order. Catalog availability does not establish that a particular campaign has predecessor lineage or scientific evidence. Artifact metadata is read from its owner and checked against the exact retained reference.

History pins are deliberately bounded local captures of loaded records: up to8 captures,200 graph nodes and2MiB per capture, explicit omissions, no persistence and no invented historical mutable-frontier endpoint. Immutable completion/lineage/artifact records retain their owner authority. Live revision and fetch time are distinct; local pins stay fixed while live observations advance. Scope/denial clears captured data. Runtime currently emits run_changed, so invalidation is run-scoped; finer affected-node refresh requires a future producer contract.

The source-adjacent [Studio boundary](../../../studio/README.md) owns replacement behavior and evidence links. Scientific property/material/model/knowledge views remain unavailable until actual producers ship; comparison fixtures establish only exact context partitioning and explanation/causality separation. Next-campaign authoring remains BP-05.03.
