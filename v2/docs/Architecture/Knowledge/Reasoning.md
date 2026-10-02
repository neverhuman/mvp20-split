# Reasoning and Evidence Authority

- Design status: Configured finite reasoning, exact owner-state binding, durable result history and optional HTTP implemented in BP-06.03/B1; artifact publication, Research assessment and domain receipts remain pending.
- Naming note: component/record/operation names below are proposed logical design, not implemented APIs or selected deployment technology
- Last reviewed: `2026-10-02 09:39:22` (America/Chicago)
- Parent: [Domain overview](Knowledge_Architecture.md)
- Requirement source: [Product Requirements](../Requirements/Product_Requirements.md#neuro-symbolic-reasoning-and-evolutionary-search)

## Owned Contract

Assertions carry evidence, scope, temporal validity, confidence, evidence strength, author and hypothesis/accepted posture. Symbolic rules/equations/domain objects produce bounded reasoning with consumed assertions and rule versions. Distinguish hard constraints, defeasible guidance, hypotheses and contradictions. Derived assertions retain derivation lineage rather than becoming independent evidence.

Refinery stages separate acquired/candidate material, normalized claims, evaluation, promotion and withdrawal. Scientific authority is separate from operational health. Projections expose applicability limits and missing knowledge for planning, constraints and explanations.

## Boundary and Flow

Data supplies rights-scoped artifacts/retrieval; Research supplies observations; Agents proposes statements. Knowledge owns claim/rule promotion; Campaigns records exact projections consumed. Platform enforces reviewer identities and approvals, not scientific truth.

## Invariants and Verification

Do not strengthen correlation or hypotheses into proven causality. Model output is not measurement. Corrections identify consumers without rewriting old decisions. Verify contradiction visibility, applicability abstention, candidate/trusted separation, rollback and explanation lineage.

## Component and Object Design

| Proposed component | Owned behavior |
|---|---|
| Assertion/evidence binder | Scoped assertions, supporting/contradicting evidence and source authority |
| Rule registry | Versioned symbolic rules, applicability and review state |
| Projection builder | Bounded revision-pinned knowledge selected for a task/purpose |
| Reasoning evaluator | Constraint/inference results with consumed assertions and derivation traces |
| Promotion/withdrawal policy | Review decisions and affected-consumer consequences |

Keep an assertion's extraction confidence separate from scientific evidence strength. Confidence propagation requires a declared method; do not multiply arbitrary scores or treat repeated citations of one observation as independent corroboration. Derived conclusions reference rules and premises, including contradictions and missing premises.

## Reasoning and Promotion Flow

A reasoning request names objective, domain context, graph/rule revision and authorized evidence scope. Eligibility filtering precedes inference. The result contains satisfied/violated/unknown constraints, explanations and proposed next evidence needs. A hypothesis can be represented and explored without being eligible as a hard execution constraint.

Promotion checks rights, source integrity, applicability, independent review where required and claim authority. It creates a graph/rule revision with an attributable decision. Withdrawal identifies projections, campaigns and models that consumed the old assertion; it does not rewrite their historical decisions.

## Failure and Boundary Example

Two studies disagree under different assay conditions. Preserve both observations and their applicability rather than average them into one truth value. If the campaign context matches neither study, return unknown/out-of-scope and propose acquisition or an experiment. A stale projection may be rejected or refreshed under the requesting policy, never silently replaced mid-decision.

## Design Basis and Open Decisions

Product Requirements defines the refinery and reasoning/evolution boundary; [Domain Model](../Requirements/Domain_Model.md) supplies assertion/applicability concepts. Remaining decisions: supported logic/rule formalism, contradiction policies, calibration and evidence-strength model. The knowledge graph is not itself proof of causal validity.

## Initial implementation profile

The [BP-06.03 activation audit](../../Audits/BP-06.03_Activation.md) selects finite grounded signed implications for synthetic engine proof, with exact context identity and bounded work/depth/facts. Explicit conflict remains visible; no negation-as-failure or arbitrary code is executed. The [private module](../../../services/knowledge/src/amphora_knowledge/reasoning/README.md) documents implemented behavior and limits. Logical entailment from represented hypotheses cannot grant scientific authority. General scientific rule formalism/calibration remains open beyond this fixture profile.
