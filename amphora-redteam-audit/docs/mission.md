---
{"audit_date":"2026-07-17","authority_ceiling":"EVIDENCE_ONLY","candidate_types":["evidence_package"],"capability_profile":"capability-profile.json","consumers":["amphora-report-packager"],"dependencies":["amphora-candidate-contract","amphora-model-card-authority"],"evidence_inventory":"../../config/module-evidence-inventory.json","lane":"infrastructure","module_id":"amphora-redteam-audit","operational_readiness":"COMPLETE","phase":"PHASE_0","schema":"amphora.module-mission.v1","scientific_readiness":"NOT_APPLICABLE","solver_use_ceiling":"DISABLED"}
---

# amphora-redteam-audit mission

## Decision and falsifiable hypothesis

This module supports the decision of whether artifacts preserve contracts, claim locks, and prohibited-claim boundaries. Its falsifiable hypothesis is that a locked adversarial corpus detects malformed envelopes and authority escalation.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-assurance-capabilities/src/lib.rs` with SHA-256 `c0b2540fa84a9b8c98d2be5d82cbb1d21e9fd8b9806edad23815a0d912f4ab4d`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-assurance-capabilities/src/lib.rs` — SHA-256 `c0b2540fa84a9b8c98d2be5d82cbb1d21e9fd8b9806edad23815a0d912f4ab4d`
- `amphora-assurance-capabilities/src/diagnostics.rs` — SHA-256 `bab349d7039ab3d323c3313f3edc6680932278842d6e0512d9d929dbccaf987a`

Operational state is `COMPLETE`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `dataset` `amphora-redteam-audit/reference/mvp20/data/claim_registry.json` — SHA-256 `775330ec4d180802357c50b06de0d744544696b0e8f3d76e08d1d1f5a33e1b84`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-redteam-audit/reference/mvp20/out/redteam_self_audit.json` — SHA-256 `be8279ec78ca3980ba52b3b616390ac86601cca51809e300bfcd9d757de39c79`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-assurance-capabilities/tests/redteam_audit_phase0_kpi.rs` drives
the deterministic `deterministic_control_diagnostic` meta-audit runtime
across the nine supported upstream modules
(amphora-evidence-intake-validator, amphora-source-ledger,
amphora-redteam-audit, amphora-report-packager,
amphora-formulation-arithmetic, amphora-formulation-universe,
amphora-envelope-gates, amphora-cro-protocol-packager,
amphora-optimizer-orchestrator). Each per-module inner diagnostic embeds
its reference fixture bytes via `include_bytes!` at compile time; the
"fixture SHA-256" the receipt records is the SHA-256 of the runtime
source file `amphora-assurance-capabilities/src/diagnostics.rs`
(`4ec366110c523f30e285dd3cbca08fd199f28edb06560897cf7e17e7abe7dd89`).
The harness emits a byte-stable canonical receipt at
`evidence/phase0/benchmark/result.v1.json` (SHA-256
`701482a26cbe704e06bdade4c3af3279e6fee066319c5041822f37ed8dbf9f1f`). The
Phase-0 KPI receipt lives at
`evidence/phase0/kpis/redteam-audit-deterministic-control-diagnostic-kpi.v1.json`.

Observed Phase-0 KPI outcomes (all deterministic, `cargo test --workspace --locked`):

- `diagnostic_dispatch_ok_rate` observed **1.0** (9/9 supported module IDs return `Ok`) — **PASSED** (floor 1.0)
- `diagnostic_passed_flag_true_rate` observed **1.0** (9/9 returned `DeterministicControlDiagnosticV1.passed == true`) — **PASSED** (floor 1.0)
- `expected_equals_observed_fixture_outcomes_rate` observed **1.0** (9/9 embedded fixture outcomes match hardcoded expectations bit-exact) — **PASSED** (floor 1.0)
- `implementation_readiness_complete_rate` observed **1.0** (9/9 `implementation_readiness == "COMPLETE"` and schema bit-exact) — **PASSED** (floor 1.0)
- `zero_authority_lock_coverage_rate` observed **1.0** (9/9 populate every one of the 10 `REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS` to `true`) — **PASSED** (floor 1.0)
- `result_digest_byte_stable_across_replays_rate` observed **1.0** (9/9 `details["result_digest"]` byte-identical across replays) — **PASSED** (floor 1.0)
- `positive_or_negative_control_counts_present_rate` observed **1.0** (9/9 have non-trivial fixture corpora) — **PASSED** (floor 1.0)
- `unsupported_module_id_fail_closed_rate` observed **1.0** (6/6 probes - empty string, whitespace, unknown id, underscore-variant, uppercase-variant, unicode-variant - return Err) — **PASSED** (floor 1.0)
- `attack_axis_coverage_complete_rate` observed **1.0** (24/24 REDTEAM_ATTACK_AXES literally appear in `evidence/phase0/benchmark/benchmark-lock.v1.json`) — **PASSED** (floor 1.0)
- `authority_envelope_preservation_rate` observed **1.0** (15/15 serialized results and probe errors contain no `batch_release`/`qualified`/`authorized`/`manufacturing_qualification`/`release_authority` key) — **PASSED** (floor 1.0)
- `byte_stable_two_replay_rate` observed **1.0** (9/9 full DeterministicControlDiagnosticV1 payloads byte-identical across replays) — reported observationally.

DSSE-style signature envelope binding, Ed25519 signature verification,
SHA-256 hash-chained fixture integrity, and locked-adversarial-corpus
policy validation constitute the meta-audit theory stack (in-toto
Attestation v1.0 2020; Bernstein et al. CHES 2011 / RFC 8032 2017; NIST
FIPS 180-4 2015; Merkle 1988 CRYPTO 87; Anderson 1980 Reference-Monitor;
NIST SP 800-53 Rev. 5 AU-6 & CM-6; OWASP ASVS 4.0 V14). The runtime
reproduces the meta-audit boundary on 9 dispatched module diagnostics at
100% correctness and every one of the 24 module-specific attack axes
declared in `evidence/phase0/benchmark/benchmark-lock.v1.json` is
literally cross-checked against `REDTEAM_ATTACK_AXES` at test time.

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` (`RIGHTS` for the
runtime-embedded compilation, `LOCKED_SPLIT`, `LOCKED_BENCHMARK`,
`TWO_REPLAYS`, `RED_TEAM` across 47 attack axes, `CLAIM_LOCKS`,
`FOLDER_CONFINEMENT`, `BENCHMARK_EXECUTION_COMPLETE`,
`MODULE_INVARIANTS`) are passing. Awaiting `PHASE0_EVALUATOR` and
`PHASE0_INTERNAL_REVIEWER` signatures per the `evaluation.v1.dsse.json`
and `phase0-review-receipt.v1.json` protocol before the front-matter's
`phase: PHASE_0` and `operational_readiness: COMPLETE` become
substantively - rather than aspirationally - promotable. This push
lands the deterministic KPI receipt that makes the target substantive
at the moment of signing.

### Known contradictions

- A successful self-audit only confirms encoded checks; it is not independent red-team coverage or evidence that all attacks were anticipated.
- The 24 module-specific attack axes declared in `REDTEAM_ATTACK_AXES` and cross-checked at benchmark-lock time are the axes the runtime detects; independent adversarial-corpus mutation remains a Phase-1 external dependency.
- The `RED_TEAM` gate above is asserted as passing across all 47 attack axes without qualification. A live-runtime oracle (`evidence/phase0/independent/governance-axis-live-corpus-v1.dsse.json`, first run 2026-07-31, reproduced byte-identically 2026-08-19 in `evidence/audit/governance-axis-live-corpus-replay-20260819-v1/`) shows 4 of the outer 24 portfolio-governance axes (`FAILING_DETERMINISTIC_DIAGNOSTIC`, `FALSE_MOVEMENT_CLAIM`, `STALE_PARENT`, `STRIPPED_MISSION_LOCKS`) are not mediated by the live `amphora-phase0-reviewer` binary against a real adversary. In particular its re-executed benchmark diagnostic resolves the reviewed workspace from a compile-time constant (`amphora-cli/src/main.rs fn workspace_root()`), not the `--workspace` path under review, so a tampered `benchmark-lock.v1.json` inside the reviewed tree is not detected. AUDIT_ONLY; no promotion effect; unrepaired as of this writing.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `evidence_package` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `gates.score_envelopes_valid`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-redteam-audit-example", "candidate_type": "evidence_package", "evidence_refs": {"evidence_package": {}}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `gates.score_envelopes_valid`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `EVIDENCE_ONLY` and solver-use ceiling is `DISABLED`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **red-team rejection rate** at `gates.score_envelopes_valid`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0; locked module-specific benchmark required for Phase 1.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `rtk cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Independent adversarial review and mutation corpus

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-assurance-capabilities/src/lib.rs` via `rtk cargo test --workspace --locked`. Scenario: Reject empty or malformed artifact lists and invalid input envelopes.
