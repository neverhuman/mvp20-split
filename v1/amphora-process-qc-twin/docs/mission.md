---
{"audit_date":"2026-07-17","authority_ceiling":"EVIDENCE_ONLY","candidate_types":["formulation"],"capability_profile":"capability-profile.json","consumers":[],"dependencies":["amphora-candidate-contract","amphora-source-ledger"],"evidence_inventory":"../../config/module-evidence-inventory.json","lane":"performance","module_id":"amphora-process-qc-twin","operational_readiness":"OPEN","phase":"PHASE_0","schema":"amphora.module-mission.v1","scientific_readiness":"LOCKED_INTERNAL","solver_use_ceiling":"AUDIT_ONLY"}
---

# amphora-process-qc-twin mission

## Decision and falsifiable hypothesis

This module supports the decision of which batches require review without granting release authority. Its falsifiable hypothesis is that a prospective detector can recall seeded deviations with few false alarms and no false releases.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-formulation-capabilities/src/lib.rs` with SHA-256 `c0b7449903224b5e50736a3a9d3f271b845bc2ba18c0348476a6e6225847a047`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-formulation-capabilities/src/lib.rs` — SHA-256 `c0b7449903224b5e50736a3a9d3f271b845bc2ba18c0348476a6e6225847a047`

Operational state is `OPEN`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `output_artifact` `amphora-process-qc-twin/reference/mvp20/out/capture_template.json` — SHA-256 `dc0b3bb461446abb94a61ff624579c0d8eb059327a66998eaaea2261bc283e6d`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-formulation-capabilities/tests/process_qc_twin_phase0_kpi.rs`
drives the deterministic `audit_process_qc` capability (Individuals /
Moving-Range Shewhart 3-sigma; EWMA lambda=0.2, L=3; standardized tabular
CUSUM k=0.5, h=5) across a self-authored fixture at
`amphora-process-qc-twin/reference/phase0-process-qc-twin-known-answer.v1.json`
(SHA-256 `e82caba394d7c4e74d81b7ea86cbd39dfa5922028391f1c47e59f5b64bd1aa3c`;
CC0-1.0, `eligible_for_derivatives: true`; 10 SPC universes: 4
stable-control + 4 seeded step-shift + 1 linear drift + 1 isolated
outlier; baselines 20-25 obs, monitoring 20-50 obs, values from the
closed-form pattern `mu=100 + ((seq-1) mod 5 - 2)*0.1`) and emits a
byte-stable canonical receipt at
`evidence/phase0/benchmark/result.v1.json` (SHA-256
`4f9f97a2e621a0336fe091ef632af3f34a009be69873e605a85ef6e5b070baf9`). The
Phase-0 KPI receipt lives at
`evidence/phase0/kpis/process-qc-twin-spc-audit-kpi.v1.json`.

Observed Phase-0 KPI outcomes (all deterministic, `cargo test --workspace --locked`):

- `shewhart_control_limit_arithmetic_correctness_rate` observed **1.0** (10/10; harness independently recomputes mu, sigma, UCL, LCL, and the Shewhart alert list and asserts bit-exact equality against runtime) — **PASSED** (floor 1.0)
- `ewma_recursion_arithmetic_correctness_rate` observed **1.0** (10/10; independent recompute of `z_t = 0.2*x_t + 0.8*z_{t-1}` with closed-form `L_t = 3*sigma*sqrt((0.2/1.8)*(1 - 0.8^(2t)))` matches runtime bit-exact) — **PASSED** (floor 1.0)
- `cusum_tabular_arithmetic_correctness_rate` observed **1.0** (10/10; independent recompute of standardized tabular CUSUM with reset-on-alert matches runtime bit-exact) — **PASSED** (floor 1.0)
- `seeded_shift_detection_recall_rate` observed **1.0** (6/6 seeded universes each produce at least one alert across Shewhart + EWMA + CUSUM) — **PASSED** (floor 1.0)
- `stable_process_false_positive_absence_rate` observed **1.0** (4/4 stable universes produce zero alerts across all three detectors) — **PASSED** (floor 1.0)
- `specification_control_separation_correctness_rate` observed **1.0** (2/2; SPEC_ONLY_FAIL universe emits spec failures with empty control channels, CONTROL_ONLY_FAIL universe emits control alerts with empty spec channel) — **PASSED** (floor 1.0)
- `reordered_batches_fail_closed_rate` observed **1.0** (3/3 probes: baseline swap, monitoring swap, monitoring reversed - all Err) — **PASSED** (floor 1.0)
- `baseline_contamination_fail_closed_rate` observed **1.0** (3/3 probes: monitoring first-seq equal, below, and mid-baseline vs. baseline last-seq - all Err) — **PASSED** (floor 1.0)
- `time_leakage_fail_closed_rate` observed **1.0** (3/3 probes: duplicate seq in baseline, duplicate seq in monitoring, boundary equality - all Err) — **PASSED** (floor 1.0)
- `authority_lock_preservation_rate` observed **1.0** (10/10; `detector_status == "AUDIT_ONLY"` bit-exact and no `batch_release`/`qualified`/`authorized`/`manufacturing_qualification`/`release_authority` key anywhere in serialized SpcAuditResultV1) — **PASSED** (floor 1.0)
- `byte_stable_two_replay_rate` observed **1.0** (10/10 back-to-back invocations byte-identical) — reported observationally.

Statistical Process Control on Individuals data with Shewhart 3-sigma
plus EWMA and CUSUM is the industrial-standard quality-audit stack
(Shewhart 1931 Ch. III; Roberts 1959 *Technometrics* 1(3):239-250; Page
1954 *Biometrika* 41(1/2):100-115; Montgomery 2020 *Introduction to
Statistical Quality Control* 8th ed. Ch. 6/9; NIST/SEMATECH e-Handbook
Sec. 6.3.2; Juran 1999 Sec. 45). The runtime reproduces the
three-detector arithmetic on 10 labelled SPC universes at 100%
correctness via an independent Rust recompute, and every one of the 28
red-team attack axes declared in `evidence/phase0/benchmark/benchmark-lock.v1.json`
is exercised end-to-end - the five module-specific axes
(TIME_LEAKAGE, BASELINE_CONTAMINATION, REORDERED_BATCHES,
SPECIFICATION_CONTROL_CONFLATION, UNAUTHORIZED_RELEASE) each land at 100%
fail-closed on 3 dedicated probes in the integration test and are
additionally covered by 7 new red-team unit tests in
`amphora-formulation-capabilities/src/lib.rs`.

### ARL characterization KPI

A second, consolidated Phase-0 KPI surface at
`evidence/phase0/kpis/arl-characterization-consolidated-kpi.v2.json` (campaign
item W-QC; supersedes the v1.json built under V1-KPI-QC -- see
`evidence/phase0/kpis/RETRACTION-INDEX.md` -- v1 remains on disk unmodified)
indexes this module's five signed AUDIT_ONLY ARL (average-run-length)
degradation characterization receipts under `evidence/audit/`:
known-parameter Shewhart/EWMA/CUSUM anchors validated against Montgomery
(2020) Table 9.4 and Siegmund (1985); estimated-parameter Shewhart
degradation under both the sample-S/c4 and moving-range MRbar/d2 sigma
estimators; and estimated-parameter EWMA/CUSUM (memory-detector) union
degradation under both S/c4 and MRbar/d2. It restates already-measured values
only; no new model is fit. Headline: at the module's m=20-25 pilot baseline,
guaranteed (5th-percentile) in-control run length retains only ~7.6-8.9% of
the known-parameter value at m=30 under MRbar/d2 (worse than ~9.5-13.3% under
S/c4, as expected since MRbar/d2 has fewer effective degrees of freedom).
The MRbar/d2 x EWMA/CUSUM cross is now CLOSED
(`evidence/audit/mr-memory-detector-arl-degradation-v1/`, CLAIM_SURVIVED): the
locked <=1.5-expected-false-alarm/30-batch union budget at baseline m=50 is
1.44946 under MRbar/d2 (vs 1.10155 under S/c4) -- still inside budget, and the
smallest tabulated baseline meeting it is m=50 under either estimator,
unchanged. This KPI grants no release, qualification, or regulatory
authority.

### AR(1) autocorrelation x tamper-corpus adversarial test (campaign item T-10) -- CLAIM_REFUTED

The consolidated ARL KPI above (and all five receipts it indexes) assumes
i.i.d. normal in-control data; every one of those receipts explicitly flags
autocorrelation as an unmodeled, open gap. A first adversarial attack
(evidence/audit/ar1-estparam-drift-corpus-v1/, CLAIM_REFUTED) closes that
gap and REFUTES two claims that gap was propping up: (1) the m=50 baseline
that mr-memory-detector-arl-degradation-v1 reported as "still meets the
locked <=1.5 expected-false-alarm/30-batch budget" breaches that budget in
all 9 tested AR(1) cells (phi in {0.2,0.4,0.6} x 3 detector arms) once mild
AR(1) autocorrelation is present, with P(false alarm in 30 batches) rising as
high as 0.62 against the 0.05 budget; (2) a 128-case tamper corpus (persistent
mean-shift tampers masked as sensor noise, keyed to 60 pinned canonical
seeds, 100% byte-identical two-replay determinism) measures the module's
locked >=90% seeded-shift recall target at only 0.828 under estimated-
parameter + AR(1) stress -- 22/128 tampers were masked as noise. The harness's
known-parameter anchor gate passed (<=4.3% MC error vs Montgomery/Siegmund/
Shewhart published theory) and a 6-sigma positive-control shift was detected
immediately, so this is not an artifact of a broken detector. Non-normality
and higher-order autocorrelation (MA/ARMA) remain open. This receipt grants
no release, qualification, or regulatory authority.

### NIST/SEMATECH primary-baseline audit (campaign item W-T-QC) -- CLAIM_REFUTED

Every theory-baseline comparison above (spc-arl-characterization-v1, T-10) cited
paid sources exclusively -- Montgomery (2020) and Siegmund (1985) -- and had never
been checked against a named, freely-verifiable published baseline. A first check
against the NIST/SEMATECH e-Handbook of Statistical Methods Sec. 6.3.2 (public
domain, DOI 10.18434/M32189; `evidence/phase0/repairs/W-T-QC/done/`, CLAIM_REFUTED)
enumerated 7 normative requirements across Shewhart/EWMA/CUSUM known-parameter ARL:
6/7 are conformant (Shewhart ARL0=370.37 and shifts 0.5/1.0/2.0-sigma; the EWMA
lambda=1 limiting case; CUSUM h=5,k=0.5 at shift=1.0-sigma), but one CUSUM cell
(h=5,k=0.5, shift=0.5-sigma) diverges 26.7% from the real NIST table value (30.0)
against the prior receipt's asserted 38.0 -- outside that gate's own declared 6%
tolerance. Because this is a known-parameter comparison (no estimation involved),
the divergence cannot be an estimated-parameter effect; it is classified a
citation/baseline-sourcing defect in the prior receipt's `cusum_siegmund_vs_
montgomery_table_9_4` gate, filed as proposed_followups[F1] pending a dedicated
repair fire (supersede-never-rewrite; spc-arl-characterization-v1 remains
byte-intact on disk). See `evidence/phase0/kpis/RETRACTION-INDEX.md`.

### Sigma-estimator attribution parity audit -- CLAIM_REFUTED

Every estimated-parameter receipt above (`estparam-arl-degradation-v1`,
`moving-range-arl-degradation-v1`, `estparam-memory-detector-arl-degradation-v1`,
`mr-memory-detector-arl-degradation-v1`) labels `MRbar/d2(2)` "the estimator
the Individuals chart actually defaults to (operating estimator)" and labels
`S/c4(m)` merely "an upper bound, not the operating estimator." A parity audit
(`evidence/audit/sigma-estimator-attribution-parity-v1/`, CLAIM_REFUTED) checked
that attribution against the live, checked implementation
(`amphora-formulation-capabilities/src/lib.rs::audit_process_qc`) and found it
false: the runtime computes plain, uncorrected sample standard deviation over
the full baseline window (Bessel `n-1` variance, square-rooted) -- no moving
range is ever computed. This is independently corroborated by the module's own
bit-exact Phase-0 independent-recompute gate
(`amphora-formulation-capabilities/tests/process_qc_twin_phase0_kpi.rs::independent_mean_sigma`,
doc-commented "sample stdev"). On the module's own closed-form sawtooth
fixture the three candidate estimators (raw S, S/c4, MRbar/d2) sit within
~11% of one another, masking the mislabeling; on a physically realistic
drifting baseline (e.g. a pilot-onboarding warm-up transient), a live
`cargo test` run shows raw S diverges from MRbar/d2 by +246% while tracking
S/c4 (-1.3%) -- the opposite of the attacked receipts' classification. The
consequence is real, not cosmetic: a genuine out-of-control shift that a
correctly MRbar/d2-attributed 3-sigma limit would flag is missed by all
three live detectors (Shewhart, EWMA, CUSUM) under that same drifting
baseline, because raw S inflates with baseline drift in a way MRbar/d2 does
not. No receipt on file has characterized ARL/false-alarm/recall degradation
under the estimator the runtime actually uses (raw, uncorrected sample S);
the consolidated ARL-characterization KPI v2 above has, since its first fire,
characterized an estimator (MRbar/d2) the deployed code does not implement.
This does not modify, delete, or re-sign any prior receipt (supersede-never-
rewrite; all remain byte-intact on disk) and grants no release, qualification,
or regulatory authority. See `evidence/phase0/kpis/RETRACTION-INDEX.md`.

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` (`RIGHTS` for the CC0
self-authored SPC compilation, `LOCKED_SPLIT`, `LOCKED_BENCHMARK`,
`TWO_REPLAYS`, `RED_TEAM` across 28 attack axes, `CLAIM_LOCKS`,
`FOLDER_CONFINEMENT`, `BENCHMARK_EXECUTION_COMPLETE`,
`MODULE_INVARIANTS`) are passing. Awaiting `PHASE0_EVALUATOR` and
`PHASE0_INTERNAL_REVIEWER` signatures per the `evaluation.v1.dsse.json`
and `phase0-review-receipt.v1.json` protocol before the `phase` header
becomes substantively - rather than aspirationally - `PHASE_0`. Until
the signed receipt lands, the module's advertised `phase: PRE_PHASE_0`
and `operational_readiness: OPEN` in the front-matter are preserved as
targets; this Phase-0 push lands the deterministic KPI receipt that will
make the target substantive at the moment of signing.

### Known contradictions

- No prospective 30-batch pilot is checked in, and the module has no manufacturing or batch-release authority.
- Structural correctness of Shewhart/EWMA/CUSUM arithmetic under owned synthetic universes does not establish real-batch acceptability, EHS acceptability, or qualification.
- The consolidated ARL-characterization KPI's estimated-parameter figures are labeled by sigma estimator (S/c4 vs MRbar/d2), but neither label matches the live runtime's actual estimator (plain uncorrected sample S); see the sigma-estimator attribution parity audit above. The runtime's true operating ARL/false-alarm/recall degradation under raw S remains uncharacterized.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `formulation` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `metrics.detector_status`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-process-qc-twin-example", "candidate_type": "formulation", "formulation": {"application": {"dft_mil": 5.0, "relative_humidity_pct": 50.0, "substrate": "steel", "surface_preparation": "declared", "temperature_C": 25.0}, "basis": "mass_g_per_batch", "batch_mass_g": 137.13, "ingredient_catalog_version": "facts.v2", "process": {"application_method": null, "induction_time_min": null, "mix_order": null, "pot_age_h": 0.0}, "recipe": {"part_A": {"dgeba_828": {"ingredient_id": "dgeba_828", "mass_g": 100.0}}, "part_B": {"ancamide_350a": {"ingredient_id": "ancamide_350a", "mass_g": 37.13}}}}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `metrics.detector_status`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `EVIDENCE_ONLY` and solver-use ceiling is `AUDIT_ONLY`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **seeded-control recall** at `metrics.detector_status`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Prospective 30-batch pilot with seeded-control recall >= 90%, false alarms <= 5%, and zero false releases.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Prospective time-ordered 30-batch pilot with seeded controls

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-formulation-capabilities/src/lib.rs` via `cargo test --workspace --locked`. Scenario: Detect seeded controls without granting batch-release authority.
