# Amphora Master Architecture

- Design status: proposed v2 architecture; implementation not claimed
- Last reviewed: `2026-09-22 21:03:27` (America/Chicago)
- Scope: system principles, construction boundary and functional responsibility domains
- Requirement authority: Product_Requirements.md in docs/Architecture

## Purpose

Initial delivery is internal/demo use, one user and one active autonomous campaign on a single server. The engine remains domain-general, with bio-available polymers a likely early application. Human changes apply between campaigns. Modules are deliberately replaceable behind documented, versioned boundaries; implementation detail must not become an accidental cross-module contract.

Amphora turns research objectives into executable, inspectable campaigns across materials, chemistry and biology. People and agents compose reviewed capabilities, compare evidence and revise research pathways without encoding each scientific workflow permanently into the engine. Existing v1 code is a frozen source of selectively reusable components, not the shape of v2.

## Major Principles

1. **Graphs express research.** Campaign graphs define execution; domain graphs represent scientific knowledge. Execution/provenance lineage is derived from actual work. These responsibilities remain distinct.
2. **Capabilities supply behavior.** Typed, scientifically scoped tools are reusable building blocks. Graphs compose them; tools keep the stateless, stateful or asynchronous behavior their function requires.
3. **Humans express intent; models propose structure.** Text is the primary knowledge-authoring surface. LLMs discover available capabilities and propose graphs, hypotheses and changes. Explicit validation and authority govern activation.
4. **Science is context-specific.** Representations, operators, methods and evidence retain domain applicability. Shared infrastructure does not make polymer, small-molecule and biological science interchangeable.
5. **Evidence governs decisions.** Predicted, measured, inferred and reviewed information retain distinct identities, uncertainty and authority. No model, score or successful execution promotes itself.
6. **State is explicit and recoverable.** Immutable revisions, declared state ownership, attributable changes and bounded feedback preserve reproducibility. Working state, retained evidence and derived indexes are different artifacts.
7. **Human interaction is part of the engine.** Users navigate massive context, inspect decisions, compare alternatives, edit graphs and intervene through role-appropriate views.
8. **Authority crosses every boundary.** Tenant, purpose, rights, approval, cost and audit constraints accompany work. Operational health, scientific validity and external qualification are separate claims.
9. **Build in bounded stages.** Architecture owns intent; focused contracts own behavior; implementation plans own sequence and evidence. Technology and service extraction decisions follow contracts and measured needs.

## Immediate Architectural Children

### System Construction

[System Architecture](docs/Architecture/System/System_Architecture.md) defines how the engine is built: a modular control application and durable graph interpreter, separate worker processes, transactional authoritative state, immutable scientific artifacts and rebuildable projections. The user-selected initial deployment is a single server with remote scientific tools where needed. This child owns process topology, execution semantics, consistency protocols and the end-to-end research loop.

### Functional Responsibility Domains

These eight children define scientific/product ownership inside that system; they are not an eight-service deployment map.

| Domain | Owns | Primary output |
|---|---|---|
| [Research](docs/Architecture/Research/Research_Architecture.md) | Intent, candidates, synthesis feasibility and experiments | Reviewed objectives, scientific objects and experimental dispositions |
| [Campaigns](docs/Architecture/Campaigns/Campaign_Architecture.md) | Graph definitions, execution state and evolutionary coordination | Authorized runs, transitions and search decisions |
| [Knowledge](docs/Architecture/Knowledge/Knowledge_Architecture.md) | Text-to-graph meaning, assertions and reasoning | Reviewed domain revisions and scoped reasoning results |
| [Data](docs/Architecture/Data/Data_Architecture.md) | Sources, artifacts, reusable representations and model/data lifecycle | Versioned inputs, retrieval and eligible model artifacts |
| [Capabilities](docs/Architecture/Capabilities/Capability_Architecture.md) | Tool contracts, catalog, invocation boundary and lifecycle | Discoverable, independently validated scientific capabilities |
| [Agents](docs/Architecture/Agents/Agent_Architecture.md) | LLM planning, context and bounded delegated work | Reviewable proposals and attributable task outcomes |
| [Experience](docs/Architecture/Experience/Experience_Architecture.md) | Graph interaction and role workspaces | Inspectable research and attributable human commands |
| [Platform](docs/Architecture/Platform/Platform_Architecture.md) | Identity, operations, integration and audit mechanisms | Enforced authority, durable records and supported service boundaries |

## System Relationships

Research defines the question and eligible decisions. Agents proposes a campaign using Capabilities and relevant Knowledge/Data. Campaigns validates and executes that composition; scientific results return to Research. Reviewed observations may update Knowledge, while evaluated datasets/models and permitted experience support future work through Data. Experience exposes these transitions and human interventions. Platform enforces shared identity, durability, cost and audit guarantees throughout.

These domains are responsibility boundaries, not a mandate for eight deployed services. The campaign is the executable source of truth; agent plans and UI projections must not become rival workflow definitions. No fixed one-way pipeline is imposed on research composition.

## Scope and Navigation Rule

This master links only to its nine immediate architectural children: system construction and eight functional domains. Each child explains its boundary and links to immediate focused contracts. Read deeper only for the responsibility being changed. Detailed schemas, algorithms, vendor choices, phase trackers and acceptance evidence belong below this level or in their owning delivery records, not in this master.

Current implementation posture is planned. Detailed product acceptance remains binding even where a summary omits it; decomposition narrows context, not product scope.
