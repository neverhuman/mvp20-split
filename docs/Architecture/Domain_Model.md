# Domain Model

## Core Entities

### User

Represents authenticated system users. Users own created records and may have roles such as scientist, program lead, reviewer, admin, or lab operator.

### Organization / Program

A program is the business and technical container for a material development effort. It owns product envelopes, candidate campaigns, lab plans, evidence, and deliverables.

### ProductEnvelope

The signed technical problem statement. It contains typed constraints, objectives, test methods, process limits, cost limits, regulatory constraints, and unresolved ambiguity.

Product envelopes are versioned. A candidate campaign must bind to a specific envelope version.

### DomainPack

A domain-specific capability bundle:

- representation adapter
- property calculators or simulators
- material/feedstock library
- design rules
- test-method map
- evidence schema
- known-answer benchmarks

The first concrete domain pack is coatings. Future packs may cover membranes, batteries, semiconductor-class materials, cement systems, or PK/PD/ADMET formulation envelopes.

### Ingredient

A material input with constants, supplier data, role, cost, rights/restriction status, and provenance.

### Formulation

A versioned recipe made of ingredient components. Formulations are immutable once referenced by experiments. Iteration happens by cloning to a new version with `parent_id` lineage.

### FormulationComponent

The ingredient and mass fraction pair inside a formulation. Two-component systems may also need part assignment and equivalent-balance metadata.

### Candidate

A generated or human-authored formulation proposal bound to a product envelope and candidate campaign. A candidate may be feasible, rejected, quarantined, selected for lab, or retired.

### EvolutionCampaign

A bounded genetic-programming style optimization run under a signed product envelope. It owns the seed population, generation requests, allowed operators, generation limits, fitness policy, authority snapshot, and selection decisions.

### Genome

The mutable representation of a candidate. For coatings this may be ingredients, roles, mass fractions, part assignments, mix ratios, and process parameters. For molecule/polymer campaigns this may be parent structure ids, reaction templates, grammar ids, scaffold facts, and role constraints.

### CandidateAttempt

An attempted generated candidate. Accepted attempts, rejected attempts, invalid attempts, duplicates, and quarantined attempts are all retained for replay and audit.

### FitnessComponent

An authority-scoped score or gate emitted by a module for a candidate attempt. Abstentions remain abstentions; they are not zeros.

### SelectionDecision

A policy-solver decision that records which candidates were selected or rejected, which fitness components counted, what authority snapshot was used, and whether ranking was authorized.

### ComputedProperty

A deterministic derivation from formulation composition and ingredient constants. Computed properties are not the source of truth; they are recomputed on read or cached with invalidation.

### Experiment

A planned, prepared, tested, failed, or retired lab batch bound to a formulation/candidate. It records batch code, preparation context, and notes.

### Measurement

A measured property from an experiment. It includes property name, value, unit, method, measured timestamp, raw file references, calibration/custody data, and deviation notes when available.

### EvidenceRecord

A candidate-bound result emitted by a module or ingested from lab/source review. It carries authority, provenance, module version, method/model-card reference, and pass/fail/abstain/not-applicable status.

### Module

A specialist capability that answers a narrow question. Modules do not become globally authoritative by existing; they declare authority per method, domain, and evidence tier.

### CandidatePackage

An auditable handoff artifact that assembles candidate identity, formula, process route, sourcing, cost, gate results, evidence limitations, and lab protocol references.

## Data Acquisition Entities

These are proposed domain responsibilities, not implemented database/API schemas. See [Data Sources and Acquisition](Data_Sources_and_Acquisition.md) for behavior and acceptance.

- **DataSource / SourceRevision:** stable source identity and immutable access/format/capability metadata revisions, including protected credential references, rights, applicability, and freshness policy.
- **SourceScopeAssociation:** associates a source with a domain pack, product/envelope, or project/program for discovery and defaults; it cannot grant access.
- **CampaignSourceBinding:** pins the resolved source revision, query/selection, expected typed outputs, and acquisition/failure policy to a campaign revision; a run records the exact resolved inputs.
- **AcquisitionRecord:** owns acquisition outcome and attempt history, provider version/cursor or window where applicable, timestamp, connector version, and produced artifact references.
- **DataArtifactRevision:** immutable retained payload identity and metadata, hashes, schema/representation, quality state, rights/retention rules, and upstream source/transformation lineage.
- **EvidenceBundle:** versioned selection of artifact revisions and evidence references with selection rules and review disposition. It does not grant its members greater authority.

Source/binding policies own eligibility and default resolution; acquisition objects own state and retry outcomes; artifact/bundle objects own lineage and version selection. Boundary DTOs serialize these decisions rather than replacing domain behavior.

```text
DomainPack / ProductEnvelope / Project or Program
  -> SourceScopeAssociation -> DataSource -> SourceRevision
Campaign revision -> CampaignSourceBinding -> SourceRevision
Campaign run/node -> AcquisitionRecord -> DataArtifactRevision
DataArtifactRevision -> normalization/validation -> DataArtifactRevision
EvidenceBundle -> pinned artifact/evidence revisions
Reviewed domain assertion -> supporting/contradictory evidence references
Campaign decision -> consumed artifact revisions and reviewed assertions
```

## Lifecycle Rules

- Product envelopes require explicit sign-off before candidate generation.
- Inferred/defaulted constraints remain low-authority until countersigned.
- Formulations become immutable when experiments reference them.
- Computed properties derive from ingredients and components; do not edit them manually.
- Candidate rankings are only allowed where module authority explicitly permits them.
- Evolutionary campaigns must preserve every attempt, including rejects and duplicates.
- Chemistry-changing operators remain disabled until validated and authorized.
- Unknown or missing evidence must remain visible as missing evidence.
- Lab data enters through evidence intake, not ad hoc edits.
- Model promotion depends on held-out evaluation and authority gates, not manual optimism.
- Customer engagement data stays scoped to the engagement unless explicitly approved otherwise.
- Source defaults cannot widen access; activated bindings and historical acquired inputs cannot change silently.
- Source refreshes create new artifact revisions; acquisition does not promote extracted scientific claims.
- Retention/access restrictions apply to raw and derived artifacts; replay limitations remain visible when required inputs cannot be retained or accessed.

## High-Level Relationships

```text
Organization
  -> Program
     -> ProductEnvelope version
     -> DomainPack
     -> EvolutionCampaign
        -> GenerationRequest
        -> CandidateAttempt
           -> Genome
           -> Candidate
           -> Formulation version
              -> FormulationComponent
                 -> Ingredient
           -> ComputedProperty
           -> FitnessComponent
           -> EvidenceRecord
           -> CandidatePackage
        -> SelectionDecision
        -> Experiment
           -> Measurement
```
