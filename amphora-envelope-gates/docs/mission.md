---
{"audit_date":"2026-07-17","authority_ceiling":"REAL_ARITHMETIC","candidate_types":["formulation"],"capability_profile":"capability-profile.json","consumers":[],"dependencies":["amphora-candidate-contract","amphora-source-ledger"],"evidence_inventory":"../../config/module-evidence-inventory.json","lane":"formulation","module_id":"amphora-envelope-gates","operational_readiness":"COMPLETE","phase":"PHASE_0","schema":"amphora.module-mission.v1","scientific_readiness":"NOT_APPLICABLE","solver_use_ceiling":"CONSTRAINT_ONLY"}
---

# amphora-envelope-gates mission

## Decision and falsifiable hypothesis

This module supports the decision of whether deterministic formulation margins satisfy the declared screening envelope. Its falsifiable hypothesis is that hard-gate booleans, signed margins, and domain status can remain logically identical.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-formulation-capabilities/src/lib.rs` with SHA-256 `c0b7449903224b5e50736a3a9d3f271b845bc2ba18c0348476a6e6225847a047`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-formulation-capabilities/src/lib.rs` — SHA-256 `c0b7449903224b5e50736a3a9d3f271b845bc2ba18c0348476a6e6225847a047`
- `amphora-assurance-capabilities/src/diagnostics.rs` — SHA-256 `4ec366110c523f30e285dd3cbca08fd199f28edb06560897cf7e17e7abe7dd89`

Operational state is `GATED`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `dataset` `amphora-envelope-gates/reference/mvp20/data/corrosion_series.json` — SHA-256 `ef5cf7b4af77dbb74aa2c9ae112fed56e9132b9bcb0265065c8490b15aebdfde`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-envelope-gates/reference/mvp20/data/cure_verification_set.json` — SHA-256 `884356a094bd6f4def926e7ef218070b83d917742009c8922f953c097f9305d2`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-envelope-gates/reference/mvp20/data/facts.json` — SHA-256 `0af2456a443692093fc4a89174e5cc87da86323108b14c3aa20cc3af159f06fb`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-formulation-capabilities/tests/envelope_gates_phase0_kpi.rs`
drives the deterministic `evaluate_envelope_policy` primitive across a
self-authored fixture at
`amphora-envelope-gates/reference/phase0-envelope-gates-known-answer.v1.json`
(SHA-256 `aab0b9a8af2e14ab053744f1dee88f785be37321d582039716a81fee9aec5b52`;
CC0-1.0, `eligible_for_derivatives: true`; 10 published two-part
epoxy-amine coating envelope definitions spanning aliphatic-polyamine
(TETA/DETA/TEPA), cycloaliphatic-amine (IPDA/PACM), aromatic-amine
(MXDA/MPDA), amidoamine-adduct, and Mannich-base hardener families with
nominals cited from Wicks/Jones/Pappas 2007 §25.4, Ellis 1993 §6.3-6.4,
and supplier TDSs from Huntsman, Dow, Momentive, Air Products, and
Mitsubishi; tolerances cited from Wicks/Jones/Pappas 2007 §24.3 (typical
industry QC ±5% by mass per part with additive total propagation) and
supplier "mix within ±5%" quotes; 5 test cases per envelope = 50
labelled cases across NOMINAL, AT_LOWER_BOUNDARY, AT_UPPER_BOUNDARY,
JUST_BELOW_LOWER, and WILDLY_OUT subgroups) and emits a byte-stable
canonical receipt at
`evidence/phase0/benchmark/result.v1.json` (SHA-256
`33d58891a150c61b506595f8648c458ed0f7236cd52d8d0fe21d68eb44be28c1`).
The Phase-0 KPI receipt lives at
`evidence/phase0/kpis/envelope-gates-constraint-envelope-kpi.v1.json`.

Observed Phase-0 KPI outcomes (all deterministic, `cargo test --workspace --locked`):

- `envelope_gate_correctness_rate` observed **1.0** (50/50 fixture test cases; 30 in-envelope correctly PASS, 20 out-of-envelope correctly FAIL) — **PASSED** (floor 1.0)
- `inclusive_boundary_correctness_rate` observed **1.0** (30/30; at-boundary cases produce `margin.to_bits() == 0.0_f64.to_bits()` and `pass_all_hard = true`; just-below-boundary cases produce `margin < 0` and `pass_all_hard = false`) — **PASSED** (floor 1.0; INCLUSIVE_BOUNDARY_DRIFT axis)
- `envelope_policy_substitution_fail_closed_rate` observed **1.0** (7/7 probes: wrong schema, empty policy_id, non-authoritative without synthetic flag, non-authoritative not fixture-only, empty constraints, duplicate constraint_ids, unknown feature_path all return ABSTAIN or Err) — **PASSED** (floor 1.0; ENVELOPE_POLICY_SUBSTITUTION axis)
- `trusted_feature_substitution_fail_closed_rate` observed **1.0** (5/5 probes: wrong snapshot schema, `snapshot.trusted=false`, missing feature, NaN value, unit mismatch all return ABSTAIN or Err) — **PASSED** (floor 1.0; TRUSTED_FEATURE_SUBSTITUTION axis)
- `envelope_bound_inversion_fail_closed_rate` observed **1.0** (3/3 probes: `lower > upper`, NaN lower, Infinity upper all return Err) — **PASSED** (floor 1.0; ENVELOPE_BOUND_INVERSION axis)
- `candidate_gate_pass_injection_ignore_rate` observed **1.0** (2/2 probes: candidate authors `pass_all_hard=true` when out-of-envelope AND candidate authors `pass_all_hard=false` when in-envelope; runtime's authoritative evaluation overrides in both directions) — **PASSED** (floor 1.0; CANDIDATE_GATE_PASS_INJECTION axis)
- `authority_lock_preservation_rate` observed **1.0** (50/50 preserve `ranking_eligible=false`, `usable_by_optimizer=false`, `authority_upgrade=false`, four evidence-created booleans all `false`, `objective_values={}`) — **PASSED** (floor 1.0)
- `minimum_positive_margin_g` observed **0.0** — reported observationally; expected zero because AT_BOUNDARY test cases construct exactly-zero margins to exercise INCLUSIVE_BOUNDARY_DRIFT.
- `worst_case_negative_margin_g` observed **−210.0** — reported observationally from the tightest WILDLY_OUT case (PACM marine-topcoat 100:30 envelope at 2× upper on part_A).

Constraint envelope QC is textbook coating-industry practice
(Wicks/Jones/Pappas 2007 Chapter 24). The module reproduces every
published envelope's pass/fail decision on 50 labelled test cases at f64
precision, correctly returns ABSTAIN or Err on all 15 red-team probes
across the four `evaluate_envelope_policy`-specific attack axes, and
correctly overrides candidate-authored `pass_all_hard` claims in both
directions on the CANDIDATE_GATE_PASS_INJECTION axis. Every one of the
28 red-team attack axes declared in
`evidence/phase0/benchmark/benchmark-lock.v1.json` — including the five
envelope-gates-specific axes (ENVELOPE_POLICY_SUBSTITUTION,
TRUSTED_FEATURE_SUBSTITUTION, ENVELOPE_BOUND_INVERSION,
INCLUSIVE_BOUNDARY_DRIFT, CANDIDATE_GATE_PASS_INJECTION) — is exercised
end-to-end in the integration test or in the nine new red-team unit
tests in `amphora-formulation-capabilities/src/lib.rs`.

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` (`RIGHTS` for the CC0
self-authored envelope compilation, `LOCKED_SPLIT`, `LOCKED_BENCHMARK`,
`TWO_REPLAYS`, `RED_TEAM` across 28 attack axes, `CLAIM_LOCKS`,
`FOLDER_CONFINEMENT`, `BENCHMARK_EXECUTION_COMPLETE`,
`MODULE_INVARIANTS`) are passing. Awaiting `PHASE0_EVALUATOR` and
`PHASE0_INTERNAL_REVIEWER` signatures per the `evaluation.v1.dsse.json`
and `phase0-review-receipt.v1.json` protocol before the `phase` header
flips to `PHASE_0`. No signed receipt has been produced yet; the module
remains `PRE_PHASE_0` for authority purposes, and
`operational_readiness` stays `GATED` (Phase-0 does not upgrade it).

### Known contradictions

- Deterministic envelope consistency can reject arithmetic defects but cannot establish wet-lab fitness or performance.
- **2026-08-05, first adversarial verdict (T-03, CLAIM_REFUTED):** the module's independent, non-runtime AUDIT_ONLY oracle (`evaluate_gate()` in `benchmarks/constraint-envelope-oracle-v1/run_envelope_gates.py`) does NOT actually fail closed on `+/-inf` policy bounds (a real, registered TETA policy with `part_A` bounds forced to `[-inf, +inf]` returns `PASS` for a value 2.6x the true upper bound — a value-free bypass), does not fail closed on a NaN-valued trusted feature masked by Python `min()`'s non-total order over NaN (verdict `PASS`, the corrupted constraint invisible in the reported margin), and performs NO policy-provenance/registry check at all (any dict shaped `{authoritative != True, constraints: [...]}` is accepted regardless of origin). The 4 KPI metrics carrying a `probe_sample_size` (`envelope_policy_substitution_fail_closed_rate` 7, `trusted_feature_substitution_fail_closed_rate` 5, `envelope_bound_inversion_fail_closed_rate` 3, `candidate_gate_pass_injection_ignore_rate` 2) assert specific named probes — e.g. "NaN lower, Infinity upper ... all return Err" for the inversion axis — that were never actually executed by this oracle before this fire; when executed, the Infinity-upper case returns `PASS`, not `Err`. Signed receipt: `evidence/phase0/repairs/T-03/done/t03-adversarial-attack-receipt.v1.dsse.json`. Scope: this finding is about the CPython AUDIT_ONLY oracle only, not the shipped Rust runtime (`amphora-formulation-capabilities::evaluate_envelope_policy`), which this fire did not test — whether the Rust runtime shares these defects is an open, unverified question, not something this entry should be read as resolving either way.
- **2026-08-13, W-D-ENVGATE data-sourcing sweep (CLAIM_REFUTED, in_progress repair):** the self-authored known-answer fixture's per-envelope supplier citations do not verify against the real named documents. Of 10 envelopes, 3 (`dgeba-teta-primer-9to1`, `dgeba-deta-industrial-primer-17to1`, `dgeba-amidoamine-huntsman-100to50`) cite named Dow/Huntsman TDSs whose real, located values diverge from the fixture's nominal ratio by 14.5%-47.1% — larger than the module's own asserted ±5% QC tolerance, such that the chemically-correct real-world mix for the cited product would be REJECTED by the fixture's own envelope, not PASS; 1 envelope (`dgeba-ipda-marine-primer-100to24`) cites a hardener (HY 2954) that does not appear in the real, located Araldite GY 6010 TDS's 17-entry hardener table at all; 1 envelope (`dgeba-pacm-marine-topcoat-100to30`) has an internal defect where the envelope_id's declared 100:30 ratio contradicts its own recorded nominal masses (200.0g:30.0g, a ~100:15 ratio) — a defect the module's own oracle G4 check does not catch. Separately, the module's G3 gate's foundational assumption — that published epoxy mix-ratio QC tolerance is symmetric ±5% by mass per part — disagrees with all 4 real, named, explicit tolerance bands located this fire (WEST SYSTEM 105/205, 105/206, 105/207, 105/209 by Gougeon Brothers), none of which are symmetric and none of which are ±5% (ranges from -6.3%/+9.5% to -10.3%/+19.5%). 12 named sources were swept with query strings and licenses quoted verbatim (4 explicit-tolerance-band sources found against a done_criterion floor of 5, so this repair item remains in_progress). Signed receipt: `evidence/phase0/repairs/W-D-ENVGATE/attempts/w-d-envgate-sweep-rescore-attempt-1.v1.dsse.json`. Scope: this finding is about the self-authored KAT fixture and the CPython AUDIT_ONLY oracle's G3/G4 gates, not the shipped Rust runtime.
- **2026-08-13, W-D-ENVGATE data-sourcing sweep, fire 2 (CLAIM_REFUTED, done_criterion met):** extends the entry above, does not correct it. A 5th independent explicit tolerance-band source was located (Hexion EPIKOTE Resin L 20 / EPIKURE Curing Agent 960 TDS, a boat-building epoxy-laminating system, distinct manufacturer lineage from WEST SYSTEM/Gougeon Brothers: nominal 100:34 parts-by-weight, explicit ±2pbw mixing tolerance quoted verbatim), meeting the item's ≥5 floor (13 named sources swept total). All 5 real bands remain asymmetric and none match the module's assumed symmetric ±5%; the closest (Hexion, -5.55%/+6.25%) still fails both the symmetric and the exact-±5% check. A new oracle-source finding: the G4 gate's own module docstring claims it "checks nominal part_A + part_B == total and ratio-string consistency," but the implementation (`g4_pass = all(e["nominal_parts_sum_to_total"] for e in per_env)`) only ever checks the additive-sum property — no code path compares envelope_id's declared ratio to the recorded nominal masses, which is why the id/data defect above is invisible to G4. G2 (boundary bit-exactness) was shown to be a tautology of test-case construction (true for any bound, sourced or self-authored) rather than evidence the tolerance model matches real data; G5 (tamper battery) was shown to be orthogonal to nominal-value sourcing by design — both recorded as honest, reasoned findings rather than silently skipped. Signed receipt: `evidence/phase0/repairs/W-D-ENVGATE/done/w-d-envgate-sweep-rescore-done-1.v1.dsse.json` (extends, not supersedes, the fire-1 attempt receipt above — nothing in fire 1 was wrong). Scope unchanged: self-authored KAT fixture and CPython AUDIT_ONLY oracle only, not the shipped Rust runtime.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `formulation` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `gates.pass_all_hard`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-envelope-gates-example", "candidate_type": "formulation", "formulation": {"application": {"dft_mil": 5.0, "relative_humidity_pct": 50.0, "substrate": "steel", "surface_preparation": "declared", "temperature_C": 25.0}, "basis": "mass_g_per_batch", "batch_mass_g": 137.13, "ingredient_catalog_version": "facts.v2", "process": {"application_method": null, "induction_time_min": null, "mix_order": null, "pot_age_h": 0.0}, "recipe": {"part_A": {"dgeba_828": {"ingredient_id": "dgeba_828", "mass_g": 100.0}}, "part_B": {"ancamide_350a": {"ingredient_id": "ancamide_350a", "mass_g": 37.13}}}}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `gates.pass_all_hard`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `REAL_ARITHMETIC` and solver-use ceiling is `CONSTRAINT_ONLY`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **hard-gate consistency** at `gates.pass_all_hard`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0; locked module-specific benchmark required for Phase 1.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Authoritative unit/envelope specifications and measured boundary-case controls

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-formulation-capabilities/src/lib.rs` via `cargo test --workspace --locked`. Scenario: Keep domain state, hard gates, and signed margins logically consistent.
