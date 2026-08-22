---
{"audit_date":"2026-07-17","authority_ceiling":"CRO_GATED","candidate_types":["formulation"],"capability_profile":"capability-profile.json","consumers":[],"dependencies":["amphora-candidate-contract","amphora-source-ledger"],"evidence_inventory":"../../config/module-evidence-inventory.json","lane":"infrastructure","module_id":"amphora-cro-protocol-packager","operational_readiness":"COMPLETE","phase":"PHASE_0","schema":"amphora.module-mission.v1","scientific_readiness":"NOT_APPLICABLE","solver_use_ceiling":"DISABLED"}
---

# amphora-cro-protocol-packager mission

## Decision and falsifiable hypothesis

This module supports the decision of whether a candidate-bound numeric recipe is complete enough to issue a CRO protocol. Its falsifiable hypothesis is that candidate and formula binding prevents ambiguous or nonnumeric lab packets.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-assurance-capabilities/src/lib.rs` with SHA-256 `ae46b34766f092ddd332fa617a4348c3fda5e0c2b014f54a1662004c73ae7b5d`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-assurance-capabilities/src/lib.rs` — SHA-256 `ae46b34766f092ddd332fa617a4348c3fda5e0c2b014f54a1662004c73ae7b5d`
- `amphora-assurance-capabilities/src/diagnostics.rs` — SHA-256 `bab349d7039ab3d323c3313f3edc6680932278842d6e0512d9d929dbccaf987a`

Operational state is `READY`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `output_artifact` `amphora-cro-protocol-packager/reference/mvp20/out/capture_template.json` — SHA-256 `a5c7f81c256a86b2dcae14c473ace58d16e7993ac95ae056ee7c0e2a8f7c2881` (updated 2026-08-11, CF-TEST fire 2/2 repair: gate method fixes + gates_lock + power-analysis wiring, superseding the stale `dc0b3bb4...` pin already flagged by CF-TEST fire 1); rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-cro-protocol-packager/reference/mvp20/out/cro_protocol.md` — SHA-256 `4e001dc82eac042fa90fd1164faece447e40c7ef3f0f29649dd0322e12faa0d9`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-cro-protocol-packager/reference/mvp20/out/falsification_protocol.json` — SHA-256 `79040c136af5ecfad26d81d64790416a79bd1c1ce1eb2cb9f1912b2b0a4e8658` (updated 2026-08-11, CF-TEST fire 2/2 repair: `uncertainty_status` restated honestly, `locked_rank_hash` unchanged); rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-cro-protocol-packager/reference/mvp20/out/power_analysis.json` — SHA-256 `36dfd0f7ec383c7cc31c77a3fad54d10bcba1d99f156575065d27814d7eaf9eb` (new 2026-08-11, CF-TEST fire 2/2 repair: a priori power/CI analysis, sigma assumptions cited from Floyd et al. 2009 Prog. Org. Coat. 66(1):8-34, doi:10.1016/j.porgcoat.2009.04.009, formula from Cohen 1988); rights `UNRESOLVED` (internally authored from a cited published finding plus a published statistical formula; no dataset rights question applies to the authored file itself, but no rights receipt is bound to it either.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-assurance-capabilities/tests/cro_protocol_packager_phase0_kpi.rs`
drives the deterministic `CroProtocolPackageV2` runtime (draft, validate,
sign via Ed25519 DSSE, verify_signature against TrustStore) across 5
hand-authored campaign / candidate / balance packets spanning marine
primer, industrial-maintenance topcoat, epoxy flooring, structural
adhesive, and electronic encapsulant scenarios (SHA-256 fixture handle
`72e1f99bb6c0748d9c7b0f5376b8d2c63e7932288e8e5a3e8387e23d25a7323e` for
the on-disk reference packet consumed by the meta-audit dispatcher). The
harness emits a byte-stable canonical receipt at
`evidence/phase0/benchmark/result.v1.json` (SHA-256
`dc2cb1dca3f4eb3f3291165c4cdbd28627586dec73c7119c12350087f488743e`). The
Phase-0 KPI receipt lives at
`evidence/phase0/kpis/cro-protocol-packager-signed-packet-kpi.v1.json`.

Observed Phase-0 KPI outcomes (all deterministic, `cargo test --workspace --locked`):

- `packet_draft_ok_rate` observed **1.0** (5/5 draft() succeeds) — **PASSED** (floor 1.0)
- `packet_id_matches_computed_rate` observed **1.0** (5/5 packet.packet_id == packet.computed_packet_id() recomputed via stable_hash) — **PASSED** (floor 1.0)
- `candidate_and_formula_sha256_binding_correctness_rate` observed **1.0** (5/5 candidate_sha256 and formula_sha256 bit-exact against independent recompute) — **PASSED** (floor 1.0)
- `all_eight_required_cro_claim_locks_true_rate` observed **1.0** (5/5 - NO_EXECUTION_AUTHORITY, NO_PROCUREMENT_AUTHORITY, NO_SAFETY_CLAIM, NO_SYNTHESIS_CLAIM, NO_PERFORMANCE_CLAIM, NO_QUALIFICATION_CLAIM, NO_RANKING_AUTHORITY, UNMADE_DIGITAL_PROPOSAL) — **PASSED** (floor 1.0)
- `execution_authority_locked_false_rate` observed **1.0** (5/5 execution_authorized=false, ranking_eligible=false, authority_ceiling=AUDIT_ONLY, all four review statuses frozen) — **PASSED** (floor 1.0)
- `sign_verify_round_trip_rate` observed **1.0** (5/5 Ed25519 sign followed by verify_signature against independent TrustStore returns matching key_id) — **PASSED** (floor 1.0)
- `cro_identity_hash_substitution_fail_closed_rate` observed **1.0** (3/3 probes: candidate_sha256 zeroed, candidate_binding mutated, formula_sha256 substituted - all validate Err) — **PASSED** (floor 1.0)
- `incomplete_protocol_sections_fail_closed_rate` observed **1.0** (3/3 probes: emptied custody / controls / required_outputs - all validate Err) — **PASSED** (floor 1.0)
- `false_cro_execution_fail_closed_rate` observed **1.0** (3/3 probes: execution_authorized=true, status forged, cro_acceptance forged - all validate Err) — **PASSED** (floor 1.0)
- `banned_cro_performance_claim_fail_closed_rate` observed **1.0** (4/4 probes: claim lock stripped, authority upgraded, ranking_eligible=true, claim lock value=false - all validate Err) — **PASSED** (floor 1.0)
- `cro_signature_defect_fail_closed_rate` observed **1.0** (3/3 probes: wrong-key TrustStore, post-sign mutation, absent signature - all verify_signature Err) — **PASSED** (floor 1.0)
- `cro_prose_waiver_fail_closed_rate` observed **1.0** (2/2 probes: extra "waiver" / "override_note" JSON field - both rejected at serde deserialization by #[serde(deny_unknown_fields)]) — **PASSED** (floor 1.0)
- `authority_envelope_preservation_rate` observed **1.0** (5/5 serialized CroProtocolPackageV2 contains no batch_release/qualified/authorized_by/manufacturing_qualification/release_authority key) — **PASSED** (floor 1.0)
- `byte_stable_two_replay_rate` observed **1.0** (5/5 draft() twice identical) — reported observationally.

DSSE + Ed25519 + SHA-256 canonical-JSON binding + ICH Q9(R1)/E6(R3)
protocol-lock methodology constitute the signed-packet contract theory
stack (in-toto Attestation v1.0 2020; Bernstein et al. CHES 2011 / RFC
8032 2017; NIST FIPS 180-4 2015; Merkle 1988 CRYPTO 87; ICH Q9(R1) 2023;
ICH E6(R3) 2023; FDA Contract Manufacturing Guidance 2016; NIST SP
800-53 Rev. 5 AU-6/CM-6; OWASP ASVS 4.0 V9/V10). The runtime reproduces
the signed-packet boundary on 5 independent packets at 100% correctness
and every one of the 6 module-specific attack axes declared in
`evidence/phase0/benchmark/benchmark-lock.v1.json`
(CRO_IDENTITY_HASH_SUBSTITUTION, INCOMPLETE_PROTOCOL_SECTIONS,
CRO_PROSE_WAIVER, CRO_SIGNATURE_DEFECT, FALSE_CRO_EXECUTION,
BANNED_CRO_PERFORMANCE_CLAIM) is exercised end-to-end by 18 dedicated
fail-closed probes.

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` (`RIGHTS` for the
Amphora-authored packet compilation, `LOCKED_SPLIT`, `LOCKED_BENCHMARK`,
`TWO_REPLAYS`, `RED_TEAM` across 29 attack axes, `CLAIM_LOCKS`,
`FOLDER_CONFINEMENT`, `BENCHMARK_EXECUTION_COMPLETE`,
`MODULE_INVARIANTS`) are passing. Awaiting `PHASE0_EVALUATOR` and
`PHASE0_INTERNAL_REVIEWER` signatures per the `evaluation.v1.dsse.json`
and `phase0-review-receipt.v1.json` protocol before the front-matter's
`phase: PRE_PHASE_0` becomes substantively `PHASE_0`. Until the signed
receipt lands, the module's advertised `authority_ceiling: CRO_GATED`
and `operational_readiness: READY` in the front-matter are preserved.

### Known contradictions

- A candidate- and formula-bound packet is an execution specification only; no returned CRO measurements are checked in.
- Signed-packet contract integrity (DSSE + Ed25519 + SHA-256) is not evidence that a CRO has accepted the packet or executed the protocol; those remain Phase-1 external dependencies.
- FIRST ADVERSARIAL VERDICT (2026-08-05, campaign item T-02 / founder directive T2-02): CLAIM_REFUTED. A packet-authored performance/decision threshold in `locked_numeric_thresholds`, paired with a format-valid but content-undereived `protocol_lock_sha256` (64 hex chars, never actually computed as a hash of the thresholds it claims to lock), is ACCEPTED end-to-end by `validate()`, `sign()`, and `verify_signature()`. All 8 `REQUIRED_CRO_CLAIM_LOCKS` strip/null mutations, `execution_authorized=true`, a one-byte flip of the signed DSSE payload, and an 8-alternate-encoding injection harness (16 vector/path combinations against the claim-lock and execution-authority-locked paths) all correctly fail closed -- only the threshold-binding gap survived. Signed receipt: `evidence/audit/t02-claim-lock-execution-authority-adversarial-v1/t02-claim-lock-execution-authority-adversarial-receipt.v1.dsse.json` (mirrored at `evidence/phase0/repairs/T-02/done/`). No producer or consumer in the current runtime reads `locked_numeric_thresholds`/`protocol_lock_sha256` to make a live decision, so nothing is honored today, but the signed-packet contract itself accepts an unauthenticated packet-authored threshold, which is a repair target: `protocol_lock_sha256` must become a real content hash of `locked_numeric_thresholds`, verified in `validate()`, not merely format-checked. REPAIR (W-CRO1, this fire): `validate()` now recomputes `protocol_lock_sha256` from the canonical `locked_numeric_thresholds` content via `computed_protocol_lock_sha256()` (SHA-256 over the canonicalized threshold map, same construction as `candidate_sha256`/`formula_sha256`) and rejects any mismatch with `CroProtocolPackageError::Binding`. Re-running T-02's exact probe (same test file, sha256 `7d3959863564d7a8fd04abb15e66bd9e74db6fea182d97f9fc6066ef364f3c01`) shows the previously-accepted attacker vector now fails closed (`validate_ok=false, sign_ok=false, verify_signature_ok=false, packet_authored_threshold_accepted=false`) with all 34 other probes (19 directive minus (d), 16 encoding combinations) unchanged from T-02's recorded results -- 0 regressions, two-replay byte-identical (`43bba2ec80a6f2d4006e592cf13e6cff9befaffaede80d78c651022012f5268d`). Superseding receipt: `evidence/phase0/repairs/W-CRO1/done/w-cro1-protocol-lock-content-binding-repair-receipt.v1.dsse.json`.
- CF-TEST ADVERSARIAL VERDICT (2026-08-11, campaign item CF-TEST / founder directive AMPHORA-DIRECTIVE-2026-08-09 S7): CLAIM_REFUTED. The pre-registered test plan (`reference/mvp20/out/falsification_protocol.json` + `cro_protocol.md`) and the candidate-bound data-capture template (`reference/mvp20/out/capture_template.json`) were audited against the done_criterion's 5 named axes: methods/standards named, acceptance thresholds and kill criteria locked before measurement, splits declared, uncertainty quantified, candidate-bound unit-specified capture template. 3 of 5 fail on the real, unmodified corpus: (a) 2/18 kill/acceptance gates (`early_kill_gates.gel_or_phase_split`, `acceptance_gates.raw_data_return`) cite no named external standard; (b) `falsification_protocol.json`'s barrier rank IS content-hash-locked (`locked_rank_hash` recomputed and checked, `hash_matches=true`), but no equivalent lock exists anywhere for the bench-level `early_kill_gates`/`acceptance_gates` -- the literal attack (delete the well-formed `pot_life_below_90_min` gate, method `ASTM D562`, from a copy) confirms this: the methods-named check's pass/fail verdict and its exact missing-gates list are byte-identical before and after the deletion, so nothing in this corpus detects a silently deleted kill criterion; (c) `uncertainty_status` in `falsification_protocol.json` explicitly states "no calibrated uncertainty available", and the one referenced quantification artifact, `statistical_decision_rules.power_analysis_path` ("out/power_analysis.json"), does not exist anywhere in the module. Axes C (splits: panel_plan/panel_counts/randomization/blocking) and E (candidate binding: prediction_ledger binds all 3 declared M00-series candidates 1:1, 14/14 per-candidate measurement fields carry an explicit unit) genuinely PASS. Also observed in passing: the mission-front-matter-adjacent `output_artifact` SHA-256 pin for `capture_template.json` recorded above (`dc0b3bb4...`) no longer matches the file's current on-disk hash (`4e3f2dca7d...`), i.e. that provenance pin is stale as of this fire. Signed receipt: `evidence/audit/cf-test-preregistration-completeness-v1/cf-test-preregistration-completeness-audit-receipt.v1.dsse.json` (mirrored at `evidence/phase0/repairs/CF-TEST/attempts/`). Repair target for a future CF-TEST fire (max_fires=2): name a standard for the two gates, add a content-hash lock over the bench kill/acceptance gates mirroring `locked_rank_hash`, and either produce a real power-analysis artifact or remove the dangling reference and restate `uncertainty_status` honestly.

- CF-TEST REPAIR VERDICT (2026-08-11, campaign item CF-TEST fire 2/2 / founder directive AMPHORA-DIRECTIVE-2026-08-09 S7): CLAIM_SURVIVED (repaired). All 3 axes fire-1 found failing now pass on re-running the SAME unmodified checker (`evidence/audit/cf-test-preregistration-completeness-v1/run_cf_test_completeness_audit_v1.py`, sha256 `a0af1a4c4016a4f19d7f144bdd2d350798e98f76837ae3d2cd2ae034410daf71`, unchanged from fire 1) against the repaired corpus: (a) axis A -- `early_kill_gates.gel_or_phase_split.method` now names `ASTM D562` (KU trend, consistent with the pot-life gate's own method) and `acceptance_gates.raw_data_return.method` now names `ISO 17025` (lab record-completeness/traceability/calibration-record standard); (b) axis B -- `capture_template.json` now carries `locked_gates_hash` / `gates_lock` (schema `amphora.cro-protocol-packager.gates-lock.v1`), a real sha256 content lock over `early_kill_gates`+`acceptance_gates` using the SAME construction empirically verified against `falsification_protocol.json`'s own `locked_rank_hash` (`sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()`); independently re-run beyond the checker's own (presence-only) axis-B test, deleting the fire-1 attack's exact gate (`pot_life_below_90_min`) from a copy now DOES change the recomputed hash (`cc9c9bd0...` real vs `c1ed035e...` mutated -- mismatch, i.e. detected), closing the gap fire 1 demonstrated was silent; (c) axis D -- `power_analysis.json` (new) is a real a priori, formula-based (Cohen 1988) power/confidence-interval analysis over an assumed sigma range cited from Floyd et al. 2009 (doi:10.1016/j.porgcoat.2009.04.009); `falsification_protocol.json`'s `uncertainty_status` no longer claims uncertainty is unavailable and instead states plainly that this is a PRE-MEASUREMENT, assumption-based quantification (no bench data exists yet), not a post-hoc calibrated interval -- the pre-registered DEFAULT of 6 panels/track/arm clears 80% power at every sigma tested (0.1-0.5) but the MINIMUM FLOOR of 3 drops to 68.8% power at the pessimistic end, stated honestly rather than hidden. Signed receipt: `evidence/audit/cf-test-preregistration-completeness-v1/cf-test-preregistration-completeness-repair-receipt.v2.dsse.json` (filed to `evidence/phase0/repairs/CF-TEST/done/` -- done_criterion met). Fire 1's CLAIM_REFUTED receipt remains the true historical record of the pre-repair state; it is not superseded, only built upon.
- CF-RISK REPAIR VERDICT (2026-08-11, campaign item CF-RISK fire 2/2 / founder directive AMPHORA-DIRECTIVE-2026-08-09 S7): CLAIM_SURVIVED (repaired). Fire 1 found zero of the 4 required known-failure-mode entries (pinholing, wetting, film_build, pot_life) anywhere in the module. This fire adds a "Known failure modes and application limits" section to `reference/mvp20/out/cro_protocol.md` with one fully-qualifying entry per risk (application-limit parameter most likely exceeded + numeric threshold + mitigation), grounded in SSPC-PA 1/2, ASTM D3276/D4414, NACE SP0508/ISO 8502-6, Crank (1975, *The Mathematics of Diffusion*, ISBN 0-19-853411-6), and this document's own already-cited MIL-DTL-24441/38A + D562 pot-life values, tagged MEASURED/MODELED/ASSUMED consistent with the rest of the document. Two sub-parameters (the recipe-specific pinhole WFT threshold and the recipe-specific soluble-salt tolerance) are explicitly flagged CANNOT FULLY DEFEND with a named resolving experiment rather than a guessed number. Re-running the SAME unmodified fire-1 checker (`evidence/audit/cf-risk-known-failure-modes-v1/run_cf_risk_known_failure_modes_audit_v1.py`, sha256 `252f3566092b024b2299d670423ad37cd3b831f035c1af12b4fa52522994c673`, unchanged) against the repaired corpus now reports `missing_or_unqualified_risks=[]`, byte-identical across two independent runs. Beyond that checker's own synthetic self-test, this fire ran a stronger positive control directly against the real repaired document: deleting each risk's own mitigation sentence (one at a time, from a copy) correctly flips only that risk to failing while the other 3 remain passing, with no false fire on the real, unmutated text -- an earlier draft passed the synthetic self-test while failing this real-document control (adjacent-section text leaked into the detection window) and was restructured before signing. Signed receipt: `evidence/audit/cf-risk-known-failure-modes-v1/cf-risk-known-failure-modes-repair-receipt.v2.dsse.json` (filed to `evidence/phase0/repairs/CF-RISK/done/` -- done_criterion met). Fire 1's CLAIM_REFUTED receipt remains the true historical record of the pre-repair state; it is not superseded, only built upon.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `formulation` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `gates.protocol_packet_complete`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-cro-protocol-packager-example", "candidate_type": "formulation", "formulation": {"application": {"dft_mil": 5.0, "relative_humidity_pct": 50.0, "substrate": "steel", "surface_preparation": "declared", "temperature_C": 25.0}, "basis": "mass_g_per_batch", "batch_mass_g": 137.13, "ingredient_catalog_version": "facts.v2", "process": {"application_method": null, "induction_time_min": null, "mix_order": null, "pot_age_h": 0.0}, "recipe": {"part_A": {"dgeba_828": {"ingredient_id": "dgeba_828", "mass_g": 100.0}}, "part_B": {"ancamide_350a": {"ingredient_id": "ancamide_350a", "mass_g": 37.13}}}}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `gates.protocol_packet_complete`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `CRO_GATED` and solver-use ceiling is `DISABLED`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **packet completeness** at `gates.protocol_packet_complete`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0; locked module-specific benchmark required for Phase 1.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `rtk cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- CRO execution, signed method selection, and returned candidate-bound raw data

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-assurance-capabilities/src/lib.rs` via `rtk cargo test --workspace --locked`. Scenario: Reject negative/non-finite recipe masses and candidate or formula hash mismatch.
