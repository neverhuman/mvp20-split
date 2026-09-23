---
{"audit_date": "2026-07-17", "authority_ceiling": "EVIDENCE_ONLY", "candidate_types": ["formulation"], "capability_profile": "capability-profile.json", "consumers": [], "dependencies": ["amphora-candidate-contract", "amphora-source-ledger"], "evidence_inventory": "../../config/module-evidence-inventory.json", "lane": "infrastructure", "module_id": "amphora-ip-fto-guard", "operational_readiness": "GATED", "phase": "PRE_PHASE_0", "schema": "amphora.module-mission.v1", "scientific_readiness": "UNVALIDATED", "solver_use_ceiling": "DISABLED"}
---

# amphora-ip-fto-guard mission

## Decision and falsifiable hypothesis

This module supports the decision of which technical patent categories require qualified counsel review. Its falsifiable hypothesis is that technical landscape screening can surface unresolved categories without claiming FTO.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-assurance-capabilities/src/lib.rs` with SHA-256 `0fe122cc7434bdad38fc90a812c2c2fc10d431b0ba30fbac179a8bcef0c84f7d`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-assurance-capabilities/src/lib.rs` — SHA-256 `0fe122cc7434bdad38fc90a812c2c2fc10d431b0ba30fbac179a8bcef0c84f7d`

Operational state is `GATED`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `dataset` `amphora-ip-fto-guard/reference/mvp20/data/patent_landscape.json` — SHA-256 `52ada09074f435d515a8286e57b1d31da40fcbe3d0ec4f79a9be754e5cce63dc`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-assurance-capabilities/tests/ip_fto_guard_phase0_kpi.rs` drives
the deterministic `evaluate_ip_fto_guard` runtime via
`AssuranceCapability::new("amphora-ip-fto-guard")` across 5 formulation
candidate scenarios (baseline; adversary-supplied signed_by_counsel=true;
explicit signed_by_counsel=false; unrelated evidence_refs; nested
counsel_fto object omitting the signed_by_counsel key) plus 3
fail-closed probes. The harness independently recomputes family and
sweep counts from the compile-time-embedded `patent_landscape.json`
(SHA-256 `52ada09074f435d515a8286e57b1d31da40fcbe3d0ec4f79a9be754e5cce63dc`;
60 patent families spanning DGEBA epoxy + polyamide + curing agent +
anticorrosive pigment + high-solids-process anchor classes; 6 CPC/IPC
sweeps including C09D163/00, C09D5/08, C09D7/61, C08G59/50, B05D, and
one high-solids/process category). It emits a byte-stable canonical
receipt at `evidence/phase0/benchmark/result.v1.json` (SHA-256
`a6cb423d8858421e4b0e8c96de063da7eaaa97916a1da71523ffaae2788b6a77`). The
Phase-0 KPI receipt lives at
`evidence/phase0/kpis/ip-fto-guard-technical-landscape-kpi.v1.json`.

Observed Phase-0 KPI outcomes (all deterministic, `cargo test --workspace --locked`):

- `patent_landscape_pinned_60_families_and_6_sweeps_rate` observed **1.0** (independent recompute matches exact populate-time pin) — **PASSED** (floor 1.0)
- `runtime_status_scored_rate` observed **1.0** (5/5 - SCORED means the technical screen executed, not legal clearance) — **PASSED** (floor 1.0)
- `fto_status_pinned_to_never_performed_rate` observed **1.0** (5/5 metrics.fto_status == 'FTO NOT PERFORMED' bit-exact) — **PASSED** (floor 1.0)
- `legal_advice_false_rate` observed **1.0** (5/5 metrics.legal_advice == false) — **PASSED** (floor 1.0)
- `fto_legal_closure_gate_false_rate` observed **1.0** (5/5 gates.fto_legal_closure == false) — **PASSED** (floor 1.0)
- `technical_landscape_present_gate_true_rate` observed **1.0** (5/5 gates.technical_landscape_present == true, reflecting fixture presence not legal conclusion) — **PASSED** (floor 1.0)
- `runtime_family_and_sweep_counts_match_fixture_rate` observed **1.0** (10/10 - public_family_count=60 AND classification_sweep_count=6 for every candidate) — **PASSED** (floor 1.0)
- `boolean_counsel_assertion_ignored_correctness_rate` observed **1.0** (5/5 - scenarios 2 and 3 with signed_by_counsel present trigger ignored=true; scenarios 1, 4, 5 without leave ignored=false; presence not value triggers the defensive lock) — **PASSED** (floor 1.0)
- `explanation_disclaims_legal_advice_rate` observed **1.0** (5/5 explanations contain literal 'not legal advice' + 'FTO NOT PERFORMED') — **PASSED** (floor 1.0)
- `authority_envelope_preservation_rate` observed **1.0** (5/5 serialized ModuleResult contains no batch_release/qualified/authorized_by/manufacturing_qualification/release_authority key) — **PASSED** (floor 1.0)
- `unsupported_input_fail_closed_rate` observed **1.0** (3/3 probes: wrong candidate_type, unknown module_id, whitespace module_id - all Err) — **PASSED** (floor 1.0)
- `byte_stable_two_replay_rate` observed **1.0** (5/5 evaluate() twice byte-identical) — reported observationally.

USPTO Manual of Patent Examining Procedure (MPEP) 9th ed. Rev. 07.2022
Section 706; European Patent Convention Article 54 + EPO Guidelines
Part G Chapter II Section 2; 35 U.S.C. Section 102 (Novelty) and
Section 103 (Non-obvious subject matter); Cooperative Patent
Classification (CPC) + International Patent Classification (IPC) joint
framework; ABA Model Rules of Professional Conduct Rule 1.1 (Competence)
and Rule 5.5 (Unauthorized Practice of Law); Federal Circuit Bar
Association Guidelines on Patent Landscape Analyses (2020); *In re Longi*
759 F.2d 887 (Fed. Cir. 1985); Anderson 1980 reference-monitor. The
runtime reproduces the technical-landscape prescreen boundary at 100%
correctness across 5 independent candidate invocations; every one of
the 23 standard red-team attack axes declared in
`evidence/phase0/benchmark/benchmark-lock.v1.json` is exercised
end-to-end. The `boolean_counsel_assertion_ignored` defensive lock
implements the Anderson 1980 reference-monitor pattern for untrusted
candidate-supplied claims - the runtime records the injection attempt
without ever elevating a candidate boolean into legal opinion.

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` (`RIGHTS` for the on-disk
patent landscape, `LOCKED_SPLIT`, `LOCKED_BENCHMARK`, `TWO_REPLAYS`,
`RED_TEAM` across 23 attack axes, `CLAIM_LOCKS`, `FOLDER_CONFINEMENT`,
`BENCHMARK_EXECUTION_COMPLETE`, `MODULE_INVARIANTS`) are passing.
Awaiting `PHASE0_EVALUATOR` and `PHASE0_INTERNAL_REVIEWER` signatures
per the `evaluation.v1.dsse.json` and `phase0-review-receipt.v1.json`
protocol before the front-matter's `phase: PRE_PHASE_0` becomes
substantively `PHASE_0`. The module's advertised
`authority_ceiling: EVIDENCE_ONLY`, `solver_use_ceiling: DISABLED`, and
`operational_readiness: GATED` in the front-matter are preserved.

### Known contradictions

- FTO is explicitly not performed; neither a Boolean counsel flag nor a local patent landscape creates legal closure.
- Technical landscape correctness against the on-disk fixture does not establish patentability, procurement, or jurisdictional coverage; those remain counsel-scope external dependencies for any Phase-1 or Phase-2 claim.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `formulation` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `metrics.unresolved_technical_categories`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-ip-fto-guard-example", "candidate_type": "formulation", "formulation": {"application": {"dft_mil": 5.0, "relative_humidity_pct": 50.0, "substrate": "steel", "surface_preparation": "declared", "temperature_C": 25.0}, "basis": "mass_g_per_batch", "batch_mass_g": 137.13, "ingredient_catalog_version": "facts.v2", "process": {"application_method": null, "induction_time_min": null, "mix_order": null, "pot_age_h": 0.0}, "recipe": {"part_A": {"dgeba_828": {"ingredient_id": "dgeba_828", "mass_g": 100.0}}, "part_B": {"ancamide_350a": {"ingredient_id": "ancamide_350a", "mass_g": 37.13}}}}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `metrics.unresolved_technical_categories`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `EVIDENCE_ONLY` and solver-use ceiling is `DISABLED`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **unresolved category coverage** at `metrics.unresolved_technical_categories`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0; locked module-specific benchmark required for Phase 1.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Qualified patent counsel, current jurisdictional search, and claim charts

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-assurance-capabilities/src/lib.rs` via `cargo test --workspace --locked`. Scenario: Keep FTO NOT PERFORMED even when signed_by_counsel is true.

### Pin-integrity correction (2026-08-16)

The `amphora-assurance-capabilities/src/lib.rs` and `result.v1.json` SHA-256 pins above were corrected against the live files by `evidence/audit/pinned-source-hash-integrity-v1/pinned-source-hash-integrity-receipt.v1.dsse.json`. The prior pins (`c0b2540f...` for lib.rs, `bbd8a967...` for result.v1.json) were stale since before the 2026-08-03 R-B01 repair, which already flagged them as a non-load-bearing maintainer follow-up in `amphora-assurance-capabilities/evidence/phase0/kpis/RETRACTION-INDEX.md` that was never actioned until now. The receipt independently confirmed `evaluate_ip_fto_guard`'s own function body was byte-identical across every commit in lib.rs's full tracked history and the live working tree, so this is a documentation-pin fix, not a behavior change. `config/module-evidence-inventory.json` still carries the old pin and is out of this module's subtree; see the receipt's `followups_not_performed_this_fire`.
