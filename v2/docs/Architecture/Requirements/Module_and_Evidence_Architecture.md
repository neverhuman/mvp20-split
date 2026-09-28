# Module and Evidence Architecture

For the active graph-native tool invocation, state, feedback and cross-domain migration contract, see [Scientific Tools and Graph Execution](Scientific_Tools_and_Graph_Execution.md). The module families below describe the existing coatings-oriented baseline, not a universal execution pipeline or biological tool catalog.

## Architectural Principle

The platform is a governed evidence network, not a single model with averaged scores. Specialist modules emit typed evidence. A central policy/orchestration layer decides what may count for a given output.

A module with no standing to answer a question must abstain instead of producing a confident number.

## Module Families

### Molecule Modules

Purpose: identity and structural reasoning.

Expected capabilities:

- identity and property diagnostics
- proposal generation with lineage
- role fitting
- novelty distance
- structural design gates

### Formulation Modules

Purpose: formulation arithmetic, constraints, and manufacturability.

Expected capabilities:

- mass and equivalent arithmetic
- formulation universe accounting
- envelope gates
- design rules
- ingredient library
- solvency and phase stability
- tolerance robustness

### Performance Modules

Purpose: property and service-condition models.

Expected capabilities:

- barrier corrosion
- cure and pot life
- process quality control twin
- viscosity and sag
- corrosion benchmarking

### Assurance Modules

Purpose: trust, custody, claims, replay, and reporting.

Expected capabilities:

- candidate contracts
- evidence intake
- source and rights ledger
- run provenance and replay
- red-team audit
- freedom-to-operate flagging for counsel review
- sourcing, environment, health, and safety screening
- report packaging

## Evidence Bus

Every module result should use a common evidence envelope:

```text
module_id
module_version
method_id
authority_tier
candidate_id
input_hash
output_hash
status: PASS | FAIL | ABSTAIN | NOT_APPLICABLE | UNKNOWN
confidence_or_error_when_authorized
limitations
source_refs
created_at
review_state
```

The evidence bus must preserve candidate-bound provenance across generation, gate checks, lab handoff, lab return, reporting, and replay.

## Policy Solver

The policy solver reads module envelopes and model-card authority. It applies:

- authority ceiling
- applicability to the current envelope
- evidence strength
- coverage
- abstention handling
- rights/license status
- customer-data scope
- safety/legal/qualification limits

Authorized outputs include audit cohorts, rejections/quarantine, abstentions, CRO packet drafts, candidate packages, and later manufacturing packages.

## Authority Rules

- `INTERESTING_FOR_AUDIT` is not a rank.
- Dataset presence is not model validity.
- A signed deterministic check is not scientific validation.
- A candidate package is not product qualification.
- Freedom-to-operate flagging is not a legal opinion.
- NAVSEA/QPL/procurement approval can only come from external authority.
- Unknown evidence fails closed for hard gates.

## Model and Method Selection

The system should use the strongest available method for each parameter, even when that method is classical physics or literature rather than Amphora ML.

Examples from the artifacts:

- Use physics when classical polymer physics beats the learned model.
- Use literature methods when they beat the internal implementation.
- Treat public corrosion data as too thin when no method beats baseline; require proprietary panel data before model authority improves.

## Lab Feedback Rule

Only accepted empirical returns may update an authorized method. Claim locks, held-out splits, truth labels, thresholds, and solver authority must not adapt silently.

The lab loop requires:

- raw measurement files
- calibration and method metadata
- candidate binding
- controls
- deviation records
- custody/provenance
- reviewer state
- model-card update trail
