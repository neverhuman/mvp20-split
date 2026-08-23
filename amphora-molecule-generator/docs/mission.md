---
{"audit_date": "2026-07-17", "authority_ceiling": "ROADMAP", "candidate_types": ["molecule"], "capability_profile": "capability-profile.json", "consumers": [], "dependencies": ["amphora-candidate-contract", "amphora-source-ledger"], "evidence_inventory": "../../config/module-evidence-inventory.json", "lane": "molecule", "module_id": "amphora-molecule-generator", "operational_readiness": "ROADMAP", "phase": "PRE_PHASE_0", "schema": "amphora.module-mission.v1", "scientific_readiness": "UNVALIDATED", "solver_use_ceiling": "AUDIT_ONLY"}
---

# amphora-molecule-generator mission

## Decision and falsifiable hypothesis

This module supports the decision of which valid, diverse molecular proposals enter expert review. Its falsifiable hypothesis is that deterministic generation can improve valid unique proposal yield without sacrificing feasibility.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-molecule-capabilities/src/lib.rs` with SHA-256 `258043a42c015587600da417a50170928b57f4f2eb2a0bfcee9b0ac14ada750c`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-molecule-capabilities/src/lib.rs` — SHA-256 `258043a42c015587600da417a50170928b57f4f2eb2a0bfcee9b0ac14ada750c`

Operational state is `ROADMAP`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `dataset` `amphora-molecule-generator/reference/mvp20/data/corrosion_series.json` — SHA-256 `ef5cf7b4af77dbb74aa2c9ae112fed56e9132b9bcb0265065c8490b15aebdfde`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-molecule-generator/reference/mvp20/data/cure_verification_set.json` — SHA-256 `884356a094bd6f4def926e7ef218070b83d917742009c8922f953c097f9305d2`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-molecule-generator/reference/mvp20/data/facts.json` — SHA-256 `0af2456a443692093fc4a89174e5cc87da86323108b14c3aa20cc3af159f06fb`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-molecule-generator/reference/mvp20/data/feedback_v1/dataset_context.json` — SHA-256 `49a3f6ffd663ce136542c6efa650f881d037b3a24fede9d6b1866e7f918ab01a`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-molecule-capabilities/tests/molecule_generator_phase0_kpi.rs`
drives `generator_result` across 5 molecule candidates (simple oxirane
resin, ethylenediamine hardener, adversarial proposals injection,
adversarial availability declarations, minimal methane) with a shared
ExecutionContext (deterministic_seed=20260722, run_id='phase0-kpi-
molecule-generator'). 17 gates + 1 observational at floor 1.0.
Byte-stable receipt at `evidence/phase0/benchmark/result.v1.json`
(SHA-256
`604cd64f12ffeb66962e6b50505051717923954865f9d19f7f19c9f84ed6e8ef`).
Phase-0 KPI receipt at
`evidence/phase0/kpis/molecule-generator-roadmap-diagnostic-quarantine-kpi.v1.json`.

Runtime is a pure roadmap-diagnostic quarantine: never invokes RDKit,
never emits a proposal, always returns INSUFFICIENT_INPUT with
generation_status='LOCKED_INTERNAL', proposal_count=0. Records lineage
diagnostic (seed + candidate_id + run_id) for reproducibility.
Adversary-supplied adversary_proposals list, adversary_declared_proposal
_count, and candidate_declared availability booleans are all defensively
refused.

Theory: Corey 1969 Nobel retrosynthetic analysis; Corey-Wipke 1969
Science 166(3902):178-192; Daylight SMARTS 1997; Reymond et al. 2010
WIREs Comput Mol Sci 2(5):717-733; Segler et al. 2018 Nature 555(7698):
604-610; Todd 2005 Chem. Soc. Rev. 34(3):247-266; The Turing Way
reproducibility; ACM Artifact Review v1.1; Anderson 1980 reference-
monitor.

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` passing. Awaiting
`PHASE0_EVALUATOR` and `PHASE0_INTERNAL_REVIEWER` signatures.
Front-matter preserved.

### Known contradictions

- The current generator is deterministic rule/template code, not a trained generative model with prospective closed-loop superiority evidence.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `molecule` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `metrics.generated_count`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-molecule-generator-example", "candidate_type": "molecule", "molecule": {"role": "resin", "smiles": "CC"}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `metrics.generated_count`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `ROADMAP` and solver-use ceiling is `AUDIT_ONLY`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **chemical validity** at `metrics.generated_count`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: At least 99% validity, 95% uniqueness, deterministic lineage, scaffold-held-out controls, and expert/synthesis-feasibility noninferiority before prospective closed-loop superiority is tested.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Scaffold-held-out benchmark, expert review, and synthesis-feasibility controls

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-molecule-capabilities/src/lib.rs` via `cargo test --workspace --locked`. Scenario: Validate the checked generator fixture without inferring trained-model or performance authority.
