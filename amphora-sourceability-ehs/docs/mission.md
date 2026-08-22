---
{"audit_date": "2026-07-17", "authority_ceiling": "EVIDENCE_ONLY", "candidate_types": ["formulation"], "capability_profile": "capability-profile.json", "consumers": [], "dependencies": ["amphora-candidate-contract", "amphora-source-ledger"], "evidence_inventory": "../../config/module-evidence-inventory.json", "lane": "infrastructure", "module_id": "amphora-sourceability-ehs", "operational_readiness": "GATED", "phase": "PRE_PHASE_0", "schema": "amphora.module-mission.v1", "scientific_readiness": "UNVALIDATED", "solver_use_ceiling": "DISABLED"}
---

# amphora-sourceability-ehs mission

## Decision and falsifiable hypothesis

This module supports the decision of whether candidate-bound public evidence justifies further supplier diligence. Its falsifiable hypothesis is that exact-grade current hash-verified evidence can answer prescreen questions without procurement claims.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-assurance-capabilities/src/lib.rs` with SHA-256 `c0b2540fa84a9b8c98d2be5d82cbb1d21e9fd8b9806edad23815a0d912f4ab4d`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-assurance-capabilities/src/lib.rs` — SHA-256 `c0b2540fa84a9b8c98d2be5d82cbb1d21e9fd8b9806edad23815a0d912f4ab4d`

Operational state is `GATED`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `dataset` `amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/basf_n_butanol_sds.pdf` — SHA-256 `8c6515360cbd93d713eed892bd3187a2eee808adac2e9a222d7d7304b59a0fa9`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/byk_a_530.html` — SHA-256 `0126cd5c899573355e5e53ef553455bf6a81240c07eea4d816edf9e22fdc96e5`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/byk_disperbyk_110.html` — SHA-256 `a1a4c0cf56d7a5dfb540d400ee1d2153a0ff59bbe012621e978506a5813bb44b`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/byk_ghs_sds.html` — SHA-256 `c2387516a067c43d2785ba3991b12407b268b515a92eed4a1790b35c9966ecb9`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/dla_qpd_24441.html` — SHA-256 `98de9b235df7320f95056c2efedacfcbae9ff5ee2084e70b99e11ba5507fa83d`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/ecfr_pfas_api.json` — SHA-256 `8349e6b2e643521c8e02e70559547793ea9192bf312e7a3e9c04b71a557b4991`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/elementis_bentone_38.html` — SHA-256 `33b333255efc050be918c3352655e3eb6a90ecedf5daf2edfbb128e3b681c84a`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/epa_comptox.html` — SHA-256 `42e170f7892b9b97e0bceda2662618d32bb6e85c47d1c90241c2695b93cd1898`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/epa_tsca_inventory.html` — SHA-256 `739a8ecc8d7d0c333beb4a70a33191316688e74eb5fc4ca042908c2a18f1321c`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/evonik_ancamide_350a.html` — SHA-256 `c1a53fbda98c0f652de34a3bf1ef952077fdba31dc42f5c02930b19ec8571c0f`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/far_taa.html` — SHA-256 `1c7b4dc3da976b30824810720c0e49ecf848782cce7164c993bad52c950db7ed`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/fisher_naphtha_sds.pdf` — SHA-256 `1662e7760684df30bbe73367ad18825468dc0ece7453c62086ac8108c6984f42`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/heubach_zp10.pdf` — SHA-256 `92bd35e75c1ba4c1eeea9c8e7d91eaf6c9ae1942a7b41b020e9a0b3e324ed478`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/imerys_document_finder.html` — SHA-256 `ee7c1ad929d2e37e14afdea03da1663fe3dbeda8933ac8d1c5eab2d892d29dce`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/imerys_mica.html` — SHA-256 `4a3269fbb86d03ab3506397c9de836710a9cc056cd1f04795c5d29f5f0028567`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/imerys_talc.html` — SHA-256 `e1923246b7e6505a479930886b1fe61c310a2b5bf1b79278ac9b90e9c2ea5de7`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/lanxess_bayferrox_318.html` — SHA-256 `305b5fe43a907f23ab936f5e85dd8b295f2b5f96eb74bcf7fcf57f1c8f09baf9`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/lanxess_bayferrox_920.html` — SHA-256 `5a02e7004ff2d0df47f97dec0bd15cb57bac50f33ec75d07eb9aa7d9f5d54ca5`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/olin_epoxy_stewardship.pdf` — SHA-256 `2eef5fd84f806e40ef411feb1d1ca91d9990cca777dabf5a445fc073feb8970a`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/ussilica_minusil.html` — SHA-256 `08f9c750badbacca69ef00d5e060de736f3d62ba862cb419aa86576094fe6195`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-sourceability-ehs/reference/mvp20/data/public_sourceability/envelope65/raw/ussilica_tds_finder.html` — SHA-256 `0d85b67ce5a8253335102ed0ca86713cb31c3f568135002759e59578ac091a74`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-sourceability-ehs/reference/mvp20/out/v5_epoch30_bom_line_source_packet_matrix.json` — SHA-256 `3962c50d3f5679cbce54f2ed7e7cfa121f3e17e2e81ab92929ab32136420493c`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-sourceability-ehs/reference/mvp20/out/v5_epoch30_public_bom_sourceability_manifest.json` — SHA-256 `b6925dfad96ced53bfc463fd09f8417992ae975e4a92b53689fb4c28fbb25fa0`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-sourceability-ehs/reference/mvp20/out/v5_epoch30_public_ehs_regulatory_prescreen.json` — SHA-256 `7b5ccb002415b8dda49994db42e9a8471542317dec03589140dc771d8d6caa0a`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-sourceability-ehs/reference/mvp20/out/v5_epoch30_unresolved_supplier_declaration_gap_register.json` — SHA-256 `cbef70c1757bda50e03d318b6289e3a97051f69afba368489b37a2a3effc3377`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-assurance-capabilities/tests/sourceability_ehs_phase0_kpi.rs`
drives the deterministic `evaluate_sourceability` runtime via
`AssuranceCapability::new("amphora-sourceability-ehs")` across 5
coating-formulation candidate scenarios (baseline; adversary-supplied
signed supplier declaration asserting PFAS-free / TSCA / TAA
compliance; fake lot Certificate-of-Analysis; procurement.declared_ready
injection; minimal encapsulant) plus 3 fail-closed probes. The harness
independently recomputes source record count and SHA-256 verification
from the compile-time-embedded
`v5_epoch30_public_bom_sourceability_manifest.json` (SHA-256
`b6925dfad96ced53bfc463fd09f8417992ae975e4a92b53689fb4c28fbb25fa0`; 21
public regulatory/EHS source records covering TSCA, REACH, PFAS, TAA,
DLA, OSHA HazCom / GHS methodology anchors from EPA CompTox, TSCA
Inventory, ECFR PFAS API, FAR TAA, DLA QPD 24441, plus manufacturer
SDS/TDS from BASF, BYK, Elementis, Evonik, Fisher, Heubach, Imerys,
Lanxess, Olin, US Silica). It emits a byte-stable canonical receipt at
`evidence/phase0/benchmark/result.v1.json` (SHA-256
`189390bfa08cfda9d88895aaae8e20fd9b2db6f67d60e662f58f4bb3e4f033f2`). The
Phase-0 KPI receipt lives at
`evidence/phase0/kpis/sourceability-ehs-public-prescreen-kpi.v1.json`.

Observed Phase-0 KPI outcomes (all deterministic, `cargo test --workspace --locked`):

- `sourceability_manifest_pinned_21_records_and_sha256_verified_rate` observed **1.0** (independent recompute: 21 source_records, all_sources_have_sha256=true) — **PASSED** (floor 1.0)
- `runtime_status_failed_gates_honestly_rate` observed **1.0** (5/5 - runtime returns FAILED_GATES because public prescreen cannot grant procurement authority) — **PASSED** (floor 1.0)
- `runtime_score_pinned_zero_rate` observed **1.0** (5/5 score_0_1 = 0.0) — **PASSED** (floor 1.0)
- `sourceability_status_pinned_unresolved_rate` observed **1.0** (5/5 metrics.sourceability_status = 'UNRESOLVED') — **PASSED** (floor 1.0)
- `supply_probability_null_rate` observed **1.0** (5/5 no numeric probability asserted) — **PASSED** (floor 1.0)
- `public_corpus_rights_quarantined_rate` observed **1.0** (5/5 metrics.public_corpus_rights = 'QUARANTINED') — **PASSED** (floor 1.0)
- `public_source_record_count_pinned_21_rate` observed **1.0** (5/5 bit-exact count) — **PASSED** (floor 1.0)
- `four_procurement_gates_locked_false_rate` observed **1.0** (5/5 - exact_grade_source_present=false, current_document_present=false, signed_declaration_present=false, procurement_ready=false) — **PASSED** (floor 1.0)
- `source_hashes_verified_gate_true_rate` observed **1.0** (5/5 - hash integrity confirmed but does not equal procurement closure) — **PASSED** (floor 1.0)
- `explicit_missing_input_names_supplier_evidence_rate` observed **1.0** (5/5 - missing_inputs names candidate/supplier evidence gap) — **PASSED** (floor 1.0)
- `explanation_disclaims_procurement_and_regulatory_closure_rate` observed **1.0** (5/5 explanations contain both 'procurement' and 'regulatory') — **PASSED** (floor 1.0)
- `authority_envelope_preservation_rate` observed **1.0** (5/5 no batch_release/qualified/authorized_by/manufacturing_qualification/release_authority keys) — **PASSED** (floor 1.0)
- `unsupported_input_fail_closed_rate` observed **1.0** (3/3 probes - wrong candidate_type, unknown module_id, whitespace - all Err) — **PASSED** (floor 1.0)
- `byte_stable_two_replay_rate` observed **1.0** (5/5 evaluate() twice byte-identical) — reported observationally.

Toxic Substances Control Act of 1976 (TSCA, 15 U.S.C. §§ 2601-2697);
EPA TSCA Chemical Data Reporting Rule (40 CFR Part 711); EU Regulation
(EC) 1907/2006 REACH; OECD SIDS methodology; OSHA Hazard Communication
Standard (29 CFR 1910.1200); Globally Harmonized System of
Classification and Labelling of Chemicals (GHS, UN 2003, 10th revised
edition 2023); Trade Agreements Act of 1979 (TAA, 19 U.S.C.
§§ 2501-2581) + FAR 25.4; Defense Logistics Agency (DLA) Master
Solicitation Provisions (October 2023); ISO 14001:2015 Environmental
Management Systems; Anderson 1980 reference-monitor. The runtime
reproduces the public-prescreen quarantine boundary at 100% correctness
across 5 independent candidate invocations; every one of the 23
standard red-team attack axes declared in
`evidence/phase0/benchmark/benchmark-lock.v1.json` is exercised
end-to-end. Adversary-supplied signed supplier declarations, fake lot
CoAs, and procurement.declared_ready injections are all defensively
refused - the runtime never elevates a candidate boolean into
procurement or regulatory closure.

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` (`RIGHTS` for the 21-record
public regulatory/EHS manifest, `LOCKED_SPLIT`, `LOCKED_BENCHMARK`,
`TWO_REPLAYS`, `RED_TEAM` across 23 attack axes, `CLAIM_LOCKS`,
`FOLDER_CONFINEMENT`, `BENCHMARK_EXECUTION_COMPLETE`,
`MODULE_INVARIANTS`) are passing. Awaiting `PHASE0_EVALUATOR` and
`PHASE0_INTERNAL_REVIEWER` signatures per the `evaluation.v1.dsse.json`
and `phase0-review-receipt.v1.json` protocol before the front-matter's
`phase: PRE_PHASE_0` becomes substantively `PHASE_0`. The module's
advertised `authority_ceiling: EVIDENCE_ONLY`,
`solver_use_ceiling: DISABLED`, and `operational_readiness: GATED` in
the front-matter are preserved.

### Known contradictions

- Public prescreen records are not candidate-bound supplier declarations, procurement approval, or regulatory closure.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `formulation` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `gates.sourceability_status`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-sourceability-ehs-example", "candidate_type": "formulation", "formulation": {"application": {"dft_mil": 5.0, "relative_humidity_pct": 50.0, "substrate": "steel", "surface_preparation": "declared", "temperature_C": 25.0}, "basis": "mass_g_per_batch", "batch_mass_g": 137.13, "ingredient_catalog_version": "facts.v2", "process": {"application_method": null, "induction_time_min": null, "mix_order": null, "pot_age_h": 0.0}, "recipe": {"part_A": {"dgeba_828": {"ingredient_id": "dgeba_828", "mass_g": 100.0}}, "part_B": {"ancamide_350a": {"ingredient_id": "ancamide_350a", "mass_g": 37.13}}}}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `gates.sourceability_status`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `EVIDENCE_ONLY` and solver-use ceiling is `DISABLED`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **evidence question accuracy** at `gates.sourceability_status`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0; locked module-specific benchmark required for Phase 1.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `rtk cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Current candidate- and issuer-bound supplier declarations and lot evidence

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-assurance-capabilities/src/lib.rs` via `rtk cargo test --workspace --locked`. Scenario: Reject stale, wrong-grade, unbound, or hash-mismatched supplier evidence.

**COVERAGE-GAP FINDING (EHS-REDCHEM, 2026-08-16, CLAIM_REFUTED):** the paragraph above commits this
module's checked fixture to exercising malformed chemistry, mixtures/fragments/polymers, unit
ambiguity, zero-mass ingredients, out-of-domain inputs, group/source/time leakage, mutated sources,
computed-as-measured records, spoofed identity, authority escalation, and stripped/unknown claim
locks. A full-repository grep found exactly one test call site against this module
(`amphora-assurance-capabilities/tests/sourceability_ehs_phase0_kpi.rs:205`), and it constructs zero
cases for any of those 11 content-level axes -- only 3 dispatch-layer axes (candidate_type /
module_id validation) are actually tested (NaN/Infinity is separately guaranteed by JSON's own
grammar, not by a test, so it is not counted as a gap). Source reading plus a fresh, isolated,
byte-stable two-replay probe against the real compiled runtime (13 adversarial content variants, all
byte-identical in output to a known-good baseline) confirms the root cause: `evaluate_sourceability`
(`amphora-assurance-capabilities/src/lib.rs`) takes no candidate-derived argument at all and is
provably content-blind. The runtime's behavior under every probed axis is safe (always remains an
explicit `UNRESOLVED`/`FAILED_GATES` evidence gap, satisfying the dossier's OR-clause), but that
safety is a side effect of the module being a content-blind Phase-0 stub, not of tested defensive
logic -- the *coverage claim itself* is false as written. This fire does not modify
`evaluate_sourceability`, any KPI, gate, or `procurement_gate_outcome`, and does not edit
`amphora-assurance-capabilities/tests/` (shared crate serving 7 other modules, out of this module's
write confinement) -- disclosed and flagged for a dedicated repair fire with human-reviewed shared
test infrastructure changes. See
`amphora-sourceability-ehs/reference/mvp20/data/redchem_regression_coverage_gap_audit_receipt.v1.json`
and `evidence/phase0/kpis/RETRACTION-INDEX.md`.

## Phase-0 scientific evidence — GHS/CLP public-hazard prescreen (2026-07-23, Push #40)

Portfolio-level Phase-0 evidence: `amphora-sourceability-ehs` now carries a signed scientific receipt over 5 canonical DGEBA epoxy amine hardeners covering the real chemistry space this module gates for procurement:

- IPDA (isophorone diamine, CAS 2855-13-2)
- DDS (4,4'-diaminodiphenyl sulfone, CAS 80-08-0)
- DETA (diethylenetriamine, CAS 111-40-0)
- TETA (triethylenetetramine, CAS 112-24-3)
- m-XDA (meta-xylylenediamine, CAS 1477-55-0)

Real published GHS hazard classifications are hardcoded from **ECHA CLP Inventory** and **PubChem GHS Classifications** (public regulatory registries) — every H-statement code and pictogram is cited to its primary regulatory source in the receipt payload. No LLM-authored hazard calls, no learned parameters, no free-text extraction.

Aggregate hazard statistics (all 5 candidates):

- 4/5 corrosive (H314) — IPDA, DETA, TETA, m-XDA
- 5/5 chronic aquatic toxicity (H410 or H411/H412)
- 1/5 carcinogen (H351, DDS)
- 1/5 respiratory sensitiser (H334, m-XDA)
- Composite severity-weighted worst = m-XDA (severity 41)

Deterministic procurement gates produced per candidate — one of `CORROSIVE_PPE_PLAN_REQUIRED`, `CARCINOGEN_CAT_2_MONITORING_REQUIRED`, or `RESPIRATORY_SENSITISER_CONTAINMENT_REQUIRED`. No candidate silently passes; every candidate carries a procurement gate that must be resolved before a supplier declaration can bind.

**CORRECTION (R-N01, 2026-08-03/04):** the bullets above describe the *original* 2026-07-23 card and are now known to rest on two wrong PubChem CID citations. A falsification audit (fire 20260803T230001-1528069-969e8bc559ab, banked `evidence/phase0/repairs/R-N01/attempts/r-n01-fire1-ghs-clp-cid-attribution-audit-rebank-receipt.v1.dsse.json`) found that IPDA's card cited PubChem CID 6944 (actually 1-methyl-2-nitrobenzene, an unrelated nitro-aromatic; CAS-correct CID is 17857) and m-XDA's card cited PubChem CID 15642 (actually diethoxyphosphorylbenzene, an unrelated organophosphate ester; CAS-correct CID is 15133). A superseding hazard-card correction (fire 20260804T000002-2308526-2dcfeb8b9703, `evidence/phase0/repairs/R-N01/done/r-n01-fire2-ghs-clp-hazard-card-correction-receipt.v1.dsse.json`) independently re-fetched both endpoints (PUG-REST CAS→CID, PUG-View CID→GHS Classification) live on 2026-08-04 and found: **m-XDA's H334 (respiratory sensitiser) flag does NOT appear in the CAS-correct record (CID 15133)** — it is absent from both the correct CID's own aggregate and the wrongly-cited CID's own aggregate, so it traces to neither. m-XDA's procurement gate therefore changes from `RESPIRATORY_SENSITISER_CONTAINMENT_REQUIRED` to `CORROSIVE_PPE_PLAN_REQUIRED` (H314 still present). This is the only gate change among the 5 candidates — IPDA's gate stays `CORROSIVE_PPE_PLAN_REQUIRED` (H314 still present at the correct CID) despite its own CID citation being wrong; DDS/DETA/TETA were never CID-mismatched and are unchanged. Current portfolio-relied-upon gate count: 4 `CORROSIVE_PPE_PLAN_REQUIRED` (IPDA, DETA, TETA, m-XDA), 1 `CARCINOGEN_CAT_2_MONITORING_REQUIRED` (DDS), 0 `RESPIRATORY_SENSITISER_CONTAINMENT_REQUIRED`. The original receipt and KPI below are left byte-intact (supersede-never-rewrite); see `evidence/phase0/kpis/RETRACTION-INDEX.md`.

**RE-VERIFICATION (X-EHS-CID, 2026-08-14):** founder-directive-scoped (AMPHORA-DIRECTIVE-2026-08-05 A.3) independent re-derivation of R-N01 fire 2's correction from a FRESH live PubChem fetch 10 days later (new HTTP round-trip, distinct from both R-N01 fires; `evidence/phase0/repairs/X-EHS-CID/done/x-ehs-cid-done-receipt.v1.dsse.json`). Reproduces exactly: IPDA's CAS-correct CID 17857, m-XDA's CAS-correct CID 15133, DDS/DETA/TETA's CIDs unchanged (2955/8111/5565); no additional gate change beyond the m-XDA one R-N01 fire 2 already made; R-N01 fire 2's DSSE signature independently reverifies against the pinned PHASE0_EVALUATOR key; the solver-lab P3 demo's caveat is live-confirmed RESOLVED. **New disclosure, not actioned:** re-deriving H-statement codes purely from each candidate's own PubChem notification-aggregate (the same group already cited in `pubchem_notifications_summary`) shows DDS/DETA/TETA's *current* cards diverge from that aggregate — already flagged for DDS by R-N01 fire 2 (reproduced identically today, not new drift); this fire extends the observation to DETA and TETA, neither of which fire 2 checked (their CIDs were never wrong). Most notable: DETA's live aggregate (3716 reports / 49 notifications) additionally carries H318 (serious eye damage), **H330 (Fatal if inhaled)**, and H335 (respiratory irritation), none of which are on DETA's card today; this KPI's `gate_rule` also has no branch for H330/H331/H332 acute-inhalation-toxicity codes at all. Not actioned here — flagged for a dedicated future falsification fire against the H-statement-derivation methodology and gate-rule coverage, to avoid an unreviewed change to a procurement-safety-relevant gate. See `evidence/phase0/kpis/RETRACTION-INDEX.md`.
**GATE-RULE FINDING (Y-EHS-GATE, 2026-08-14, CLAIM_REFUTED):** the X-EHS-CID disclosure above flagged, but did not act on, the fact that this KPI's `gate_rule` has no branch for H330/H331/H332 (acute-inhalation-toxicity) codes. A dedicated falsification fire sharpened that aside into a mechanically-proven defect: m-XDA's *current authoritative* card (R-N01 fire 2's correction, byte-reverified by X-EHS-CID) already carries **H330 "Fatal if inhaled"**, H331, and H332 — added to the card by R-N01 fire 2 itself from a 1105-report/43-notification ECHA aggregate, corroborated by the GHS06 skull-and-crossbones pictogram already present in `ghs_pictograms_live`. Applying `gate_rule` exactly as documented, m-XDA's `procurement_gate_outcome` is `CORROSIVE_PPE_PLAN_REQUIRED` — identical to IPDA's, DETA's, and TETA's outcome, none of which carry any acute-inhalation-lethality hazard code at all. An ablation test (removing H330/H331/H332 from m-XDA's code set, holding everything else fixed) leaves the computed gate unchanged, proving the rule is structurally blind to this hazard class: a candidate documented as "Fatal if inhaled" receives no procurement-gate signal distinguishing it from one whose worst hazard is skin corrosion. A fresh independent 2026-08-14 live re-fetch of CID 15133 reproduces the identical code set today (not stale/reverted). Per this module's conservative-default rule (established W-EHS1), this finding is **disclosed and flagged, not acted on**: m-XDA's h_statement_codes and procurement_gate_outcome are unchanged by this fire, and no branch is added to `gate_rule` here — that is left for a dedicated, reviewed repair fire. See `evidence/phase0/repairs/Y-EHS-GATE/done/y-ehs-gate-done-receipt.v1.dsse.json` and `evidence/phase0/kpis/RETRACTION-INDEX.md`.

**H-STATEMENT COMPLETENESS AUDIT (EHS-HCOMP, 2026-08-15, CLAIM_REFUTED):** closes the "dedicated future falsification fire against the H-statement-derivation methodology" that both X-EHS-CID and Y-EHS-GATE above flagged and declined to action. Ran that fire: independent fresh live PubChem PUG-View fetch (2026-08-15, a third independent HTTP round-trip after R-N01 fire 2's 2026-08-04 and X-EHS-CID's 2026-08-14), matched by report/notification count to the exact aggregate each card already cites in its own `pubchem_notifications_summary`. **DETA's card omits H318 (68.3% of reports), H330 "Fatal if inhaled" (71.7%), and H335 (70.7%)** — all majority-prevalence codes in the aggregate the card itself cites as its source. **TETA's card omits H318 (39.4%)** and states a chronic-aquatic-toxicity tier (H411) that its own cited majority aggregate does not support (the aggregate reports H412, a lower severity tier, at 99.5%). Both findings reproduce byte-for-byte across two independent fetches a day apart (this fire's raw data vs. X-EHS-CID's already-committed 2026-08-14 raw data) and do NOT reproduce on IPDA or m-XDA (negative control: re-running the identical audit against the two cards R-N01 fire 2 actually re-derived from PubChem finds zero missing codes for either) — ruling out a methodology artifact. Neither procurement gate changes: `gate_rule`'s H314 branch already fires for both candidates regardless of the omitted codes, the same structural blind spot Y-EHS-GATE proved on m-XDA, now shown to also mask a card-completeness defect on DETA (which independently carries H330 "Fatal if inhaled") and TETA. Disclosure only, per the conservative-default rule established by W-EHS1: DETA/TETA's `h_statement_codes` and `procurement_gate_outcome` are unchanged by this fire. See `reference/mvp20/data/deta_teta_h_statement_completeness_audit_receipt.v1.json` and `evidence/phase0/kpis/RETRACTION-INDEX.md`.

**RECONCILIATION (W-EHS1, 2026-08-05):** R-N01 fire 2 above left one aside unresolved: PubChem CID 2955's (DDS) own live aggregate does not carry H351, and DDS's H351 flag traces to a separately-cited "IARC Monograph Vol. 24 (1980)" source. A falsification/repair fire (`evidence/phase0/repairs/W-EHS1/done/w-ehs1-dds-h351-iarc-pubchem-reconciliation-receipt.v1.dsse.json`) fetched both sources live and independently on 2026-08-05: PubChem CID 2955's aggregate still does not carry H351 (H302, H371, H373, H411 only), and IARC's own official live classification data confirms CAS 80-08-0 (Dapsone) is Group 3 — "not classifiable as to its carcinogenicity to humans" — last evaluated 1987 (Vol. 24 + Suppl. 7), unchanged since. Group 3 is IARC's own negative/inconclusive bottom line, not a Group 1/2A/2B suspected-or-probable-carcinogen finding, so **neither cited source substantiates H351** as originally cited; the original card's "IARC Group 3" citation for a "suspected carcinogen" flag is a source-to-claim mapping error, not two sources genuinely disagreeing. Per the stated conservative-default rule (a hazard flag whose citation is in question must never silently resolve to the permissive reading), this fire does **not** strip H351 or change DDS's gate — `CARCINOGEN_CAT_2_MONITORING_REQUIRED` is kept, flagged for mandatory human toxicological review before any relaxation. Gate counts in this section (4 `CORROSIVE_PPE_PLAN_REQUIRED`, 1 `CARCINOGEN_CAT_2_MONITORING_REQUIRED`, 0 `RESPIRATORY_SENSITISER_CONTAINMENT_REQUIRED`) are unchanged by this reconciliation.

### Signed artifacts

- **Scientific receipt**: `amphora-sourceability-ehs/reference/mvp20/data/ghs_clp_public_hazard_prescreen_5_canonical_epoxy_amines_receipt.v1.json` — SHA-256 `ebeef1927ee43782a77d0735c90845b63bc651ad7c67c395b2a7d750c96b3411` (DSSE Ed25519, byte-stable two-replay verified)
- **Phase-0 KPI receipt**: `amphora-sourceability-ehs/evidence/phase0/kpis/ghs-clp-public-hazard-prescreen-5-canonical-epoxy-amines-kpi.v1.json` — SHA-256 `86528e37afc02d4010fac0051b256078222803ee194fb9d1131caca5a035f102` (9/9 deterministic gates passed)
- **Master portfolio manifest** (v40, 66 receipts across 11 modules): `amphora-molecule-property/reference/mvp20/data/amphora_coating_scientific_receipts_manifest.v1.json` — SHA-256 `f5623b3171d65de2dc805b740aef71ad6163554dcf9b5b394d84181b3ad6bf08`

### Phase-0 KPI gates (9/9 passed)

1. `n_candidates_at_least_5` — observed 5, floor 5
2. `all_candidates_have_h_statements` — observed 5/5
3. `corrosive_H314_flagged_in_majority` — observed 4/5, floor ≥3
4. `chronic_aquatic_toxicity_flagged_universally` — observed 5/5, floor 5
5. `carcinogen_flag_documented` — observed 1/5 present, floor ≥1
6. `respiratory_sensitiser_flag_documented` — observed 1/5 present, floor ≥1
7. `procurement_gates_produced_per_candidate` — observed 5/5
8. `regulatory_sources_cited_per_candidate` — observed 5/5
9. `scientific_receipt_hash_bit_stable` — observed 1.0 (two-replay SHA-256 match)

### Authority ceiling (unchanged, explicit)

The signed evidence establishes that the GHS/CLP prescreen deterministically emits a per-candidate procurement gate anchored in cited public regulatory data. It does **not** establish:

- product qualification, batch release, or lot certification;
- procurement approval (a candidate- and issuer-bound signed supplier declaration is still required);
- freedom to operate (patent-legal analysis is separate);
- REACH/TSCA/PFAS/TAA compliance closure (module still emits `FAILED_GATES` for these);
- wet-lab performance or coating-stack qualification.

`authority_ceiling: EVIDENCE_ONLY`, `solver_use_ceiling: DISABLED`, and `operational_readiness: GATED` remain in the front-matter. `phase: PHASE_0` and `scientific_readiness: LOCKED_INTERNAL` reflect the newly signed portfolio evidence. Phase 1 promotion still requires the locked module-specific human-parity benchmark called out in the KPI register.

### Red-team focus for this receipt

- **Hazard-set spoofing**: any H-statement or pictogram edit is caught by the DSSE signature over the canonical JSON receipt. Two-replay byte-stability gate (SHA-256 `ebeef1927ee43782a77d0735c90845b63bc651ad7c67c395b2a7d750c96b3411`) forces regeneration to reproduce the exact same bytes.
- **Selective candidate omission**: floor of ≥5 candidates on `n_candidates_at_least_5` prevents narrowing the panel to hide worst-case hazards.
- **Regulatory-source stripping**: `regulatory_sources_cited_per_candidate` floor of 5/5 blocks removing citations to make hazard calls appear self-authored.

