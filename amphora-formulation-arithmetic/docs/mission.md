---
{"audit_date":"2026-07-17","authority_ceiling":"REAL_ARITHMETIC","candidate_types":["formulation"],"capability_profile":"capability-profile.json","consumers":[],"dependencies":["amphora-candidate-contract","amphora-source-ledger"],"evidence_inventory":"../../config/module-evidence-inventory.json","lane":"formulation","module_id":"amphora-formulation-arithmetic","operational_readiness":"COMPLETE","phase":"PHASE_0","schema":"amphora.module-mission.v1","scientific_readiness":"NOT_APPLICABLE","solver_use_ceiling":"OBJECTIVE"}
---

# amphora-formulation-arithmetic mission

## Decision and falsifiable hypothesis

This module supports the decision of whether a declared two-part recipe has finite internally consistent formulation arithmetic. Its falsifiable hypothesis is that cited constants and exact equations reproduce known formulation metrics.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-formulation-capabilities/src/lib.rs` with SHA-256 `8b7612325bff9830da1eebd1dc6ba4af411205581ce388c45fdc6be5356edde0`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-formulation-capabilities/src/lib.rs` — SHA-256 `8b7612325bff9830da1eebd1dc6ba4af411205581ce388c45fdc6be5356edde0`
- `amphora-assurance-capabilities/src/diagnostics.rs` — SHA-256 `bab349d7039ab3d323c3313f3edc6680932278842d6e0512d9d929dbccaf987a`

Operational state is `SHADOW`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `dataset` `amphora-formulation-arithmetic/reference/mvp20/data/corrosion_series.json` — SHA-256 `ef5cf7b4af77dbb74aa2c9ae112fed56e9132b9bcb0265065c8490b15aebdfde`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-formulation-arithmetic/reference/mvp20/data/cure_verification_set.json` — SHA-256 `884356a094bd6f4def926e7ef218070b83d917742009c8922f953c097f9305d2`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-formulation-arithmetic/reference/mvp20/data/facts.json` — SHA-256 `0af2456a443692093fc4a89174e5cc87da86323108b14c3aa20cc3af159f06fb`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-formulation-capabilities/tests/formulation_arithmetic_phase0_kpi.rs`
drives the deterministic `validate_formulation_mass` primitive across a
self-authored fixture at
`amphora-formulation-arithmetic/reference/phase0-formulation-arithmetic-known-answer.v1.json`
(SHA-256 `31c9b84c9c8c847ad72cc133d929e795bdc36e02c6a638676eb41ee87f9fd202`;
CC0-1.0, `eligible_for_derivatives: true`; 15 published two-part
epoxy-amine coating formulations spanning aliphatic-polyamine
(TETA/DETA/TEPA), cycloaliphatic-amine (IPDA/PACM/DACH), aromatic-amine
(MXDA/MPDA/MDA), amidoamine-adduct, and Mannich-base hardener families;
mass ratios cited from Wicks/Jones/Pappas 2007 Chapter 25, Ellis 1993
Chapter 6, and supplier TDSs from Huntsman, Dow, Momentive, Air
Products, and Mitsubishi; three include zero-mass optional-additive
hostile nulls) and emits a byte-stable canonical receipt at
`evidence/phase0/benchmark/result.v1.json` (SHA-256
`c5a4f9a8c273a56ae0feb34fd80c2bc1b489e55af95ddcaf6519d06b95fa0ed1`).
The Phase-0 KPI receipt lives at
`evidence/phase0/kpis/formulation-arithmetic-mass-balance-kpi.v1.json`.

Observed Phase-0 KPI outcomes (all deterministic, `cargo test --workspace --locked`):

- `mass_balance_identity_rate` observed **1.0** (15/15; `part_A + part_B − total_g = 0.0` at f64 bit precision) — **PASSED** (floor 1.0)
- `mass_balance_absolute_agreement_rate` observed **1.0** (15/15; `|computed_total_g − published_expected_g| < 1e-9`, in fact all bit-exact 0.0) — **PASSED** (floor 1.0)
- `positive_mass_ingredient_id_agreement_rate` observed **1.0** (15/15; lexicographic sorted set matches published expected) — **PASSED** (floor 1.0)
- `mass_order_drift_stability_rate` observed **1.0** (MASS_ORDER_DRIFT attack: 15 × 3 permutations → byte-identical `FormulationMassDiagnosticV1`) — **PASSED** (floor 1.0)
- `candidate_property_evidence_injection_ignore_rate` observed **1.0** (CANDIDATE_PROPERTY_EVIDENCE_INJECTION attack: 8 injected fields per formulation, 15 × 8 = 120 injection probes, all recorded in `ignored_candidate_fields` and none change computed masses) — **PASSED** (floor 1.0)
- `applicability_domain_fail_closed_rate` observed **1.0** (9/9 malformed probes: missing formulation, missing part_A, missing part_B, all-zero-mass, NaN, Infinity, negative, string-mass NUMERIC_TYPE_UNIT_CONFUSION, FINITE_SUM_OVERFLOW all return ABSTAIN or Err) — **PASSED** (floor 1.0)
- `authority_lock_preservation_rate` observed **1.0** (15/15 preserve `arithmetic_scope=MASS_ONLY`, `scientific_readiness=UNVALIDATED`, `ranking_eligible=false`, `usable_by_optimizer=false`, `candidate_created_evidence=false`, `authority_upgrade=false`, `unresolved_legacy_data_accessed=false`) — **PASSED** (floor 1.0)
- `median_mass_balance_absolute_error_g` observed **exactly 0.0 g** — mass conservation is a physical identity so a nonzero observed value would indicate a runtime bug.

Mass conservation is the fundamental invariant of formulation chemistry
(Wicks/Jones/Pappas 2007 Chapter 25; Ellis 1993 Chapter 6). The module
reproduces this identity at f64 bit precision across all 15 published
formulations, correctly separates positive-mass and zero-mass
ingredients, and correctly ignores all eight adversary-injected
scientific claim keys. Every one of the 28 attack axes declared in
`evidence/phase0/benchmark/benchmark-lock.v1.json` — including the five
arithmetic-specific axes (NUMERIC_TYPE_UNIT_CONFUSION,
CANONICAL_LEGACY_ALIAS_COLLISION, FINITE_SUM_OVERFLOW, MASS_ORDER_DRIFT,
CANDIDATE_PROPERTY_EVIDENCE_INJECTION) — is exercised end-to-end in the
integration test or in the seven new red-team unit tests in
`amphora-formulation-capabilities/src/lib.rs`.

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` (`RIGHTS` for the CC0
self-authored formulation compilation, `LOCKED_SPLIT`,
`LOCKED_BENCHMARK`, `TWO_REPLAYS`, `RED_TEAM` across 28 attack axes,
`CLAIM_LOCKS`, `FOLDER_CONFINEMENT`, `BENCHMARK_EXECUTION_COMPLETE`,
`MODULE_INVARIANTS`) are passing. Awaiting `PHASE0_EVALUATOR` and
`PHASE0_INTERNAL_REVIEWER` signatures per the `evaluation.v1.dsse.json`
and `phase0-review-receipt.v1.json` protocol before the `phase` header
flips to `PHASE_0`. No signed receipt has been produced yet; the module
remains `PRE_PHASE_0` for authority purposes, and
`operational_readiness` stays `SHADOW`.

### Known contradictions

- Computational success and in-envelope arithmetic are not formulation fitness or corrosion-performance evidence.
- **X-MASS-IDENTITY (2026-08-17, `evidence/phase0/repairs/X-MASS-IDENTITY/done/X-MASS-IDENTITY.done-receipt.v1.dsse.json`): CLAIM_REFUTED.**
  `mass_balance_identity_rate` (the first-listed metric in the signed Phase-0 KPI at
  `evidence/phase0/kpis/formulation-arithmetic-mass-balance-kpi.v1.json`, and the metric this
  document cites above as proof the module "reproduces this identity at f64 bit precision") is a
  tautology, not an empirical test. In the live Rust engine, `total_mass_g()` is defined as
  `part_a_mass_g() + part_b_mass_g()` re-evaluated, and the KPI harness's identity check
  (`(a + b).to_bits() == t.to_bits()`) reads all three of `a`, `b`, `t` off the same
  `FormulationMassDiagnosticV1` instance, i.e. compares an expression against itself. A faithful
  Python re-derivation of `RecipeObservation` (cross-validated: it reproduces the signed KPI's
  15/15 identity and 15/15 agreement exactly before any mutation) with a realistic off-by-one
  summation defect injected into `part_a_mass_g()` (silently drops the lexicographically last
  positive-mass ingredient of `part_A` from the sum while `positive_mass_ingredient_ids` still
  lists it as contributing) leaves `mass_balance_identity_rate` at 1.0/1.0 across all 15 KAT
  fixtures -- completely unmoved -- while `mass_balance_absolute_agreement_rate` (the metric that
  compares against the externally-authored `published_expected_total_g`) drops to 0.2 (3/15),
  exposing 425.0 g of silently hidden ingredient mass across 12 affected fixtures. The metric
  cannot observe a value other than 1.0 for any finite-mass input, by construction, so it
  contributes zero of the KPI's claimed independent gates; only `mass_balance_absolute_agreement_rate`
  carries the real conservation check. This does NOT show the current shipped engine has a mass-drop
  defect (agreement_rate is genuinely 1.0/15 on the real, unmutated engine) -- it shows the KPI's
  headline metric could not have caught it if it did. See the done receipt for the full structural
  proof, source citations, and defect-injection demonstration.
- **T-05 (2026-08-05, `evidence/phase0/repairs/T-05/done/T-05.done-receipt.v1.dsse.json`): CLAIM_REFUTED.**
  `EquivalentBalanceV1::from_host_facts` in `amphora-formulation-capabilities/src/lib.rs`
  (the structure-derived epoxy/amine equivalent-balance arithmetic reachable from this
  module's domain) accepts a hand-fabricated `MoleculeFactsV1` record whose
  `average_molecular_weight_g_mol` and `oxirane_ring_count` were never computed by
  RDKit, and returns a fully-computed scalar (`eew_g_per_eq`, `theoretical_hardener_phr`,
  `total_mass_g`, ...) instead of failing closed. `MoleculeFactsV1` is a plain `pub`-field
  struct with `#[derive(Deserialize)]` and carries no cryptographic host-attestation
  field; the only gate is a string/bool equality check against two constants
  (`REACTIVE_ONTOLOGY_VERSION`, `REQUIRED_RDKIT_VERSION`) that are themselves `pub`
  and trivially reproducible. Non-finite inputs, zero-group operands (no oxirane /
  no reactive amine hydrogen), and non-positive mass or ratio all correctly fail
  closed (11/11 and 3/3 respectively). The module's own mass-balance identity
  (`part_A + part_B == total_g`, the `mass_balance_identity_rate` KPI above) is
  unaffected — it is pure mass addition with no host-fact dependency — but this
  module's domain also reaches `EquivalentBalanceV1`, which is not yet closed
  against candidate-supplied constants entering the balance. See the done receipt
  for the full adversarial case log and the founder directive T2-05 citation.

- **X-COV-CPVC (2026-08-15, `evidence/phase0/repairs/X-COV-CPVC/done/X-COV-CPVC.done-receipt.v1.dsse.json`): CLAIM_REFUTED.**
  `coverage-spreading-v1` (signed 2026-07-29, `COVERAGE_SPREADING_ENGINE_READY__KNOWN_ANSWER_BATTERY_PASS__1604_ANCHOR_EXACT`) computes wet-film-thickness/theoretical-coverage from a void-free closure identity (`WFT * VS_frac == DFT` exactly) with zero PVC/CPVC awareness -- none of its 9 known-answer cases or scope notes mention pigment loading. Its own sibling receipt `reduced-pvc-porosity-v1` (signed two days later, 2026-07-31) had already established that above the Bierwagen CPVC a real dry film's volume is amplified by `LAMBDA = PVC/CPVC` versus void-free packing, and named an iron-oxide-red anti-corrosion primer at PVC 0.50 (CPVC 0.4183, `LAMBDA` 1.1953) as its own worked in-domain example -- but that finding was never propagated back into `coverage-spreading-v1` as a repair or disclosed scope boundary. This fire independently reimplemented both engines from their published source, reproduced both receipts' point estimates bit-exact, and composed them: applying `coverage-spreading-v1`'s own signed WFT prescription (190.30 um) to this in-domain porous primer at its own declared 127 um DFT target yields an actual film build of 151.79 um, a +19.53% overshoot (and a -16.33% dry-film-density error) -- about 19.5x the receipt's own `at_nominal_dft` calibrated 95% interval half-width. A below-CPVC control case (PVC 0.35) showed exactly 0.0% divergence, confirming the bias is the CPVC/porosity effect and not a reimplementation artifact. `coverage-spreading-v1` is READY only for the undisclosed below-CPVC subset of the module's declared applicability domain. See the done receipt for the full composition, reproduction checks, and proposed_followups.

- **W-T-ARITH (2026-08-13, `evidence/phase0/repairs/W-T-ARITH/done/W-T-ARITH.done-receipt.v1.dsse.json`): CLAIM_REFUTED.**
  This module's prior dimensioned-arithmetic receipts (volume solids, VOC g/L, PVC, mix-ratio, coverage/spreading -- see evidence/audit/*-v1 and amphora-redteam-audit/benchmarks/formulation-arithmetic-dimensioned-v1) were checked only against this module's own fixture, never against a named published baseline. Measured 8 normative requirements from EPA Method 24 (40 CFR Part 60 Appendix A-7, public-domain federal regulation) against the dimensioned engine: 3 CONFORMANT (mass-balance identity Eq.24-6; density round-trip / unit consistency Eq.11.3.3+12.1), 3 NOT_APPLICABLE (thin-film UV classification Eq.24-1; waterborne asymmetric confidence limits sec.9.2/12.6; volume-solids equation-level check, since Method 24 sec.11.3.4 itself delegates to 'the manufacturer's formulation' with no equation given), and 2 DIVERGENT. The load-bearing divergence: the field `voc_g_per_L_epa_method24` computes total volatile mass over volume (Wv*Dc) unconditionally, never excluding water or exempt-solvent mass (Wo*Dc) as EPA Method 24 Eq.24-3/24-4/24-5 requires the instant either is present -- because the ingredient schema has no water/exempt-solvent category at all (0/83 amphora-ingredient-library facts.json entries). A 30g-water positive-control probe against the module's own real marine-primer fixture showed a 50% VOC overstatement versus the EPA-conformant value; a zero-water control confirmed the two formulas coincide exactly when no water is present, isolating the gap. This is the same mass/volume-basis-conflation defect class previously found in amphora-known-answer-benchmarks (ARITH-A221-X70P1-VOLUME-SOLIDS, 2026-08-03). See the done receipt for all 8 requirements, evidence, and proposed_followups.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `formulation` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `metrics.gate_margins`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-formulation-arithmetic-example", "candidate_type": "formulation", "formulation": {"application": {"dft_mil": 5.0, "relative_humidity_pct": 50.0, "substrate": "steel", "surface_preparation": "declared", "temperature_C": 25.0}, "basis": "mass_g_per_batch", "batch_mass_g": 137.13, "ingredient_catalog_version": "facts.v2", "process": {"application_method": null, "induction_time_min": null, "mix_order": null, "pot_age_h": 0.0}, "recipe": {"part_A": {"dgeba_828": {"ingredient_id": "dgeba_828", "mass_g": 100.0}}, "part_B": {"ancamide_350a": {"ingredient_id": "ancamide_350a", "mass_g": 37.13}}}}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `metrics.gate_margins`, metric `metrics.gate_margins`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `REAL_ARITHMETIC` and solver-use ceiling is `OBJECTIVE`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **known-answer arithmetic error** at `metrics.gate_margins`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0; locked module-specific benchmark required for Phase 1.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `rtk cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Independent hand/spreadsheet known answers and official method definitions

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-formulation-capabilities/src/lib.rs` via `rtk cargo test --workspace --locked`. Scenario: Reject non-finite formulation arithmetic inputs.
