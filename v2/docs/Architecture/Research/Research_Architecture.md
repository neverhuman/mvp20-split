# Research Lifecycle

- Document role: intended domain architecture; not an implemented code-module contract
- Design status: proposed architecture; implementation not claimed
- Last reviewed: `2026-09-22 18:56:40` (America/Chicago)
- Parent: [Master Architecture](../../../Architecture.md)

## Scope and Ownership

Owns research intent, scientific objects, experimental interpretation and deliverable meaning. Defines what a campaign must establish, not how jobs are scheduled.

## Integration Boundary

Receives objectives and evidence; supplies reviewed decision contracts, candidate identities and experimental dispositions to Campaigns. Uses Knowledge for context and Capabilities for methods.

## Domain Coordination

Intent owns accepted questions and constraints; Candidates owns design/route identity and assessed feasibility; Experiments owns what was actually performed and observed. These records reference one another by immutable revision rather than embedding mutable copies. A single project can contain formulation design, biological assays and historical observations without forcing all work into one candidate type.

The domain exposes reviewed decision contracts, candidate/route assessments, experiment proposals and measurement eligibility decisions. It consumes scientific tool outputs and source artifacts. It delegates execution order and durable job recovery to Campaigns, transport to Data, and broader assertion promotion to Knowledge. Local measurement eligibility, shared scientific knowledge and model promotion are distinct decisions.

The implementation boundary should permit an experiment to exist without a generated candidate, a candidate without a proven route, and a research objective without a manufacturing recipe. A missing relationship is explicit rather than synthesized to satisfy a coatings-shaped schema.

## Immediate Children

- [Intent and Decision Contracts](Intent.md)
- [Candidates and Synthesis](Candidates.md)
- [Experiments and Feedback](Experiments.md)

## Delegation Rule

This summary owns domain responsibilities and integration boundaries. Its children own focused behavior and verification. Navigate one level at a time; do not duplicate child implementation details here. Cross-domain contracts name their owner rather than replicating its rules. Children inherit revision pinning, least privilege, explicit uncertainty and provenance from the master principles.
