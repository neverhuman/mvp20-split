# Multistage Process Graphs

- Design status: intended semantics and qualification requirements; no new runtime
  implementation claimed by this document.
- Last reviewed: 2026-10-08 20:58:22 (America/Chicago).
- Parent: [Graph Definitions and Activation](Definitions.md).
- Delivery: UI-01.05 owns inventory-grounded LLM authoring; POP-01 owns population/
  process composition, execution and visualization qualification. Scientific tools
  own actual reaction/process models; this design does not authorize physical lab work.

## Width changes represent scientific operations

A campaign is not restricted to a pipeline or one scatter followed by one join.
It may repeatedly widen, converge and widen again, with unequal branch lengths,
conditional routes, multiple inputs/outputs, reusable subgraphs and bounded loops.
For example, independent A/B preparation can feed a combine operation; its mixture
can feed a thermal-process model; that output and independently prepared C can
feed another addition operation; the resulting intermediate can split into several
analyses or alternative downstream routes. A19-stage route is an ordinary supported
graph shape to qualify, not a special hard-coded workflow.

Three operations must not be conflated:

- **Synchronization join:** waits for required control/data dependencies. It does
  not chemically combine substances or manufacture an aggregate scientific result.
- **Scientific transform:** a registered multi-input tool creates a new mixture,
  intermediate or product state, with exact input/output and process provenance.
- **Population selection:** a declared policy narrows candidate membership. It
  neither merges those candidates chemically nor erases rejected history.

Reading one artifact from several nodes is data fan-out. Splitting a physical batch
into aliquots or proposing several new chemical products is a scientific operation
with its own identity, quantities and evidence. Copying references does not prove
material availability or conservation.

## Ports, material state and lineage

Represent a molecule, formulation, mixture, intermediate, product and physical
sample/batch as distinct typed records where applicable. Preserve representation,
composition/amounts/units, phase/state and known process conditions with explicit
unknowns. Heating a material can change its state or properties without changing
its molecular identity; do not invent a reaction product from an operation label.

Each transform produces a new immutable state revision referencing all consumed
inputs, tool/model release, parameters and evidence. Many-to-one and one-to-many
lineage are not genetic crossover. The current numeric candidate contract's two-
parent bound must not be reused as a maximum reaction-input count. Genetic ancestry,
material derivation and execution lineage remain separately typed and traversable.

Port contracts declare single/optional/collection input, representation/units,
compatibility and output cardinality. Pairwise, keyed and Cartesian combinations
are distinct policies. Never accidentally produce an all-pairs explosion; require
explicit keys/compatibility rules, deterministic ordering and declared upper bounds.
Runtime learns actual output membership from accepted manifests and validates it
against the admitted bound before expanding downstream work.

Chemical identity, mass/stoichiometry, compatibility, yields/byproducts and equipment
applicability are checked by qualified domain tools under declared assumptions.
Runtime validates contracts and routes their outcomes; it cannot infer chemical
feasibility from graph connectivity or treat unknown mass balance as validated.

## Execution and authoring

Readiness is local to required predecessor outputs, not a barrier across every
visual column or stage. Unrelated branches can continue while a slower precursor
is pending. A declared generation-selection barrier is a separate Search policy.
Missing/failed/optional inputs have explicit join and fallback semantics. No implicit
use of a different candidate's, generation's or batch's intermediate to satisfy a join.

Iteration uses existing explicit bounded loop constructs; arbitrary cycles remain
invalid. Nested candidate/process scopes preserve occurrence identity. Admission
checks expanded-work bounds, route depth, resource/attempt budgets, termination and
compatible typed bindings. Intermediate artifacts/checkpoints survive restart;
accepted work is not rerun solely because a downstream stage failed.

The LLM composes this topology using Registry descriptors and pinned Knowledge
constraints. It must express branch/convergence intent, stage inputs/outputs,
pairing policy and limits rather than emit a flat list of steps. Unsupported
transforms become durable capability requests. A plausible diagram or language
description does not create an executable tool or qualify a chemical process.
Human changes target later campaign revisions; existing active-run policy remains.

## Visualization and qualification

Show actual directed scientific dependencies, with expandable process-stage groups
and a retained local view. Population and generation overlays remain separate from
material combinations. At a convergence show what inputs were consumed and what
new intermediate was produced; allow backward tracing through every precursor.
Long routes need readable local neighborhoods/breadcrumbs and a bounded overview,
not shrinking all labels to fit or assuming all sibling nodes share one stage.

Acceptance includes a19-stage deterministic engineering fixture with at least three
width changes, multi-input and multi-output steps, unequal branch durations, a
conditional route and bounded iteration. Prove local readiness, intermediate reuse,
identity-safe combinations, cardinality limits, restart and lineage/UI traversal.
Use synthetic process tools and label that evidence as software qualification;
real synthesis, lab control or prediction accuracy requires separate tool evidence.
