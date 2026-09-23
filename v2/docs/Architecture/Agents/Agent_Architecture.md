# Agent Planning and Bounded Work

- Document role: intended domain architecture; not an implemented code-module contract
- Design status: proposed architecture; implementation not claimed
- Last reviewed: `2026-09-22 18:56:40` (America/Chicago)
- Parent: [Master Architecture](../../../Architecture.md)

## Scope and Ownership

Owns agent definitions, model/prompt context, proposed plans and durable delegated work. LLMs translate and propose; they do not establish scientific authority or replace execution semantics.

## Integration Boundary

Discovers Capabilities, consumes scoped Data/Knowledge and proposes Research/Campaigns contracts. Work bindings map to canonical campaign execution; agent plans cannot become hidden competing topology. Platform grants authority; Experience exposes intervention.

## Domain Coordination

Planning owns scoped context, prompt/model calls and typed proposals. Work owns durable assignment, supervision, task state and escalation. A plan expressed by an LLM is advisory until the owning domain validates and accepts its contract. A task's execution status must reflect committed runtime evidence rather than narrative claims of success.

Agents consume objectives, capability descriptors, artifacts, projections and grants. They emit proposals, bounded tool requests, task results and explanations. Scientific authority remains with reviewed domain policies; permission remains with Platform enforcement. Agent profiles cannot grant themselves broader access to avoid a blocker.

Campaign-bound work maps to campaign run/node identities. Independent support or operational tasks still need durable work and the same authority/recovery principles, but do not require inventing a scientific campaign. The initial shared execution mechanism must define this mapping before introducing separate worker pools or agent-specific queues.

## Immediate Children

- [LLM Planning and Context](Planning.md)
- [Agent Work and Supervision](Work.md)

## Delegation Rule

This summary owns domain responsibilities and integration boundaries. Its children own focused behavior and verification. Navigate one level at a time; do not duplicate child implementation details here. Cross-domain contracts name their owner rather than replicating its rules. Children inherit revision pinning, least privilege, explicit uncertainty and provenance from the master principles.
