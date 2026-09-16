# Amphora Architecture Decomposition

This folder decomposes the documents in `Artifacts/` into the parameters of a usable product system.

The starting requirement source is `Artifacts/Amphora_tech overview_Aug 2026 (1).pptx`. The main software architecture sources are `Artifacts/ARCHITECTURE.md.pdf` and `Artifacts/Amphora Platform Architecture.pdf`.

## Document Set

- `Graph_Native_Research_Engine.md` - active architecture direction for executable campaign graphs, neuro-symbolic domain graphs, evolutionary campaign topology, the semantic module index, and the human Graph Studio.
- [Data Sources and Acquisition](Data_Sources_and_Acquisition.md) - domain/product/project source scope, heterogeneous campaign acquisition, versioned artifacts, evidence review, replay, and acceptance gates.
- `Product_Requirements.md` - product mission, users, workflows, non-goals, and acceptance posture.
- `System_Parameters.md` - concrete operating parameters the system must represent and enforce.
- `Domain_Model.md` - durable entities, relationships, and lifecycle rules.
- `Module_and_Evidence_Architecture.md` - specialist modules, evidence bus, authority gates, and audit rules.
- `Genetic_Programming_Paradigm.md` - preferred evolutionary optimization architecture for candidate populations, operators, fitness, and selection.
- `Implementation_Architecture.md` - MVP technical architecture, API surface, service boundaries, data store, and scaling path.
- `Artifact_Source_Map.md` - source artifact classification and what each artifact contributes.

## Active Direction

The engine is graph-native and domain-flexible. Executable campaign graphs define how modules are composed, branched, iterated, retained, and evolved; separate neuro-symbolic domain graphs define the knowledge, mechanisms, evidence, uncertainty, and reasoning boundaries that inform those campaigns. Epoxy remains an important proving domain, but its current pathway is not the fixed shape of the engine.

The canonical reference is [`Graph_Native_Research_Engine.md`](Graph_Native_Research_Engine.md).

## Prior Core Interpretation

Amphora is an R&D operating system and manufacturing compiler for materials. Users define product envelopes, ingredients, formulations, experiments, constraints, and measurements. The system computes physics-derived properties, proposes next formulations, records evidence, and compiles auditable handoff packages for lab validation and eventual manufacturing release.

The existing product material establishes the first manufacturing-oriented proving path:

```text
partner brief -> product envelope -> domain pack -> generate/score/gate -> lab plan -> evidence intake -> next candidates -> manufacturing package
```

The preferred implementation style for candidate generation is the genetic programming paradigm: bounded candidate populations, explicit variation operators, retained rejects and duplicates, evidence-bound fitness components, policy-controlled selection, and lab-feedback-driven next generations. The neuro-symbolic stack should support this loop as the evaluator and trust layer, not replace the evolutionary campaign model.

The system must not treat model output as qualification, procurement approval, safety approval, or legal opinion. Authority is explicit, evidence-bound, and fail-closed.
