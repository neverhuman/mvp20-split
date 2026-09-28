# Datasets Models and Shared Learning

- Design status: detailed proposed contract; implementation and scientific acceptance pending
- Naming note: component/record/operation names below are proposed logical design, not implemented APIs or selected deployment technology
- Last reviewed: `2026-09-22 18:56:40` (America/Chicago)
- Parent: [Domain overview](Data_Architecture.md)
- Requirement source: [Product Requirements](../Requirements/Product_Requirements.md#neuro-symbolic-reasoning-and-evolutionary-search)

## Owned Contract

Separate project evidence, promoted knowledge, models and campaign experience. Project-local learning does not authorize sharing. Dataset revisions bind inputs, rights, representation, splits, applicability and quality. Model revisions bind training lineage, method, domain/endpoint scope, uncertainty, validation and rollback.

Training follows eligible evidence -> rights/context review -> dataset -> training -> independent validation -> candidate -> shadow/limited-active evaluation -> reviewed promotion. Preserve controls and leakage boundaries. New results never automatically replace a model. Retirement identifies consumers and preserves permitted historical artifacts.

## Boundary and Flow

Research establishes measurement eligibility; Knowledge governs assertions/rules; Campaigns produces experience and runs jobs. Data governs datasets, models and reusable-experience packaging. Platform enforces consent/access. Capabilities binds models to inference/training tools.

## Invariants and Verification

Do not pool incompatible domains/methods/endpoints based on similar formats. Prior seeds/statistics are proposals, not new-project fitness evidence. Verify private-project exclusion, revocation, split independence, applicability abstention, comparisons and independent rollback for models, knowledge and search experience. Pipeline success is separate from scientific validity.

## Component and Object Design

| Proposed component | Owned records and behavior |
|---|---|
| Dataset curator | Exact member revisions, eligibility, representation and split manifests |
| Training/evaluation coordinator | Job configuration, seeds, method/environment and retained outputs |
| Model registry | Candidate/approved model versions, applicability, uncertainty and evaluation receipts |
| Experience curator | Rights-eligible seeds, motifs and operator statistics without leaked project context |
| Promotion controller | Shadow/limited-active decisions, consumer bindings and rollback targets |

Dataset lineage must include excluded records and exclusion reasons. A split manifest assigns stable grouping identities so related replicates, candidates or source families cannot accidentally straddle discovery and confirmation sets. The grouping policy is domain-specific and versioned.

## Training and Deployment Flow

Freeze eligible evidence and split policy, train a candidate artifact, run independent evaluation, then record scientific/operational approval separately. Inference tools bind exact approved model versions; promotion creates new bindings for eligible future invocations. Outstanding comparisons must either keep their model snapshot or explicitly reevaluate under the new one.

Knowledge updates and model updates have different acceptance paths. Shared experience statistics retain which tasks and policies produced them; a model ranking well under one endpoint does not automatically become eligible for another domain.

## Failure and Boundary Example

Consent is withdrawn for an observation used by a shared model. Identify the dataset, training jobs, model versions and consumers, restrict affected future use according to policy and create a remediation/retraining decision. Deleting the raw row alone does not remove its influence from a model; the impact remains explicit until resolved.

## Design Basis and Open Decisions

Product Requirements defines four governed learning surfaces. Remaining choices: model-family-specific validation rubrics, split grouping, retraining triggers and rights-remediation policies. Comparisons need uncertainty and out-of-distribution assessment; no generic score establishes transferability.
