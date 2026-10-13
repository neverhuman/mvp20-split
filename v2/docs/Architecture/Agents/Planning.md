# LLM Planning and Context

- Design status: context/proposal,owner handoff,durable supervision,inspection and bounded live synthetic evaluation implemented; selected-model deployment wiring and scientific-quality validation remain separate gates.
- Naming note: component/record/operation names below are proposed logical design, not implemented APIs or selected deployment technology
- Last reviewed: `2026-10-11 19:26:42` (America/Chicago)
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

Prompt integration and human-decomposition requirements define authority boundaries. Initial evaluation uses pinned GPT-5.4 mini under delegated cost limits. Production context-ranking/tokenizer policies and broader task-specific quality thresholds remain separate decisions. Campaign and extraction output profiles are already versioned; new tasks require explicit profile review. Evaluation must distinguish grounded scientific usefulness from fluent narration.

## Implemented boundary checkpoint

Agent Planning0.30 and public Planning contracts0.7 preserve the [initial model boundary](../../Audits/BP-07.01_Model_Engagement_Closeout.md) and add versioned attributed text extraction, exact source-byte quotations, immutable failed/repaired traces, aggregate repair budgets and derived Artifact publication. Separate source, Knowledge and Research readers use bounded public interfaces. Owner handoff persists original request bytes before effects and reconciles exact owner records after replacement; it never changes a task's pinned graph head. Knowledge accepts structural changes, Research registers declarations and Data controls processing rights. Candidate answers and model interpretations retain proposal authority.

The [Planning module contract](../../../services/agent_planning/README.md) owns implementation detail and replacement instructions. Actual Data/Research/Knowledge process evidence covers rights withdrawal, lost replies, abrupt Planning exits, exact receipt recovery and future-task correction selection. Reviewed synthetic corpus scoring is software evidence, not scientific entailment or real-model accuracy. The service now has public checkpoint intake and a separately injected live evaluation adapter; deployed scheduling remains fixture/disabled until BP-09.03 integration. Campaign proposal compilation is now implemented as described below; Runtime engagement acceptance is implemented under BP-07.04; no extraction acknowledgment advances a running campaign or makes scientific quality a global veto.

Planning0.52/public Planning0.9 also implements bounded public campaign context reads, exact required/optional packet fitting under a reviewed fixture tokenizer, and immutable planning0012 preparation history. Actual five-peer input assembly, source-rights denial versus historical readback, future-only correction and process replacement are verified. The distinct campaign output profile binds original request/action/digest/scope/cut and preserves exact raw/typed observation history across process and installation replacement. Semantic eligibility and compiler handoff are now implemented below; Runtime engagement acceptance is implemented under BP-07.04; no live-model or scientific claim follows from these proofs.


Planning0.69/public Planning0.9 implements evidence-purpose and exact tool/composition policies, declarationv1/v2 bounds, original stored-accounting checks and a durable compiler client. Runtime retains draft/compiler/execution authority; Registry eligibility observations are finite and do not reserve capacity. Immutable selection/round/effect journals, database-clock fencing, original receipt reconciliation and fresh-use checks bound one effectful POST per progression invocation. Actual-owner crashes, source-rights changes and replacement preserve exact histories. The [campaign closeout audit](../../Audits/BP-07.03_Campaign_Closeout.md) separates these proofs from pending Runtime engagement acceptance and live-model/scientific quality.300-descriptor synthetic catalog acceptance measures bounded identity/context handling, not semantic ranking effectiveness.

Current evaluation boundary: Planning0.95/planning0019 preserves frozen input/rubric/model revisions,allprimaryattempts and conservative settlement. Provider-enforced extraction schema complements local validation; current syntheticv5 passes12/12,earlierfailuresretained. Runtime0.62/Studio0.8 expose coherent scoped metadata and separate authoritative decisions. [Evaluation closeout](../../Audits/BP-07.05_Evaluation_Closeout.md) records independent replacement,exact limits and BP-09.03 deployment handoff.

## Exact saved-campaign provenance

Planning owns a bounded read-only association between an exact Runtime draft
revision/content digest and its original retained compiler proposal/preparation,
Research selections, Knowledge pins, tool bindings and accepted save receipt.
Record the private lookup atomically with the accepted save observation. Rebuild
and reads revalidate original history; no latest-head inference, provider call or
peer database access is permitted. Scope/read grant is independent of write rights.
Studio verifies Runtime and Research reads separately before displaying provenance;
source and Knowledge inspection retain their own authorization. Missing association
never identifies the author. Compilation and context do not establish scientific
validity or current execution eligibility. [UI-01.07](../../Build%20Plans/UI-01.07%20Campaign%20provenance%20decision.md)
and the [owned module](../../../services/agent_planning/src/amphora_agent_planning/campaign_origin/README.md)
record the concrete versioned API and qualification. This contract does not expose
raw prompts, provider captures or hidden reasoning.

## Managed curation peer identities

Planning retains the human requester as owner of the curation intent and policy.
Its compiler already records separate Runtime-author and Registry-eligibility
identities in immutable selection records. Managed worker configuration must expose
that separation so each peer can authorize a restricted service credential without
duplicating a human principal or sharing operator credentials. Private profilev2
selects these two actors explicitly; legacyv1 keeps its original same-actor behavior.
A configuration binding creates no grant: Runtime/Registry authenticate their own
principals, and retained selections reject a changed peer identity on replay.

## Provider response windows and output allocation

Token allowance and response deadline are independent controls. Output allowance
includes reasoning as well as visible graph text ([official OpenAI reasoning
guidance](https://developers.openai.com/api/docs/guides/reasoning)). A larger graph
can need both enough output tokens and a bounded longer wait. Keep spend reservations,
request identity and recorded dispatch deadlines explicit; timeout does not prove
zero provider spend or authorize resending an original. Curation job heartbeats renew
ownership separately from provider timing, and quiescence waits for the bounded turn.
Current scientific profile keeps the same0.25USD hold while reallocating input/output;
the opt-in180s response window is separate from the default60s profile. Actual
provider acceptance, software execution and scientific validity remain separate gates.
