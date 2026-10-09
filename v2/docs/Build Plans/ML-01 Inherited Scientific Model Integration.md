# ML-01 Inherited Scientific Model Integration

## Canonical tracker

- Status: queued; standalone post-demo plan, not activated.
- Last refreshed: 2026-10-08 19:07:02 (America/Chicago).
- Owner direction: prove the front-to-back research workflow before concentrating
  on the scientific implementations inside execution nodes.
- Overall implementation: 0%; M1/M2/M3/M4/V1=0%. Five equal delivery gates;
  Build0% averages M1-M4, Verification0% is V1. Planning earns no delivery credit.
- Owners: independent scientific tools own models/data applicability; Registry
  owns descriptors/releases; Planning owns inventory-grounded proposals; Runtime
  owns execution acceptance; Knowledge owns claims; Studio owns presentation.
- Prerequisite: UI-01/V1 and UI-02/P4 end-to-end evidence, including UI-01.05/I1
  inventory-to-LLM curation and a retained request for an unavailable capability.
- Current focus: preserve the inherited ML reuse backlog and its evidence limits.
- Next gate: after the demo acceptance gate, bounded activation audit and M1 inventory.
- Blockers/dependencies: raw feedback datasets absent from this checkout; complete
  trained-model bundles and reproducibility have not been established. v1 is read-only.
- Parent: none; priority and percentages mirrored in the Master Build Tracker.

## Entry gate: complete the workflow first

Demonstrate, through the served UI and actual owners:

1. Research question and relevant Knowledge claims/evidence are inspectable.
2. The LLM receives a versioned, bounded inventory of eligible tools and pinned
   Knowledge context, curates a graph and produces a validated revision.
3. A missing capability becomes an explicit, durable new-node/tool request,
   visible in the UI and linked to the research need. It is not invented as available.
4. Run admits a new campaign, starts managed workers and shows node-level progress.
5. Results preserve candidate identity, formula/structure and evidence; a subsequent
   campaign uses a traceable proposed change while prior history remains intact.

The missing-capability request mechanism must work before ML-01, but fulfillment
of that request by an inherited ML tool may be demonstrated inside ML-01. Do not
create a circular dependency by requiring ML migration for the initial workflow.
Calendar expiry or an attractive static demo is not this entry gate. Minimal
structure/formula support needed by UI-02 stays there; broad ML migration stays here.

## Initial inventory to investigate

| Family | Inherited evidence | Qualification questions |
|---|---|---|
| Solubility / BigSolDB | LightGBM/RDKit training and grouped validation scripts | Raw data/rights availability, exact-solute versus scaffold splits, corrected benchmark status and intended candidate domain |
| Melt viscosity / Polyverse | Gradient-boosting receipts, molecular fingerprints, polymer-safe tests and conformal/applicability records | Recover full training/inference bundle; preserve polymer-held-out results rather than using earlier source-split scores as novel-polymer performance |
| Coating properties / Purformance | ML/linear/physical baseline code, property receipts and duplicate/split audits | Apply superseding deduplicated evaluation; scope each endpoint and formulation space explicitly |
| Diffusivity / barrier | Fingerprint-based ML and conformal/shift evidence | Separate simulated from measured labels; reproduce weak cross-source/scaffold results and interval-width/applicability limits |

These are candidates for reuse, not four qualified v2 tools. M1 must produce a
disposition for every family: selected first tranche, blocked, or explicitly deferred,
with reasons. Do not silently drop an inherited family or imply all are ready.
The public corrosion benchmark's failed qualification is negative evidence to
preserve, not a performance claim to transfer to a coating candidate.

## Ordered phases

| Phase | Completion | Prerequisite | Deliverable / exit gate |
|---|---:|---|---|
| M1 inventory and scope | 0% | Entry gate and activation audit | Map actual code, data, weights, environments, rights, receipts and superseding audits; select and freeze the first tranche, explain every deferral, identify missing inputs and contract changes. |
| M2 reproduce and qualify | 0% | M1 complete | Restore authorized data outside v1, verify hashes/versions, reproduce selected baselines and corrected held-out protocols; retain failed results, uncertainty and applicability; distinguish inherited reports from fresh measurements. |
| M3 independent graph tools | 0% | M2 complete | Package qualified inference behind owned versioned contracts/descriptors, isolated dependencies and module READMEs; pin model/feature/dataset versions and record inputs/outputs. Separate training/calibration from inference. |
| M4 inventory and reasoning integration | 0% | M3 complete | Publish eligible descriptors; existing inventory/LLM flow discovers and proposes actual tools, validates compatible graph changes, links Knowledge evidence and fulfills a prior capability request through a qualified release. |
| V1 replacement and scientific evidence | 0% | M4 complete | Actual admitted campaign executes selected ML tools; UI shows outputs, benchmark scope and unknowns; independent installs, module tests, negative cases, replacement/replay preservation and scoped drift audit pass. |

M1 freezes the selected tool matrix before implementation. If later discoveries
change scoped work, update the denominator and MBT explicitly; do not keep a
near-complete percentage while accumulating more model families. Each tool's
replacement README must be sufficient to rebuild its behavior independently.

## Scientific and execution boundaries

Retain scientific meanings and units. Bulk melt viscosity does not automatically
predict formulation sprayability; small-molecule solubility is not universal polymer
compatibility; coating datasets do not establish biological performance. Represent
unsupported chemistry, missing required context and out-of-domain predictions
explicitly. Keep useful exploratory uncertainty distinct from invalid execution.

Publish endpoint-specific benchmark metrics with sample counts, splits, dataset/model
versions and limitations. R-squared and interval coverage are not percent accuracy.
Duplicate audits, negative controls and failed generalization remain visible.
Historical signatures establish neither independent scientific review nor current
v2 readiness. Do not promote a model merely because its receipt says passed.

Descriptors expose purpose, typed ports, representations, applicability, evidence,
resource/cost requirements and release identity. Planning may request a capability
or propose an existing node; it cannot make an unavailable tool executable by naming
it. New scientific code follows ordinary isolated build/test/publication gates.
No private cross-service imports, database shortcuts or new monolithic science backend.
No automatic retraining on incoming lab results or in-flight model replacement.

## Evidence lookup and verification

Start from v1/amphora-solvency-score/benchmarks/bigsoldb-v1/run_v20_lso.py;
v1/amphora-viscosity-score/evidence/phase0/kpis/;
v1/amphora-design-rule-score/benchmarks/split-integrity-dedup-v1/;
v1/amphora-barrier-corrosion-score/benchmarks/; and v1/BUILD.md for omitted data.
The analysis checkpoint identified these records; it did not rerun training or
establish deployable weights. Do not modify v1 or fetch external reference repos
without the applicable authorization.

Tests belong to each owning tool/service, grouped by model, contract, applicability
and protocol behavior. Cross-owner/browser acceptance is a separate tier. Include
schema/unit mismatches, unsupported chemistry, malformed model output, failed worker,
stale inventory, unavailable capability and version replacement. Audit both software
isolation and scientific evidence transfer before closing this standalone plan.
