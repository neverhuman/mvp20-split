---
{"audit_date":"2026-07-17","authority_ceiling":"EVIDENCE_ONLY","candidate_types":["evidence_package"],"capability_profile":"capability-profile.json","consumers":["amphora-model-card-authority"],"dependencies":["amphora-candidate-contract"],"evidence_inventory":"../../config/module-evidence-inventory.json","lane":"infrastructure","module_id":"amphora-run-provenance","operational_readiness":"COMPLETE","phase":"PHASE_0","schema":"amphora.module-mission.v1","scientific_readiness":"NOT_APPLICABLE","solver_use_ceiling":"DISABLED"}
---

# amphora-run-provenance mission

## Decision and falsifiable hypothesis

This module supports the decision of whether a complete validated run can be replayed from hash-bound inputs. Its falsifiable hypothesis is that fixed-seed replay is byte-identical outside declared wall-clock telemetry.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-engine/src/lib.rs` with SHA-256 `6b007d7d9d0acd453aac5e7c300ab16fb9a7253337c722cc4cffe0be23db62b4`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-engine/src/lib.rs` — SHA-256 `6b007d7d9d0acd453aac5e7c300ab16fb9a7253337c722cc4cffe0be23db62b4`

Operational state is `COMPLETE`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `output_artifact` `amphora-run-provenance/reference/mvp20/out/run_manifest.json` — SHA-256 `eb68f96019b42e0617a08243d391c1aaf1104de62e1f797ca266b9533cd3e8c6`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-core/tests/run_provenance_phase0_kpi.rs` builds real run
archives under tempdir via RunArchive::create + append + snapshot +
final_state, then invokes verify_run. 3 positive scenarios (empty, 3
events, 12 events across 3 generations) + 10 tamper probes each
mutating exactly one integrity condition (manifest bytes, events.jsonl
bytes, final-state.json, provenance.json root_hash, provenance
events_sha256, sequence gap, mutated event payload, missing provenance,
missing manifest, duplicate archive create). Byte-stable receipt at
`evidence/phase0/benchmark/result.v1.json` (SHA-256
`e1027610672259a2f40437c1819fd69197f13b6ad6cab14e4879b856d6a5ffb3`).
Phase-0 KPI receipt at
`evidence/phase0/kpis/run-provenance-hash-chain-integrity-kpi.v1.json`.

All 6 deterministic gates at floor 1.0. Runtime returns bit-exact
root_hash matching independent harness recomputation of stable_hash({
run_id, manifest_sha256, events_sha256, event_chain_root,
final_state_hash}). All 10 tamper probes fail closed with expected
RunArchiveError variant. signature_status pinned to
UNSIGNED_CONTROLLED_KEY_REQUIRED; promotion_receipt_eligible pinned
false.

Theory: Haber-Stornetta 1991 J. Cryptology 3(2):99-111 hash-chain
time-stamping; Merkle 1980 IEEE S&P; RFC 6962 Certificate Transparency;
Torvalds-Hamano git 2005; in-toto Attestation v1.0 (2020); SLSA v1.0
(2023); NIST FIPS 180-4; NIST SP 800-92 log integrity; ISO/IEC 27001:
2022 A.12.4 & A.8.15; Anderson 1980 reference-monitor; Salzer-Schroeder
1975 complete-mediation.

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` passing. Awaiting
`PHASE0_EVALUATOR` and `PHASE0_INTERNAL_REVIEWER` signatures.
Front-matter preserved.

### Known contradictions

- A deterministic provenance record binds observed bytes but does not independently prove the scientific truth or ownership of those bytes.
- **CLAIM_REFUTED (2026-08-06, first adversarial test, campaign T-13/T2-13):** the "hash chain integrity" and "interior Haber-Stornetta linkage enforced" claims above overstate what `verify_run` actually checks. Read from `amphora-core/src/lib.rs`: `verify_run` never independently recomputes an individual event's `event_hash` from `stable_hash({schema,sequence,run_id,event_type,candidate_id,generation,payload,previous_event_hash})`; it only checks positional sequence contiguity, whole-file SHA-256 of `manifest.json`/`events.jsonl` against the values recorded in `provenance.json`, and the last event's stored `event_hash` against `provenance.event_chain_root`. Running the real `verify_run` against copies of 28 real in-tree run archives under `.amphora/runs/` (not the shipped n=3 synthetic fixture), 122/126 forged-or-replayed tamper cases (truncated chain, reordered links, substituted intermediate hash, verbatim replay, spliced-input divergence — each reconciled by recomputing `provenance.json` with the real hash formula) returned `Ok(root_hash)`: a tampered, reordered, truncated, substituted, or replayed/foreign history verified as intact. Naive (non-reforged) tampering is still caught via the coarse whole-file hash check. Separately, and with zero tampering: 4 of the 5 real archives carrying a genuine runtime-written `provenance.json` (2026-07-17) fail `verify_run` today on `final_state_hash` alone — `stable_hash`'s canonicalization of `final-state.json` has drifted since those archives were written, so untampered historical archives silently stop verifying. Signed receipt: `evidence/audit/real-archive-tamper-scale-v1/real-archive-tamper-scale-receipt.v1.dsse.json`. Prior related finding (hand-built fixture, not real archives): `evidence/audit/live-runtime-archive-parity-v1/live-runtime-archive-parity-receipt.v1.dsse.json` H0b.

- **CLAIM_REFUTED (2026-08-13, campaign W-T-PROV, theory-dimension):** the "hash-chain integrity 1.0 at n=3" KPI above is self-referential — it measures `verify_run` against its own fixture, not against a named published provenance standard. Measured explicitly against in-toto Attestation Framework v1 (https://github.com/in-toto/attestation/tree/main/spec/v1, https://in-toto.io/docs/attestation-spec/) and SLSA v1.0 (https://slsa.dev/spec/v1.0/, OpenSSF, released 2023-04-19): `provenance.json` is not an in-toto Statement (no `_type`, `subject`, or `predicateType` fields) and is never wrapped in a DSSE Envelope — `RunArchive::final_state` writes it as plain JSON with `signature_status` hard-set to the literal string `UNSIGNED_CONTROLLED_KEY_REQUIRED`; no code path calls `sign_dsse` on it. Against SLSA v1.0 Build-track requirements the module satisfies only part of L1 (consistent build process + digest-bound provenance generation) but not L1's provenance-distribution requirement (provenance never leaves the local `.amphora/runs/<run_id>/` directory) and not any part of L2 ("Provenance is Authenticated" — no digital signature exists over the run-provenance record at all). L3 is not reachable while L2 is unmet. Full 14-row requirement-by-requirement conformance table with citations and evidence: `evidence/phase0/repairs/W-T-PROV/done/w-t-prov-done-receipt.v1.dsse.json`.

- **CLAIM_REFUTED (2026-08-15, ROTATION fire, study fixed-seed-replay-determinism-v1):** the falsifiable hypothesis stated at the top of this document — "fixed-seed replay is byte-identical outside declared wall-clock telemetry" — was tested directly for the first time (all prior fires attacked `verify_run`'s tamper-detection semantics or standards conformance against a single archive, never cross-run replay determinism). Built the real production binary (`amphora-cli`, bin `amphora-tui`) and invoked `run` twice with byte-identical `--candidate --seed --population --generations --workers --lane` arguments. All five provenance hash anchors differed between the two runs: `manifest_sha256`, `events_sha256`, `event_chain_root`, `final_state_hash`, and `root_hash`. Root cause read from `amphora-cli/src/main.rs`: the module already computes a deterministic, seed-derived run identity (`deterministic_run_id` → `scoring_run_id`) but the production `run` subcommand discards it for archive identity, using `format!("run-{}", now_ms())` instead — only `demo` mode reuses the deterministic id. Because `run_id` is embedded in `manifest.json` and every event line, this one wall-clock value cascades into every hash the module computes, including `root_hash`. A targeted search of the module and its shared runtime for any allowlist, schema field, or code constant declaring which fields count as exempt "wall-clock telemetry" found none — the phrase appears nowhere except the hypothesis sentence itself, so the exemption clause is not mechanically checkable by any shipped tool (`replay --verify` only self-checks one archive; there is no cross-run compare command). Bounded finding: after manually stripping `run_id` and named timing fields (`at_ms`, `started_at_ms`, `average_latency_ms`, `duration_ms`, `wall_clock_ms`), all 22 real events across the two runs — proposals, mutations, scores, rankings, `result_hash` — were byte-identical, so the seeded RNG and scoring path genuinely are deterministic; what fails is the module's own hash-anchor apparatus's ability to witness that fact.

- **CLAIM_REFUTED (2026-08-17, ROTATION fire, study run-id-collision-silent-substitution-v1):** the third headline claim in this document's KPI register -- "Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0" -- was tested directly for the first time and also does not hold. Using the real production `amphora-tui` binary (unmodified; identity confirmed by `amphora-cli/src/main.rs` sha256 match to the 2026-08-15 fire) plus an external LD_PRELOAD clock-interposition shim (no amphora source touched), two DIFFERENT, legitimate, concurrently-issued requests -- candidate A (DGEBA-monomer, seed 111) and candidate B (a genuinely different molecule, TETA-hardener-B, seed 222) -- were forced to collide on the wall-clock-derived production `run_id` (root cause: same `format!("run-{}", now_ms())` identified 2026-08-15). Request B returned exit 0, `{"immutable_existing_run": true, "root_hash": ...}`, with the reported root_hash matching request A's archive exactly, and zero trace of candidate B or seed 222 anywhere in the archive it was silently pointed to: request B's actual inputs were never scored or archived at all. A control run with non-colliding run_ids behaved correctly (two distinct archives, both genuinely executed), isolating the defect to the collision path. Root cause, shared with the 2026-08-15 finding: `amphora-cli/src/main.rs` lines 557-570 treat `.amphora/runs/<run_id>` path existence as sufficient proof the current request was already honored, but `run_id` (production, non-demo) carries no content binding. Proposed repair: use the already-computed content-derived `scoring_run_id` (line 489) as the archive key for the `run` subcommand, exactly as `demo` mode already does at line 499 -- this repairs both this finding and the 2026-08-15 one from the same change. Signed receipt: `evidence/audit/run-id-collision-silent-substitution-v1/run-id-collision-silent-substitution-receipt.v1.dsse.json`.

- **CLAIM_REFUTED (2026-08-19, ROTATION fire, study concurrent-create-toctou-v1):** the Phase-0 KPI metric `duplicate_archive_create_rejected_via_exists_rate` (observed 1.0, n=3) and its `fitted_or_physical_model_artifact.prediction_rule` step (1), "verify base/run_id does not already exist (else Exists)", were tested for the first time under genuine concurrency rather than the shipped fixture's sequential single-threaded duplicate-create probe. A standalone Rust harness spawned 8 barrier-synchronized OS threads calling the real `amphora_core::RunArchive::create` against a SHARED `run_id` simultaneously, over 40 trials, executed twice independently (two separate live process runs). Across both executions (320 losing race attempts total), 279/320 and 280/320 losing threads respectively returned `RunArchiveError::Io`, versus only 1 and 0 returning the documented `RunArchiveError::Exists` — a 99.6%-100% Io-dominant failure mode. Root cause read from `amphora-core/src/lib.rs`: `path.exists()` (the Exists guard) is checked non-atomically before `fs::create_dir_all` (which tolerates the race, since Rust's std `create_dir_all` succeeds if the directory already exists) and a `create_new(true)` open of `manifest.json` (the actual OS-level atomic guard, O_CREAT|O_EXCL); the loser's failed open is mapped to `Io`, not `Exists`. A matched distinct-run_id control (640 concurrent creates across both executions) produced zero errors of any kind, isolating the defect to the shared-run_id race. This is a fifth, independent root-cause family from the same `amphora-cli/src/main.rs` archive-identity surface as the 2026-08-15 and 2026-08-17 findings, but requires only ordinary concurrent contention on any already-known `run_id` (no wall-clock value collision needed) and manifests even when `RunArchive::create`'s own exists-check fires exactly as intended. No archive content corruption was observed (every trial had exactly one winner). Signed receipt: `evidence/audit/concurrent-create-toctou-v1/concurrent-create-toctou-receipt.v1.dsse.json`.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `evidence_package` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `metrics.whole_run_output_hash_sha256`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-run-provenance-example", "candidate_type": "evidence_package", "evidence_refs": {"evidence_package": {}}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `metrics.whole_run_output_hash_sha256`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `EVIDENCE_ONLY` and solver-use ceiling is `DISABLED`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **replay hash equality** at `metrics.whole_run_output_hash_sha256`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0; locked module-specific benchmark required for Phase 1.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `rtk cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Signed execution environment, immutable artifact store, and independent replay

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-engine/src/lib.rs` via `rtk cargo test --workspace --locked`. Scenario: Reject empty or malformed artifacts and detect replay-byte drift.
