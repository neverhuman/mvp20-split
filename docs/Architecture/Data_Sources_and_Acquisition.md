# Data Sources and Acquisition

## Status

- Design status: specified direction; implementation and acceptance pending
- Last refreshed: `2026-09-16 11:52:21`
- Scope: domain-, product-, and project-scoped data sources, campaign acquisition, retained artifacts, and evidence lineage
- Active focus: source contracts and typed acquisition nodes within the graph-native engine
- Next gate: versioned source/binding/artifact contracts and a deterministic acquisition fixture
- Dependencies: campaign runtime, module capability index, artifact storage, and knowledge-refinery review boundaries
- Deferred: production connector coverage and live provider integration; no implementation completion is claimed

## Boundary and Ownership

Data sources have durable identities independent of any campaign. Acquisition and preparation activities are executable campaign nodes; scientific assertions extracted from their outputs belong in the neuro-symbolic domain graph after the applicable review. Execution/provenance remains derived from run events and artifacts.

| Element | Owner | Responsibility |
|---|---|---|
| Source definition | Source registry | Identity, access references, formats, supported operations, scope, rights, freshness, and applicability |
| Source binding | Versioned campaign definition and resolved run inputs | Selected source revision, query/selection, expected output, and acquisition policy |
| Connector and processing capability | Module registry | Reviewed implementation, typed ports, versions, limitations, and failure behavior |
| Acquisition and preparation | Campaign runtime | Query, import, parse, normalize, filter, join, validate, and retain |
| Data artifact and evidence bundle | Artifact/evidence storage | Immutable revisions, content identity, quality disposition, and upstream references |
| Candidate and reviewed assertion | Knowledge refinery and domain graph | Evidence-backed scientific meaning, uncertainty, applicability, contradictions, and promotion |

Raw records, PDFs, images, and instrument payloads remain artifacts referenced by graph entities. They need not become individual domain-graph nodes. A source definition is not a new authored graph type, and a registered source does not confer scientific authority on its contents.

## Source Scope and Selection

The product must support reusable source registrations and explicit associations with domain packs, products/product envelopes, and projects/programs:

- A domain can recommend reference corpora, databases, ontologies, and scientific data services.
- A product can add specifications, target profiles, supplier information, requirements, and applicability constraints.
- A project can add private experiments, instrument feeds, customer files, licensed collections, and campaign-specific inputs.

These scopes determine discovery and selection defaults, not inherited access rights. Effective selection must satisfy tenant, license, purpose, and project restrictions. Project/product choices may narrow defaults but cannot widen permissions. Conflicting defaults must be surfaced and resolved explicitly; the activated campaign records its resolved bindings rather than depending on mutable defaults. Product scope binds to a durable product or envelope identity, and project scope to its owning project/program identity.

## Heterogeneous Inputs

The capability model must accommodate APIs, relational and graph databases, object/file stores, curated uploads, document collections, instrument integrations, and bounded stream ingestion. Representations include structured tables, JSON/XML, PDFs and text, spreadsheets, molecular structures, sequences, images, spectra, and time series. This is an extensibility requirement, not a claim that every connector exists at initial delivery.

Connectors declare supported operations, formats/schema versions, pagination or cursor behavior, authentication references, rate limits, costs, freshness, retention constraints, and failure modes. Processing nodes declare representation, identifiers, units, methods, and applicability on their typed ports. Secrets are resolved through protected runtime references and must not be embedded in graph definitions, artifacts, or exported provenance.

Normalization must retain original identifiers, values, units, and method context alongside mappings and transformation versions. Ambiguous entity matches, incompatible assays, missing units, contradictory measurements, and uncertain extractions must remain visible or be quarantined under the configured policy. Deduplication must retain source lineage and must not count repeated publication or import of the same observation as independent evidence.

## Executable Acquisition Semantics

Campaign graphs can query, import, parse, normalize, filter, join, quality-check, and retain data using reviewed modules. A research loop may detect missing evidence, acquire additional material, or request an experiment before continuing. The graph must declare:

- source revisions and query/selection parameters, required versus optional inputs, and expected typed artifacts;
- pinned-snapshot, bounded-refresh, or bounded-stream policy, with freshness limits and acquisition timestamps;
- request/page/record/byte, time, cost, and retry limits as applicable;
- stream windows, offsets/watermarks, checkpoint and duplicate/late-event behavior where supported;
- missing, empty, partial, stale, incompatible, rate-limited, and unavailable-source dispositions;
- quality, evidence, and human-review gates and explicit loop/termination conditions.

A successful empty result is distinct from a failed or incomplete acquisition. Required-input failures block dependent nodes; optional inputs may proceed only under a declared policy with the omission visible. Retries must preserve attempt history and avoid duplicate retained results or repeated external effects. Source replacement and changed selections are attributable binding revisions subject to campaign amendment rules.

Newly acquired content remains candidate material until the relevant intake and review gates pass. Acquisition success is not knowledge promotion. Candidate processing and review nodes can inspect it; trusted generation, ranking, and experiment-selection consumers must use approved evidence/knowledge under the existing [refinery requirements](Product_Requirements.md#knowledge-refinery).

## Versioning, Retention, and Replay

Every acquisition records source identity/revision, selected provider version if available, query and filters, acquisition time, connector/transform versions, quality disposition, rights, run/node identity, and output artifact references. Retained artifacts carry content hashes, representation/schema metadata, upstream lineage, and applicable retention/access policy. Evidence bundles pin their member artifact revisions and selection rules.

Provider content changes and refreshes create new acquisitions/artifact revisions; they cannot rewrite the inputs of a historical run. Campaign decisions record exactly which artifact revisions and reviewed assertions they consumed. Domain assertions reference supporting and contradictory evidence at a useful granularity such as row, page, span, image region, or measurement.

Where rights permit, retain the acquired payload or a reproducible provider snapshot. If retention or provider versioning is unavailable, preserve permitted hashes, references, queries, and receipts and explicitly mark replay limitations. A hash alone does not reproduce data. Replay uses pinned retained inputs; contacting a changing provider is a new acquisition. Required deletion or access revocation must restrict consumption while preserving permitted audit metadata and explaining any resulting replay loss.

## Human Inspection

Graph Studio must let authorized users discover eligible sources, configure bindings, inspect formats and policies, preview permitted samples, and understand missing access or incompatible inputs. The execution view must expose acquisition status, freshness, quality, partial results, retained artifacts, and review state. Users must be able to traverse from a campaign decision or domain assertion to its exact source selection, transformations, and retained evidence, and compare source revisions across runs.

## Drug-Research Example

An illustrative graph combines domain reference literature and assay data, a product-specific target profile, and private project measurements:

```text
Research objective and target profile
    -> Query literature + retrieve assays + import project measurements
    -> Normalize compound/target identities, units, and assay conditions
    -> Check quality, applicability, duplicates, and contradictions
    -> Retain versioned evidence bundle
    -> Propose domain assertions and review evidence
    -> Rank candidates or design experiments using approved inputs
    -> If evidence is insufficient: bounded acquisition or experiment request
```

The fixture must preserve differing assay conditions and measured versus model-derived results. It must not silently merge incompatible endpoints or present a retrieved claim as a validated therapeutic effect. This example demonstrates composition requirements, not implemented drug-discovery functionality.

## Delivery and Acceptance

1. **Contracts:** versioned source registrations, scope associations, resolved bindings, acquisition records, and artifact/evidence-bundle references validate independently of a specific provider. Capability descriptors expose acquisition and processing contracts.
2. **Deterministic fixture:** a campaign combines at least a structured assay fixture and a document fixture with product constraints and project measurements, retains normalized outputs, and reproduces them from pinned inputs without network access.
3. **Quality and control:** fixtures exercise incompatible units/methods, ambiguous identity, duplicates, empty/partial results, stale data, denied access, unavailable providers, retry limits, and bounded acquisition loops. Required failures block; optional omissions are visible.
4. **Isolation and promotion:** project defaults cannot expose another tenant's source or widen a license; unreviewed extraction cannot enter trusted ranking or silently update accepted domain assertions.
5. **Change and replay:** changed source content creates a new revision, historical input selection remains inspectable, and retention/versioning limits explicitly prevent claims of exact replay.
6. **Inspection:** a reviewer traverses from a decision to the source/query, retained payload, transformations, quality checks, evidence review, and consumed assertion/artifact versions, and compares refreshed runs in Graph Studio.

Production integrations follow this foundation according to selected domain/product/project needs. Connector availability and validated scientific applicability must be tracked separately.
