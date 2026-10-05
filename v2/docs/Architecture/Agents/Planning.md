# LLM Planning and Context

- Design status: immutable context, deterministic provider boundary, conservative budgets, attributed text extraction, bounded repair, durable owner handoff and campaign context preparation and typed proposal outputs implemented; semantic campaign handoff, Runtime engagement acceptance and live model evaluation remain successor scope
- Naming note: component/record/operation names below are proposed logical design, not implemented APIs or selected deployment technology
- Last reviewed: `2026-10-04 20:22:16` (America/Chicago)
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

## Implemented boundary checkpoint

Agent Planning0.30 and public Planning contracts0.7 preserve the [initial model boundary](../../Audits/BP-07.01_Model_Engagement_Closeout.md) and add versioned attributed text extraction, exact source-byte quotations, immutable failed/repaired traces, aggregate repair budgets and derived Artifact publication. Separate source, Knowledge and Research readers use bounded public interfaces. Owner handoff persists original request bytes before effects and reconciles exact owner records after replacement; it never changes a task's pinned graph head. Knowledge accepts structural changes, Research registers declarations and Data controls processing rights. Candidate answers and model interpretations retain proposal authority.

The [Planning module contract](../../../services/agent_planning/README.md) owns implementation detail and replacement instructions. Actual Data/Research/Knowledge process evidence covers rights withdrawal, lost replies, abrupt Planning exits, exact receipt recovery and future-task correction selection. Reviewed synthetic corpus scoring is software evidence, not scientific entailment or real-model accuracy. This internal package still has no public server or live adapter. Campaign execution proposals and Runtime engagement acceptance are separate successors; no extraction acknowledgment advances a running campaign or makes scientific quality a global veto.

Planning0.52/public Planning0.9 also implements bounded public campaign context reads, exact required/optional packet fitting under a reviewed fixture tokenizer, and immutable planning0012 preparation history. Actual five-peer input assembly, source-rights denial versus historical readback, future-only correction and process replacement are verified. The distinct campaign output profile binds original request/action/digest/scope/cut and preserves exact raw/typed observation history across process and installation replacement. Semantic eligibility, compiler handoff and Runtime engagement acceptance remain subsequent gates; no live-model or scientific claim follows from these proofs.
