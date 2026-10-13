# Candidates and Synthesis

- Design status: detailed proposed contract; implementation and scientific acceptance pending
- Naming note: component/record/operation names below are proposed logical design, not implemented APIs or selected deployment technology
- Last reviewed: `2026-09-22 18:56:40` (America/Chicago)
- Parent: [Domain overview](Research_Architecture.md)
- Requirement source: [Product Requirements](../Requirements/Product_Requirements.md#synthesis-feasibility-and-route-planning)

## Owned Contract

Candidate versions are domain objects: formulation/process designs, discrete molecules, sequences or other declared representations. Preserve identity, parentage, immutable revisions, units and context. Domain adapters own valid variation, repair and conversion; transport schemas do not supply behavior. Shared search mathematics does not make representations interchangeable.

Formulation capabilities maintain ingredient/feedstock identities, supplier/grade constraints, fractions, units, cost and process parameters. Domain calculators may recompute physical properties while remaining independently testable and swappable. Sourcing, EHS, IP and performance assessments retain their own applicability and authority; none is implied by candidate generation. Biological candidates additionally require target/system, assay/species, route, dose/time and endpoint context where relevant.

Synthesis/production assessments bind candidate and alternative route revisions to steps, intermediates, precursors, conditions, equipment, purification, identity/purity goals and project constraints. Retain step-level precedent and uncertainty. Distinguish proposed routes, supported precedent, experimental demonstration, project-blocked routes and no route found within bounded search.

## Boundary and Flow

Capabilities supplies generation, prediction and route tools; Campaigns composes them and feeds feasibility constraints into search. Research owns scientific result meaning. Purchased material can use procurement with identity/specification checks. Laboratory confirmation belongs to the experiment lifecycle.

## Invariants and Verification

Structural validity is not synthesizability; no route found is not impossibility; laboratory success is not scale-up or qualification. Separate small-molecule, polymer and biological production applicability. Packages disclose lineage, properties, evidence, route disposition, process/BOM where applicable, limitations and handoff. Verify domain rejection, route comparison and unknown feasibility without favorable default fitness.

## Component and Object Design

| Proposed component | Owned records and behavior |
|---|---|
| Candidate aggregate | Stable design identity plus immutable representation revisions and parent/change lineage |
| Representation adapter | Decoding, canonicalization, equivalence policy and domain-valid mutation/repair |
| Route assessment coordinator | Alternative route revisions, step dependencies, applicability and project-fit dispositions |
| Package assembler | Pinned candidate/result/route/protocol references and explicit omitted evidence |

A `CandidateAttempt` records an attempted design even when invalid or duplicate. It references a candidate revision only when a valid representation exists. Route steps refer to precise intermediate identities, transformation/method versions and evidence. Route feasibility, procurement availability and authority are independent fields; do not hide them in a scalar score.

## Interaction and State

Generation emits proposed representations plus operator lineage. The adapter validates identity and admissibility before scientific evaluations are bound. Equivalent candidates may share permitted cached computation, but every attempt and selection rationale remains retained. Equivalence depends on representation: a matching molecular graph does not establish an identical polymer distribution, formulation process or assay context.

Route assessment receives candidate revision, requested scale/purity and resource policy; it returns alternatives and step-level gaps. A selected route becomes a separate experiment proposal. Laboratory evidence later attaches to the actual tested route and candidate revisions. Packaging resolves only pinned eligible evidence and cannot select a newer favorable result silently.

## Failure and Boundary Example

A route can be literature-supported but blocked because the required equipment or precursor grade is unavailable. Search may request another route or revise the candidate inside approved variation bounds. Unknown yield/cost remains unknown. If no route is found, retain provider/tool version, search space and budget so the result is not interpreted as chemical impossibility.

## Design Basis and Open Decisions

[Reuse Baseline](../Evolutionary_Code_Reuse_Baseline.md) separates numeric/identity reuse from domain-specific generation. Remaining decisions: representation schemas and equivalence for each initial domain, route-provider adapters, validated feasibility policies and package templates. These are independent of the reusable graph runtime.

## Synthetic candidate declaration ingress

BP-08.03 adds a focused Research registration boundary. Authorized callers submit the existing CandidateRevision, with an exact representation Artifact. Reviewed host profiles pin the representation schema, kind and synthetic semantic profile. Research resolves current Data access and exact bytes before entering its identity transaction; it validates scope/encoding but does not import operator implementations or infer chemical legality. Registration declares a proposed candidate only. Tool execution acceptance, evaluation fitness and scientific eligibility remain separate evidence.

Identity and first-public-registration provenance commit atomically. Exact retries retain the original actor/history and recheck source access; changed immutable bytes or stale succession conflict. Authorized historical identity reads do not fetch source bytes or erase records when rights later change. The read authorization observed before commit is not a distributed transaction guarantee or a new retention lease. Public registration is explicitly configured and separately granted from questions/needs and scientific decisions.

## Supplied finite chemical structure declarations

UI-02.01 owner approval extends candidate ingress through an explicit, separately
configured chemical profile. Research0.41.0 accepts successful chemical-structure
bundles only for the exact registered candidate/revision/scope; synthetic defaults,
DTOs, immutable identity ledger and current-rights retry rules remain intact.
An independently packaged chemical_structure tool owns parsing/normalization,
formula and bounded inert2D PNG. Research has no RDKit/scientific-tool dependency.

The first profile accepts supplied connected finite molecules/oligomers with explicit
end groups. It preserves isotope, formal charge, explicit H and supported stereo;
unspecified stereo remains visible. Unspecified polymers, mixtures, biological
sequences and unsupported chemical features require separate adapters. A structural
derivation is neither a generated candidate, a recommendation, synthesizability
assessment nor efficacy evidence. Exact accepted Runtime producer plus current Data
bytes/rights establish attribution; self-reported hashes alone do not.

UI-02/P1.1-P1.3 component gates are implemented; actual registered owner handoff
P1.4 and candidate UI P2-P4 remain acceptance gates. No claim of image deployment
or property-model integration follows from the native independent tool tests.
