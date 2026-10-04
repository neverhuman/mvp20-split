# LLM Planning and Context

- Design status: pure context/attempt identity and deterministic provider boundary implemented; durable orchestration, live model evaluation and scientific acceptance remain pending
- Naming note: component/record/operation names below are proposed logical design, not implemented APIs or selected deployment technology
- Last reviewed: `2026-10-04 02:00:10` (America/Chicago)
- Parent: [Domain overview](Agent_Architecture.md)
- Requirement source: [Product Requirements](../Requirements/Product_Requirements.md#llm-prompt-integration)

## Owned Contract

Planning requests bind approved objectives, source/context references, allowed capabilities, reviewed constraints, relevant knowledge, budgets and gates. Context assembly is scoped/versioned. Retain prompt/model/configuration and actual outputs with access controls; bounded retrieval supplies large-context material without treating transcript summaries as authority.

LLMs propose envelopes, knowledge changes, hypotheses, graphs, tools, experiments and explanations. Validators reject invented capabilities, incompatible contracts and unsupported authority. The functional universe is discoverable from the registry, without a fixed four-stage node template.

## Boundary and Flow

Research owns envelope acceptance; Knowledge assertion acceptance; Campaigns graph validation/activation. Agents owns proposals with rationale and unresolved gaps. Explanations reference recorded decisions rather than inventing fitness. Acceptance/rejection becomes typed feedback.

## Invariants and Verification

LLMs cannot mutate signed constraints, create measurements or self-promote knowledge. Source/tool content is data, not superior instruction. Verify source attribution, prompt regressions, unsupported claims, invented tools and reviewability. Retained model outputs enable reconstruction; repeated calls need not reproduce them.

## Component and Object Design

| Proposed component | Owned artifacts and behavior |
|---|---|
| Context assembler | Scoped artifact/projection selection, relevance, rights and explicit omissions |
| Prompt registry | Template/version, task/output contract, evaluation suite and allowed tool use |
| Model-call adapter | Provider/model/configuration binding, request/result and reproducibility limits |
| Proposal validator | Schema/identity/capability checks and routing to owning-domain validation |
| Explanation renderer | Human-readable account sourced from recorded decisions and evidence |

A context packet identifies objective, source revisions, constraints, relevant tool descriptors, knowledge projection, budget and required gates. It retains retrieval provenance and exclusion/truncation reasons. Token budgets are limits, not permission to discard the governing objective or hard constraints silently.

## Proposal Flow

The [Graph Runner](../System/Graph_Runner.md) can request campaign-supervision reasoning through a durable, scoped engagement. Agent Planning owns context assembly/model attempts and returns the requested typed proposal with prompt/model/input provenance. It does not own the engagement's execution decision, call scientific tools outside granted work or advance the campaign. Relevant frontier changes can make its response stale; runtime validation/conditional acceptance governs use. Model unavailability must not block unrelated graph branches.

Resolve authorized task context, retrieve a bounded functional universe, invoke the model with a structured output schema, validate the proposal and submit it to its owning domain. A graph proposal goes to Campaigns; a claim proposal to Knowledge; an envelope to Research. The model call itself does not commit these objects.

When output is invalid, a bounded repair request includes specific validation findings and preserves the original attempt. Repeated repairs cannot relax policy or exceed the original budget. Capability gaps remain named missing functions rather than generated code automatically entering the registry.

## Failure and Boundary Example

A retrieved document contains instructions to bypass evidence review. Context assembly labels it source content; validation rejects any resulting unauthorized proposal. If necessary context is unavailable, report the missing dependency and request a bounded retrieval/clarification action rather than infer an approved constraint.

## Design Basis and Open Decisions

Prompt integration and human-decomposition requirements define authority boundaries. Remaining decisions: model/provider selection, context-ranking policies, output schemas and task-specific quality thresholds. Evaluation must distinguish grounded scientific usefulness from fluent narration.
