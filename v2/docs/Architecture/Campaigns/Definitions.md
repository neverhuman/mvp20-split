# Graph Definitions and Activation

- Design status: logical architecture with implemented draft/validation/admission boundary described below; scientific acceptance remains pending
- Naming note: logical names are design vocabulary; source-adjacent module contracts define implemented APIs and limits
- Last reviewed: `2026-09-22 18:56:40` (America/Chicago)
- Parent: [Domain overview](Campaign_Architecture.md)
- Requirement source: [Product Requirements](../Requirements/Product_Requirements.md#executable-campaign-semantics)

## Owned Contract

[Multistage Process Graphs](Multistage_Process_Graphs.md) defines repeated branching
and convergence, typed intermediates and the distinction between a control join,
a scientific combination and population selection. It is an intended contract and
qualification target, not a claim that the current two-candidate demo exercises it.

Initial-profile specialization: activation/review is automated under configured campaign authority. Human edits are staged for subsequent campaigns. Only one campaign is active; unresolvable authority/evidence gaps produce explicit outcomes rather than mandatory human waits. The general graph language may retain review gates for later operating profiles.

Campaign definitions are immutable revisions containing typed tool bindings, ports, data/control dependencies, conditions, branch/join rules, state declarations, loops, budgets, human gates and termination. CapabilityPlan references that revision and lockfile, never a separate mutable topology. Execution/provenance is derived from runs, not another authored graph.

Activation checks schema, representation/units/ports, termination, dependencies, resources, applicability, evidence and authority. Retain dry-run limitations and required human review. Lockfiles pin tools, schemas, models, sources, rules and knowledge projections. Amendments create descendants while preserving previous run definitions.

## Boundary and Flow

Humans or Agents propose graphs from the available capability universe. Campaigns validates and activates. Capabilities owns callable contracts, Research objectives and Knowledge assertions. Nodes use real tool contracts rather than mandatory input/transform/retain/output slots.

## Invariants and Verification

Declared feedback loops require explicit bounded semantics; accidental cycles and unsatisfiable joins fail validation. Define successor selection and failure routes. Verify branch/loop changes without orchestration edits, diagnostics naming affected nodes/edges and no silent mutation of active runs.

## Component and Object Design

| Proposed component | Owned records and behavior |
|---|---|
| Graph revision aggregate | Node/edge identity, revision ancestry, authored parameters and declared state/control semantics |
| Graph validator | Structural, compatibility, dependency, budget, authority and scientific validation reports |
| Dependency resolver | Exact capability/source/model/rule bindings and lockfile conflict explanations |
| Activation authority | Review receipts and activated immutable graph/lockfile pairing |

Each node has a stable identity within revision lineage and a capability/control kind. Each edge states its semantic role, endpoints, value/condition reference and scope. Loop constructs declare iteration state, entry/exit rules and limits; a bare directed cycle is insufficient. Joins specify required predecessors and how skipped, failed or optional inputs affect readiness.

## Validation and Activation Flow

`Draft -> proposed -> validated -> reviewed -> activated` is a revision workflow. Failed validation produces a report bound to the proposal and dependency snapshot. Editing invalidates affected validation/approval receipts. Activation checks that all receipts still match the exact revision and resolved dependencies; it cannot activate a later edit under an earlier approval.

The validator separates structural acceptance from tool-specific scientific checks and unsupported dry-run capabilities. A replay fixture must identify any external call it substitutes. Activated definitions are immutable; amendment produces a descendant and a proposed adoption point for the run.

## Failure and Boundary Example

A tool replacement has the same JSON shape but different units or authority ceiling. Compatibility fails even if parsing succeeds. A formerly valid tool becomes quarantined between review and activation: policy either rejects new activation or routes to a reviewed substitute; it must not silently re-resolve the lockfile.

## Design Basis and Open Decisions

[Graph Design Reference](../Requirements/Graph_Native_Research_Engine.md) provides authored graph semantics. Remaining decisions: concrete graph schema/version migration, expression language for conditions and bounded topology operators. Conditions must be typed and inspectable rather than unrestricted executable strings.

## Initial Admission Consistency Profile

Structural validation pins immutable draft content and a reviewed tool/schema universe. Current eligibility remains a separate Runtime admission check against exact public Registry observations. Resolve calls happen before the short owner transaction; Runtime rechecks draft head, reviewed universe, observation timestamps, budget and the single-active-campaign guard using its database clock before publication. Accepted eligibility evidence is retained atomically with run/receipt provenance. A terminal admission replay preserves its original outcome rather than consulting changed dependencies.

The initial Registry policy is synthetic-only. Capacity/eligibility observations have bounded freshness and expiry but are not reservations or scientific acceptance. A lifecycle change after observation is not an atomic distributed revocation barrier; Runtime attempt/fence/acceptance authority remains separate. Missing or unusable current evidence rejects new admission. Stronger distributed reservation/revocation guarantees require a separately scoped protocol, not reinterpretation of the current Registry candidate contract.

## Implemented Boundary and Recovery

[Runtime definitions](../../../services/campaign_runtime/src/amphora_campaign_runtime/definitions/README.md) owns immutable revisions, pinned compiler material and atomic draft admission. BP-05.03 verification includes public browser edits, owner permission/revision conflicts, actual Registry eligibility, independent replacement and a process kill between command registration and definition mutation. Explicit same-identity resumption preserves original operation/digest and newer browser work; GET alone does not execute a pending command. No owner tables or private implementation cross the service boundary. [Closeout audit](../../Audits/BP-05.03_Authoring_Closeout.md).
