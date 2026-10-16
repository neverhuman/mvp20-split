# Architecture Document Guide

Development procedures: [SDLC framework](../sdlc/README.md). Load the relevant topic rather than treating architecture as a coding checklist.

- Last reviewed: `2026-09-23 09:51:08` (America/Chicago)
- Status: decomposed v2 design; runtime implementation pending

## Start Here

This README is navigation only. Named domain `*_Architecture.md` documents describe intended design. Module READMEs beside source describe implemented behavior and service/state boundaries; they are compared with architecture during drift audits.

[Master Architecture](../../Architecture.md) is the high-level entry point. Follow its immediate children to focused contracts. This guide is a document catalog, not an alternate flattened architecture.

The master's System Architecture child is the construction view: physical/logical topology, graph execution machine, storage/transaction boundaries, protocols and worked execution. The eight functional domain children remain responsibility views; they do not define independently deployed services.

[Product Requirements](Requirements/Product_Requirements.md) remains the requirement authority. [Requirements Coverage](Requirements_Coverage.md) maps requirement sections to owners for maintenance and audit; it is not the normal context-loading path. [SDLC framework](../sdlc/README.md) governs plans and closeout audits.

## Supporting and Historical References

High-level specifications and the earlier flat design/history documents now live in [Requirements](Requirements/README.md). The decomposed domain/System folders hold current architecture. This guide, coverage map, artifact source map and code-reuse baseline remain top-level navigation/reference surfaces.

The documents below retain earlier detailed design, source review or historical implementation context. They are supporting references, not competing master architecture documents. Current ownership follows the decomposed hierarchy. Resolve substantive conflicts against Product Requirements and record design changes explicitly rather than assuming a reference is implemented.

- [SDLC framework](../sdlc/README.md) - architecture/module decomposition, canonical plan trackers, phase gates, verification and closeout drift audits.
- [Master Build Tracker](../Build%20Plans/Master%20Build%20Tracker.md) - local program priority and links to canonical execution plans; no v2 implementation plan is active yet.
- [Domain Graph Authoring and Replay](Requirements/Domain_Graph_Authoring_and_Replay.md) - human text decomposition, initial extraction prompt, reviewed graph changes, descriptive and typed history, concurrent edits and atomic rebuild publication.
- [Scientific Tools and Graph Execution](Requirements/Scientific_Tools_and_Graph_Execution.md) - reusable tool versions, graph-node bindings, invocation/state/feedback contracts, hundreds-of-tools discovery, and domain-specific execution-layer migration.
- [Graph Native Research Engine](Requirements/Graph_Native_Research_Engine.md) - earlier integrated design reference for executable campaign graphs, neuro-symbolic domain graphs, evolutionary campaign topology, the semantic module index, and the human Graph Studio.
- [Data Sources and Acquisition](Requirements/Data_Sources_and_Acquisition.md) - domain/product/project source scope, heterogeneous campaign acquisition, versioned artifacts, evidence review, replay, and acceptance gates.
- [Evolutionary Code Reuse Baseline](Evolutionary_Code_Reuse_Baseline.md) - source-level reuse map for the five drug-product proposals, separating implemented search kernels from materials-specific adapters and missing scientific models.
- [Product Requirements](Requirements/Product_Requirements.md) - product mission, users, workflows, non-goals, and acceptance posture.
- [System Parameters](Requirements/System_Parameters.md) - concrete operating parameters the system must represent and enforce.
- [Domain Model](Requirements/Domain_Model.md) - durable entities, relationships, and lifecycle rules.
- [Module and Evidence Architecture](Requirements/Module_and_Evidence_Architecture.md) - specialist modules, evidence bus, authority gates, and audit rules.
- [Genetic Programming Paradigm](Requirements/Genetic_Programming_Paradigm.md) - preferred evolutionary optimization architecture for candidate populations, operators, fitness, and selection.
- [Implementation Architecture](Requirements/Implementation_Architecture.md) - MVP technical architecture, API surface, service boundaries, data store, and scaling path.
- `Artifact_Source_Map.md` - source artifact classification and what each artifact contributes.


Historical coatings/MVP requirement and remediation documents are not activated v2 build plans. PDF exports may predate Markdown updates. Source-artifact classification remains in Artifact_Source_Map.md.
