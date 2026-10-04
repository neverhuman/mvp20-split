# Knowledge and Scientific Reasoning

- Document role: intended domain architecture; not an implemented code-module contract
- Design status: target architecture; bounded typed authoring/replay, finite reasoning, future-only receipts and scoped exploration implemented; model extraction and scientific validation remain successor scope
- Last reviewed: `2026-10-04 01:40:15` (America/Chicago)
- Parent: [Master Architecture](../../../Architecture.md)

## Scope and Ownership

Owns domain entities, accepted assertions, contradictions, applicability and symbolic reasoning. Humans author knowledge in text; graph structure represents reviewed meaning.

## Integration Boundary

Consumes Data evidence references and Research observations; supplies pinned assertions and reasoning to Campaigns and Agents. Owns assertion promotion; Platform enforces reviewer identity and audit durability.

## Domain Coordination

Authoring owns the document-to-graph proposal and accepted revision lifecycle. Reasoning owns assertion applicability, rule execution, evidence authority and derivations. A published graph revision is a consistent scientific context; a projection selects a bounded, authorized part of that context for a particular consumer. Projection refresh is not an unreviewed knowledge edit.

Inputs include authored text, experimental observations and source-bound claim proposals. Outputs include approved revisions, scoped constraints, explanations, unresolved contradictions and affected-consumer notices. Data stores raw source artifacts; Knowledge stores their reviewed scientific meaning and references. LLM extraction can identify a candidate relationship but does not make it a scientific fact.

Entity identity, assertion revision and source-document revision must remain separate. A corrected identity mapping may change multiple relationships, which is why conflict checks include semantic dependencies rather than only changed record IDs. Domain history preserves what each campaign actually knew.

## Immediate Children

- [Text Authoring and Graph Revisions](Authoring.md)
- [Reasoning and Evidence Authority](Reasoning.md)

## Delegation Rule

This summary owns domain responsibilities and integration boundaries. Its children own focused behavior and verification. Navigate one level at a time; do not duplicate child implementation details here. Cross-domain contracts name their owner rather than replicating its rules. Children inherit revision pinning, least privilege, explicit uncertainty and provenance from the master principles.
