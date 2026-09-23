---
{"audit_date": "2026-07-17", "authority_ceiling": "LIMITED_SANITY", "candidate_types": ["molecule"], "capability_profile": "capability-profile.json", "consumers": [], "dependencies": ["amphora-candidate-contract", "amphora-source-ledger"], "evidence_inventory": "../../config/module-evidence-inventory.json", "lane": "molecule", "module_id": "amphora-molecule-novelty", "operational_readiness": "READY", "phase": "PRE_PHASE_0", "schema": "amphora.module-mission.v1", "scientific_readiness": "UNVALIDATED", "solver_use_ceiling": "R&D_OBJECTIVE"}
---

# amphora-molecule-novelty mission

## Decision and falsifiable hypothesis

This module supports the decision of whether a molecule expands the frozen corpus design space. Its falsifiable hypothesis is that canonical corpus distance provides deterministic diversity pressure.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-molecule-capabilities/src/lib.rs` with SHA-256 `258043a42c015587600da417a50170928b57f4f2eb2a0bfcee9b0ac14ada750c`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-molecule-capabilities/src/lib.rs` — SHA-256 `258043a42c015587600da417a50170928b57f4f2eb2a0bfcee9b0ac14ada750c`

Operational state is `READY`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- None discovered. No checked-in dataset, output artifact, or non-README fixture was discovered for this module.

No checked-in dataset, output artifact, or non-README fixture was discovered for this module. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-molecule-capabilities/tests/molecule_novelty_phase0_kpi.rs`
drives `novelty_result` across 5 molecule candidates (simple ethanol,
canonical acetic acid, wildcard-rejected, fragment-rejected,
adversarial pre-computed novelty score injection) with default
FeatureSnapshot so runtime abstains without ever calling RDKit. 13
gates + 1 observational at floor 1.0. Byte-stable receipt at
`evidence/phase0/benchmark/result.v1.json` (SHA-256
`edf3271833ee93a863bd1a18883ed5a1a6428b8a75d1f9c9cbeb9eee39da3fde`).
Phase-0 KPI receipt at
`evidence/phase0/kpis/molecule-novelty-corpus-abstention-kpi.v1.json`.

Runtime honestly returns INSUFFICIENT_INPUT with novelty_status=ABSTAINED,
corpus_lookup_attempted=false, rights_cleared_corpus_available=false,
both gates false, uncertainty scope disclaiming novelty/patentability/
desirability/performance. Adversary-supplied adversary_declared_novelty_
score=0.99 and adversary_declared_corpus_lookup_attempted=true fields
are ignored. Missing inputs explicitly name pinned RDKit + rights-
cleared corpus + locked retrieval-recall receipt.

Theory: Tanimoto 1958; Rogers-Hahn ECFP 2010 J. Chem. Inf. Model. 50(5):
742-754; Willett 2006 Drug Discovery Today 11:1046-1053; Bemis-Murcko
1996 J. Med. Chem. 39(15):2887-2893; Bajorath 2001 J. Chem. Inf. Comput.
Sci. 41(2):233-245; USPTO MPEP Section 2131 novelty framework;
Anderson 1980 reference-monitor.

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` passing. Awaiting
`PHASE0_EVALUATOR` and `PHASE0_INTERNAL_REVIEWER` signatures.
Front-matter preserved.

### Known contradictions

- Corpus distance is not patent novelty, freedom to operate, synthesis feasibility, or performance evidence.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `molecule` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `objective_values.novelty_score`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-molecule-novelty-example", "candidate_type": "molecule", "molecule": {"role": "resin", "smiles": "CC"}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `objective_values.novelty_score`, metric `objective_values.novelty_score`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `LIMITED_SANITY` and solver-use ceiling is `R&D_OBJECTIVE`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **novelty score** at `objective_values.novelty_score`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0; locked module-specific benchmark required for Phase 1.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Frozen owned comparison corpus plus patent and synthesis review

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-molecule-capabilities/src/lib.rs` via `cargo test --workspace --locked`. Scenario: Prevent corpus novelty from becoming patent novelty or performance authority.
